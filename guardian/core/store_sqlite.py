"""SqliteStore: archivio locale (sviluppo e test), allineato alle migrazioni Supabase 001 + 002.

I vincoli (task duplicati, un solo task running per agente, dipendenze) sono indici SQLite o controlli Python
che replicano gli indici e i trigger Postgres. Le funzioni bridge_* replicano le RPC SQL del Guardian Bridge.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path

from .models import (ACTION_TYPES, AGENT_STATI, AGENT_TIPI, APPROVAL_STATI, DEVICE_STATI, TASK_APERTI, TASK_STATI_V1,
                     TASK_TERMINALI, Handoff, ValidazioneError, adesso, pulisci, pulisci_file, scegli)
from .store import (JSON_FIELDS, LIST_FIELDS, MSG_DIPENDENZE, _valida_task, hash_token, messaggio_db, nuovo_token,
                    testo_ripresa, valida_memoria,
                    severita)

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, nome TEXT NOT NULL, email TEXT UNIQUE, ruolo TEXT,
  agente TEXT, stato TEXT NOT NULL DEFAULT 'attivo');
CREATE TABLE IF NOT EXISTS devices (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL REFERENCES users(id),
  nome TEXT NOT NULL, agent_name TEXT, model TEXT, stato TEXT NOT NULL DEFAULT 'offline', current_task_id INTEGER,
  error TEXT, limit_reached INTEGER NOT NULL DEFAULT 0, last_seen TEXT, last_checkpoint TEXT,
  token_hash TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, titolo TEXT NOT NULL, descrizione TEXT,
  responsabile TEXT REFERENCES users(id), agente TEXT, priorita TEXT NOT NULL DEFAULT 'media',
  stato TEXT NOT NULL DEFAULT 'backlog', next_step TEXT, files_changed TEXT NOT NULL DEFAULT '[]',
  created_by TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS activity_events (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER REFERENCES tasks(id),
  device_id INTEGER REFERENCES devices(id), user_id TEXT, agent_name TEXT, event_type TEXT NOT NULL,
  message TEXT NOT NULL, files TEXT NOT NULL DEFAULT '[]', external_key TEXT UNIQUE, timestamp TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS handoffs (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER REFERENCES tasks(id),
  device_id INTEGER REFERENCES devices(id), agent_name TEXT NOT NULL, summary TEXT NOT NULL, completed_steps TEXT,
  files_changed TEXT NOT NULL DEFAULT '[]', decisions TEXT, errors TEXT, tests TEXT, next_step TEXT NOT NULL,
  timestamp TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER REFERENCES tasks(id),
  action TEXT NOT NULL, description TEXT, status TEXT NOT NULL DEFAULT 'richiesta', requested_by TEXT,
  decided_by TEXT, created_at TEXT NOT NULL, decided_at TEXT);
"""

# Colonne aggiunte dalla migrazione 002 alle tabelle v1 (applicate solo se mancano).
COLONNE_V2 = {
    "users": {"accesso": "TEXT NOT NULL DEFAULT 'member'"},
    "tasks": {"project_id": "INTEGER REFERENCES projects(id)", "plan_id": "INTEGER REFERENCES plans(id)",
              "assigned_agent_id": "TEXT REFERENCES agents(id)", "depends_on": "TEXT NOT NULL DEFAULT '[]'",
              "result": "TEXT", "error": "TEXT", "expected_result": "TEXT", "completion_criteria": "TEXT"},
    "activity_events": {"severity": "TEXT NOT NULL DEFAULT 'info'", "agent_id": "TEXT", "project_id": "INTEGER"},
    "handoffs": {"from_agent_id": "TEXT", "to_agent_id": "TEXT", "tests_pending": "TEXT", "dependencies": "TEXT",
                 "important_notes": "TEXT", "stato": "TEXT NOT NULL DEFAULT 'aperto'"},
    "approvals": {"agent_id": "TEXT", "action_type": "TEXT NOT NULL DEFAULT 'altro'", "reason": "TEXT",
                  "impact": "TEXT", "data_involved": "TEXT"},
}

SCHEMA_V2 = """
CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE COLLATE NOCASE,
  descrizione TEXT, stato TEXT NOT NULL DEFAULT 'attivo', created_by TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
  device_id INTEGER REFERENCES devices(id), nome TEXT NOT NULL, tipo TEXT NOT NULL, capabilities TEXT NOT NULL DEFAULT '[]',
  stato TEXT NOT NULL DEFAULT 'unknown', current_task_id INTEGER, last_heartbeat TEXT, last_activity TEXT, error TEXT,
  disponibile INTEGER NOT NULL DEFAULT 1, usage TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS plans (id INTEGER PRIMARY KEY AUTOINCREMENT, goal TEXT NOT NULL, project_id INTEGER,
  provider TEXT, model TEXT, piano TEXT NOT NULL, stato TEXT NOT NULL DEFAULT 'bozza', created_by TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS agent_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT, device_id INTEGER,
  project_id INTEGER, task_id INTEGER, level TEXT NOT NULL DEFAULT 'info', source TEXT NOT NULL, message TEXT NOT NULL,
  ts TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL REFERENCES users(id),
  kind TEXT NOT NULL, message TEXT NOT NULL, ref_table TEXT, ref_id TEXT, read_at TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS memory (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER REFERENCES projects(id),
  task_id INTEGER REFERENCES tasks(id), kind TEXT NOT NULL, content TEXT NOT NULL, source TEXT NOT NULL,
  created_by TEXT, created_at TEXT NOT NULL, superseded_by INTEGER REFERENCES memory(id));
CREATE INDEX IF NOT EXISTS idx_events_ts ON activity_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_stato ON tasks(stato);
CREATE INDEX IF NOT EXISTS idx_logs_ts ON agent_logs(ts DESC);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, read_at);
CREATE UNIQUE INDEX IF NOT EXISTS tasks_titolo_aperto ON tasks(COALESCE(project_id, 0), lower(titolo))
  WHERE stato NOT IN ('completed', 'failed', 'cancelled');
CREATE UNIQUE INDEX IF NOT EXISTS tasks_un_running ON tasks(assigned_agent_id)
  WHERE stato = 'running' AND assigned_agent_id IS NOT NULL;
"""

ORDINE_PRIORITA = "CASE priorita WHEN 'urgente' THEN 0 WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END"


class SqliteStore:
    """Archivio locale. Thread-safe per l'uso da Streamlit (una connessione, un lock)."""

    modalita = "locale"

    def __init__(self, path: str | os.PathLike = ":memory:"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._lock = threading.RLock()
        with self._lock:
            self._migra()

    def _migra(self) -> None:
        """v1 -> v2, idempotente: nuove tabelle, colonne mancanti, conversione degli stati dei task."""
        self._db.executescript(SCHEMA_V1)
        self._db.executescript(SCHEMA_V2.split("CREATE INDEX")[0])  # prima le tabelle (servono alle FK delle colonne)
        for tabella, colonne in COLONNE_V2.items():
            esistenti = {r["name"] for r in self._db.execute(f"PRAGMA table_info({tabella})")}
            for col, decl in colonne.items():
                if col not in esistenti:
                    self._db.execute(f"ALTER TABLE {tabella} ADD COLUMN {col} {decl}")
        for vecchio, nuovo in TASK_STATI_V1.items():
            self._db.execute("UPDATE tasks SET stato=? WHERE stato=?", (nuovo, vecchio))
        terminali = ",".join(f"'{s}'" for s in TASK_TERMINALI)
        self._db.execute(  # titoli aperti duplicati (ammessi in v1): resi unici prima dell'indice
            f"UPDATE tasks SET titolo = titolo || ' (#' || id || ')' WHERE stato NOT IN ({terminali}) AND id NOT IN "
            f"(SELECT MIN(id) FROM tasks WHERE stato NOT IN ({terminali}) GROUP BY COALESCE(project_id, 0), lower(titolo))")
        self._db.executescript(SCHEMA_V2)
        self._db.commit()

    # --- utilità -------------------------------------------------------------
    def _q(self, sql: str, args=()) -> list[dict]:
        with self._lock:
            rows = self._db.execute(sql, args).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            for k in LIST_FIELDS:
                if k in d and isinstance(d[k], str):
                    d[k] = json.loads(d[k] or "[]")
            for k in JSON_FIELDS:
                if k in d and isinstance(d[k], str):
                    d[k] = json.loads(d[k])
            for k in ("limit_reached", "disponibile"):
                if k in d:
                    d[k] = bool(d[k])
            d.pop("token_hash", None)
            out.append(d)
        return out

    def _x(self, sql: str, args=()) -> int:
        with self._lock:
            try:
                cur = self._db.execute(sql, args)
            except sqlite3.IntegrityError as e:
                self._db.rollback()
                msg = messaggio_db(e)
                if msg:
                    raise ValidazioneError(msg) from None
                raise
            self._db.commit()
            return cur.lastrowid

    def _insert(self, tabella: str, campi: dict) -> int:
        campi = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in campi.items()}
        cols = ", ".join(campi)
        return self._x(f"INSERT INTO {tabella} ({cols}) VALUES ({', '.join('?' * len(campi))})",
                       tuple(campi.values()))

    def ping(self) -> bool:
        return bool(self._q("SELECT 1 AS ok"))

    # --- utenti, notifiche ----------------------------------------------------
    def users(self) -> list[dict]:
        return self._q("SELECT * FROM users ORDER BY id")

    def upsert_user(self, id: str, nome: str, email: str | None = None, ruolo: str = "", agente: str = "",
                    stato: str = "attivo", accesso: str = "member") -> None:
        self._x("INSERT INTO users (id, nome, email, ruolo, agente, stato, accesso) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET nome=excluded.nome, email=COALESCE(excluded.email, users.email), "
                "ruolo=excluded.ruolo, agente=excluded.agente, stato=excluded.stato, accesso=excluded.accesso",
                (id, nome, (email or None) and email.lower(), ruolo, agente, stato,
                 scegli(accesso, ("admin", "member"), "Accesso")))

    def _notifica(self, kind: str, message: str, user_ids=None, ref_table=None, ref_id=None) -> None:
        """user_ids=None: a tutti i collaboratori attivi."""
        if user_ids is None:
            user_ids = [u["id"] for u in self._q("SELECT id FROM users WHERE stato='attivo'")]
        for uid in {u for u in user_ids if u}:
            self._insert("notifications", {"user_id": uid, "kind": kind, "message": message[:500],
                                           "ref_table": ref_table, "ref_id": str(ref_id) if ref_id else None,
                                           "created_at": adesso()})

    def notifications(self, user_id: str, solo_non_lette: bool = False, limit: int = 50) -> list[dict]:
        extra = " AND read_at IS NULL" if solo_non_lette else ""
        return self._q(f"SELECT * FROM notifications WHERE user_id=?{extra} ORDER BY created_at DESC, id DESC LIMIT ?",
                       (user_id, limit))

    def mark_read(self, user_id: str, notification_id: int | None = None) -> None:
        if notification_id:
            self._x("UPDATE notifications SET read_at=? WHERE id=? AND user_id=?", (adesso(), notification_id, user_id))
        else:
            self._x("UPDATE notifications SET read_at=? WHERE user_id=? AND read_at IS NULL", (adesso(), user_id))

    # --- progetti ------------------------------------------------------------
    def projects(self, solo_attivi: bool = False) -> list[dict]:
        return self._q("SELECT * FROM projects" + (" WHERE stato='attivo'" if solo_attivi else "") + " ORDER BY nome")

    def create_project(self, nome: str, descrizione: str = "", created_by: str | None = None) -> dict:
        ora = adesso()
        try:
            pid = self._insert("projects", {"nome": pulisci(nome, 120, True, "nome progetto"),
                                            "descrizione": pulisci(descrizione, 2000) or None,
                                            "created_by": created_by, "created_at": ora, "updated_at": ora})
        except sqlite3.IntegrityError:
            raise ValidazioneError("Esiste già un progetto con questo nome.") from None
        self.add_event("project_created", f"Creato progetto: {nome}", user_id=created_by, project_id=pid)
        return self._q("SELECT * FROM projects WHERE id=?", (pid,))[0]

    def update_project(self, project_id: int, stato: str) -> None:
        self._x("UPDATE projects SET stato=?, updated_at=? WHERE id=?",
                (scegli(stato, ("attivo", "archiviato"), "Stato progetto"), adesso(), project_id))

    # --- dispositivi e agenti -------------------------------------------------
    def devices(self) -> list[dict]:
        return self._q("SELECT * FROM devices ORDER BY user_id, nome")

    def register_device(self, user_id: str, nome: str, agent_name: str = "") -> tuple[dict, str]:
        token = nuovo_token()
        did = self._insert("devices", {"user_id": user_id, "nome": pulisci(nome, 80, True, "nome dispositivo"),
                                       "agent_name": pulisci(agent_name, 80) or None,
                                       "token_hash": hash_token(token), "created_at": adesso()})
        return self._q("SELECT * FROM devices WHERE id=?", (did,))[0], token

    def revoke_device(self, device_id: int) -> None:
        self._x("UPDATE devices SET token_hash=?, stato='offline' WHERE id=?",
                (hash_token(nuovo_token()), device_id))

    def agents(self) -> list[dict]:
        return self._q("SELECT * FROM agents ORDER BY user_id, id")

    def agent(self, agent_id: str) -> dict | None:
        r = self._q("SELECT * FROM agents WHERE id=?", (agent_id,))
        return r[0] if r else None

    def upsert_agent(self, id: str, user_id: str, nome: str, tipo: str, device_id: int | None = None,
                     capabilities=(), disponibile: bool = True) -> dict:
        """Registra o aggiorna un agente (anagrafica). Lo stato NON si imposta qui: arriva da eventi reali."""
        agent_id = pulisci(id, 60, True, "id agente").lower()
        caps = sorted({pulisci(c, 40) for c in (capabilities or []) if c and c.strip()})
        self._x("INSERT INTO agents (id, user_id, device_id, nome, tipo, capabilities, disponibile, created_at) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET user_id=excluded.user_id, "
                "device_id=excluded.device_id, nome=excluded.nome, tipo=excluded.tipo, capabilities=excluded.capabilities, "
                "disponibile=excluded.disponibile",
                (agent_id, user_id, device_id, pulisci(nome, 80, True, "nome agente"), scegli(tipo, AGENT_TIPI, "Tipo agente"),
                 json.dumps(caps), int(bool(disponibile)), adesso()))
        return self.agent(agent_id)

    def set_agent_state(self, agent_id: str, stato: str, current_task_id=None, error=None, by: str | None = None,
                        manuale: bool = True) -> dict:
        """Cambio di stato di un agente. Dall'UI è 'manuale' e l'evento lo dichiara."""
        a = self.agent(agent_id)
        if not a:
            raise ValidazioneError("Agente inesistente.")
        stato = scegli(stato, AGENT_STATI, "Stato agente")
        err = pulisci(error, 500, nome="errore") or None
        self._x("UPDATE agents SET stato=?, current_task_id=?, error=?, last_activity=? WHERE id=?",
                (stato, current_task_id, err, adesso(), agent_id))
        if a["stato"] != stato or err:
            self.add_event("agent_state", f"{a['nome']}: {stato}{' (manuale)' if manuale else ''}"
                           + (f" — {err}" if err else ""), user_id=by or a["user_id"], agent_id=agent_id,
                           agent_name=a["nome"], task_id=current_task_id,
                           severity="error" if stato == "error" else "info")
            if stato == "error":
                self._notifica("agent_error", f"Agente {a['nome']} in errore: {err or 'senza dettagli'}",
                               [a["user_id"]], "agents", agent_id)
        return self.agent(agent_id)

    # --- task ----------------------------------------------------------------
    def tasks(self, stato: str | None = None, project_id: int | None = None) -> list[dict]:
        where, args = [], []
        if stato:
            where.append("stato=?")
            args.append(stato)
        if project_id:
            where.append("project_id=?")
            args.append(project_id)
        w = (" WHERE " + " AND ".join(where)) if where else ""
        return self._q(f"SELECT * FROM tasks{w} ORDER BY {ORDINE_PRIORITA}, updated_at DESC", args)

    def task(self, task_id: int) -> dict | None:
        r = self._q("SELECT * FROM tasks WHERE id=?", (task_id,))
        return r[0] if r else None

    def _controlla_dipendenze(self, task_id: int | None, stato: str, depends_on: list[int]) -> None:
        """Specchio del trigger Postgres tasks_controlla_dipendenze."""
        if task_id and task_id in depends_on:
            raise ValidazioneError("Un task non può dipendere da sé stesso.")
        if not depends_on:
            return
        trovati = {t["id"]: t["stato"] for t in self._q(
            f"SELECT id, stato FROM tasks WHERE id IN ({','.join('?' * len(depends_on))})", depends_on)}
        mancanti = set(depends_on) - set(trovati)
        if mancanti:
            raise ValidazioneError(f"Dipendenze inesistenti: {sorted(mancanti)}")
        if stato in ("ready", "running") and any(s != "completed" for s in trovati.values()):
            raise ValidazioneError(MSG_DIPENDENZE)

    def create_task(self, titolo, descrizione="", responsabile=None, agente="", priorita="media", next_step="",
                    created_by=None, stato="backlog", project_id=None, depends_on=(), assigned_agent_id=None,
                    expected_result=None, completion_criteria=None, plan_id=None) -> dict:
        campi = _valida_task({"titolo": titolo, "descrizione": descrizione, "responsabile": responsabile,
                              "agente": agente, "priorita": priorita, "next_step": next_step, "stato": stato,
                              "project_id": project_id, "depends_on": list(depends_on or []),
                              "assigned_agent_id": assigned_agent_id, "expected_result": expected_result,
                              "completion_criteria": completion_criteria, "plan_id": plan_id})
        self._controlla_dipendenze(None, campi["stato"], campi["depends_on"])
        ora = adesso()
        tid = self._insert("tasks", {**campi, "files_changed": [], "created_by": created_by,
                                     "created_at": ora, "updated_at": ora})
        self.add_event("task_created", f"Creato task: {campi['titolo']}", user_id=created_by, task_id=tid,
                       project_id=campi["project_id"])
        if campi["assigned_agent_id"]:
            self.add_event("task_assigned", f"Task #{tid} assegnato a {campi['assigned_agent_id']}", user_id=created_by,
                           task_id=tid, agent_id=campi["assigned_agent_id"], project_id=campi["project_id"])
        return self.task(tid)

    def update_task(self, task_id: int, by: str | None = None, agent_name: str | None = None,
                    device_id: int | None = None, agent_id: str | None = None, **campi) -> dict:
        campi = _valida_task(campi)
        prima = self.task(task_id)
        if not campi or not prima:
            raise ValidazioneError("Task inesistente o nessuna modifica.")
        stato = campi.get("stato", prima["stato"])
        self._controlla_dipendenze(task_id, stato, campi.get("depends_on", prima["depends_on"]))
        campi["updated_at"] = adesso()
        sets = ", ".join(f"{k}=?" for k in campi)
        vals = [json.dumps(v) if isinstance(v, list) else v for v in campi.values()]
        self._x(f"UPDATE tasks SET {sets} WHERE id=?", (*vals, task_id))
        self._eventi_task(prima, self.task(task_id), by, agent_name, device_id, agent_id)
        return self.task(task_id)

    def _eventi_task(self, prima: dict, dopo: dict, by, agent_name, device_id, agent_id) -> None:
        tid, pid = dopo["id"], dopo.get("project_id")
        comune = dict(user_id=by, agent_name=agent_name, task_id=tid, device_id=device_id, project_id=pid,
                      agent_id=agent_id or dopo.get("assigned_agent_id"))
        if dopo.get("assigned_agent_id") != prima.get("assigned_agent_id") and dopo.get("assigned_agent_id"):
            self.add_event("task_assigned", f"Task #{tid} assegnato a {dopo['assigned_agent_id']}", **comune)
        if dopo["stato"] != prima["stato"]:
            tipo = {"running": "task_started", "completed": "task_completed", "failed": "task_failed"}.get(
                dopo["stato"], "task_updated")
            self.add_event(tipo, f"Task #{tid} {prima['stato']} → {dopo['stato']}",
                           severity="error" if dopo["stato"] == "failed" else "info",
                           files=dopo.get("files_changed") or [], **comune)
            if dopo["stato"] == "failed":
                self._notifica("task_failed", f"Task #{tid} fallito: {dopo['titolo']}",
                               [dopo.get("responsabile")] if dopo.get("responsabile") else None, "tasks", tid)
        elif any(dopo.get(k) != prima.get(k) for k in ("priorita", "responsabile", "next_step", "files_changed",
                                                      "result", "error", "depends_on")):
            self.add_event("task_updated", f"Task #{tid} aggiornato", files=dopo.get("files_changed") or [], **comune)

    # --- eventi e log --------------------------------------------------------
    def events(self, limit: int = 100, task_id: int | None = None) -> list[dict]:
        if task_id:
            return self._q("SELECT * FROM activity_events WHERE task_id=? ORDER BY timestamp DESC, id DESC LIMIT ?",
                           (task_id, limit))
        return self._q("SELECT * FROM activity_events ORDER BY timestamp DESC, id DESC LIMIT ?", (limit,))

    def add_event(self, event_type, message, user_id=None, agent_name=None, task_id=None, device_id=None,
                  files=None, external_key=None, timestamp=None, severity="info", agent_id=None,
                  project_id=None) -> bool:
        try:
            self._insert("activity_events", {
                "event_type": pulisci(event_type, 40, True, "tipo evento"), "message": pulisci(message, 1000, True, "messaggio"),
                "user_id": user_id, "agent_name": agent_name, "task_id": task_id, "device_id": device_id,
                "files": pulisci_file(files), "external_key": external_key, "timestamp": timestamp or adesso(),
                "severity": severita(severity), "agent_id": agent_id, "project_id": project_id})
            return True
        except sqlite3.IntegrityError as e:
            if "external_key" in str(e):
                return False  # già importato
            raise

    # --- handoff -------------------------------------------------------------
    def handoffs(self, task_id: int | None = None, limit: int = 50) -> list[dict]:
        if task_id:
            return self._q("SELECT * FROM handoffs WHERE task_id=? ORDER BY timestamp DESC, id DESC LIMIT ?",
                           (task_id, limit))
        return self._q("SELECT * FROM handoffs ORDER BY timestamp DESC, id DESC LIMIT ?", (limit,))

    def add_handoff(self, h: Handoff, device_id: int | None = None, user_id: str | None = None) -> int:
        h.valida()
        t = self.task(h.task_id) if h.task_id else None
        if h.task_id and not t:
            raise ValidazioneError(f"Task #{h.task_id} inesistente.")
        dest = self.agent(h.to_agent_id) if h.to_agent_id else None
        if h.to_agent_id and not dest:
            raise ValidazioneError(f"Agente destinatario inesistente: {h.to_agent_id}")
        hid = self._insert("handoffs", {"task_id": h.task_id, "device_id": device_id, "agent_name": h.agent_name,
                                        "summary": h.summary, "files_changed": h.files_changed, "next_step": h.next_step,
                                        "timestamp": h.timestamp, "from_agent_id": h.from_agent_id,
                                        "to_agent_id": h.to_agent_id, "stato": "aperto",
                                        **{k: getattr(h, k) for k in Handoff.TESTI}})
        if h.task_id:
            self._x("UPDATE tasks SET next_step=?, updated_at=? WHERE id=?", (h.next_step, adesso(), h.task_id))
            self.add_memory("ripresa", testo_ripresa(h), f"handoff #{hid}", t.get("project_id"), h.task_id, user_id)
        if device_id:
            self._x("UPDATE devices SET last_checkpoint=? WHERE id=?", (h.timestamp, device_id))
        verso = f" → {dest['nome']}" if dest else ""
        self.add_event("handoff" if dest else "checkpoint", f"Handoff salvato{verso}. Prossimo passo: {h.next_step}",
                       user_id=user_id,
                       agent_name=h.agent_name, agent_id=h.from_agent_id, task_id=h.task_id, device_id=device_id,
                       files=h.files_changed, project_id=t.get("project_id") if t else None)
        if dest:  # specchio del trigger handoffs_notifica (migrazione 004)
            self._notifica("handoff_to_you", f"Handoff per {dest['nome']}: {h.next_step}", [dest["user_id"]],
                           "handoffs", hid)
        return hid

    def handoff(self, handoff_id: int) -> dict | None:
        r = self._q("SELECT * FROM handoffs WHERE id=?", (handoff_id,))
        return r[0] if r else None

    def take_handoff(self, handoff_id: int, agent_id: str | None = None, by: str | None = None) -> dict:
        h = self.handoff(handoff_id)
        if not h or h["stato"] != "aperto":
            raise ValidazioneError("Handoff inesistente o già preso.")
        if agent_id and not self.agent(agent_id):
            raise ValidazioneError("Agente inesistente.")
        self._x("UPDATE handoffs SET stato='preso', to_agent_id=COALESCE(?, to_agent_id) WHERE id=? AND stato='aperto'",
                (agent_id, handoff_id))
        self.add_event("handoff_taken", f"Handoff #{handoff_id} preso" + (f" da {agent_id}" if agent_id else ""),
                       user_id=by, agent_id=agent_id, task_id=h.get("task_id"))
        return self.handoff(handoff_id)

    def close_handoff(self, handoff_id: int, by: str | None = None) -> dict:
        h = self.handoff(handoff_id)
        if not h or h["stato"] == "chiuso":
            raise ValidazioneError("Handoff inesistente o già chiuso.")
        self._x("UPDATE handoffs SET stato='chiuso' WHERE id=?", (handoff_id,))
        self.add_event("handoff_closed", f"Handoff #{handoff_id} chiuso", user_id=by, task_id=h.get("task_id"))
        return self.handoff(handoff_id)

    # --- memoria condivisa ----------------------------------------------------
    def memories(self, project_id=None, task_id=None, kind=None, q: str | None = None, includi_superate: bool = False,
                 limit: int = 100) -> list[dict]:
        where, args = [], []
        for col, val in (("project_id", project_id), ("task_id", task_id), ("kind", kind)):
            if val not in (None, ""):
                where.append(f"{col}=?")
                args.append(val)
        if not includi_superate:
            where.append("superseded_by IS NULL")
        for parola in (q or "").split():
            where.append("lower(content) LIKE ?")
            args.append(f"%{parola.lower()}%")
        w = (" WHERE " + " AND ".join(where)) if where else ""
        return self._q(f"SELECT * FROM memory{w} ORDER BY created_at DESC, id DESC LIMIT ?", (*args, limit))

    def add_memory(self, kind, content, source, project_id=None, task_id=None, created_by=None) -> int:
        campi = valida_memoria(kind, content, source)
        return self._insert("memory", {**campi, "project_id": project_id, "task_id": task_id,
                                       "created_by": created_by, "created_at": adesso()})

    def supersede_memory(self, old_id: int, new_id: int) -> None:
        if old_id == new_id or not self._q("SELECT 1 FROM memory WHERE id=?", (new_id,)):
            raise ValidazioneError("La voce che sostituisce deve esistere ed essere diversa.")
        self._x("UPDATE memory SET superseded_by=? WHERE id=?", (new_id, old_id))

    # --- approvazioni --------------------------------------------------------
    def approvals(self, status: str | None = None) -> list[dict]:
        if status:
            return self._q("SELECT * FROM approvals WHERE status=? ORDER BY created_at DESC", (status,))
        return self._q("SELECT * FROM approvals ORDER BY created_at DESC")

    def request_approval(self, action, description="", task_id=None, requested_by=None, action_type="altro",
                         reason=None, impact=None, data_involved=None, agent_id=None) -> int:
        aid = self._insert("approvals", {
            "task_id": task_id, "action": pulisci(action, 200, True, "azione"),
            "description": pulisci(description, 2000), "status": "richiesta", "requested_by": requested_by,
            "created_at": adesso(), "action_type": scegli(action_type, ACTION_TYPES, "Tipo di azione"),
            "reason": pulisci(reason, 1000, nome="motivo") or None, "impact": pulisci(impact, 1000, nome="impatto") or None,
            "data_involved": pulisci(data_involved, 1000, nome="dati coinvolti") or None, "agent_id": agent_id})
        t = self.task(task_id) if task_id else None
        if t and t["stato"] in TASK_APERTI:  # specchio del trigger approvals_task_needs_approval
            self._x("UPDATE tasks SET stato='needs_approval', updated_at=? WHERE id=?", (adesso(), task_id))
        self.add_event("approval_requested", f"Richiesta approvazione: {action}", user_id=requested_by,
                       task_id=task_id, agent_id=agent_id, severity="warning")
        self._notifica("approval_requested", f"Da approvare: {action}", None, "approvals", aid)
        return aid

    def decide_approval(self, approval_id: int, status: str, decided_by: str) -> None:
        status = scegli(status, APPROVAL_STATI[1:], "Decisione")
        a = self._q("SELECT * FROM approvals WHERE id=? AND status='richiesta'", (approval_id,))
        if not a:
            return  # già decisa o inesistente: nessun cambio
        a = a[0]
        self._x("UPDATE approvals SET status=?, decided_by=?, decided_at=? WHERE id=?",
                (status, decided_by, adesso(), approval_id))
        t = self.task(a["task_id"]) if a["task_id"] else None
        if t and t["stato"] == "needs_approval" and not self._q(
                "SELECT 1 FROM approvals WHERE task_id=? AND status='richiesta'", (t["id"],)):
            nuovo = "blocked" if status == "rifiutata" else "ready"
            if nuovo == "ready" and any(s["stato"] != "completed" for s in self._q(
                    f"SELECT stato FROM tasks WHERE id IN ({','.join('?' * len(t['depends_on']))})", t["depends_on"])):
                nuovo = "planned"
            self._x("UPDATE tasks SET stato=?, updated_at=? WHERE id=?", (nuovo, adesso(), t["id"]))
        self.add_event("approval_decided", f"Approvazione #{approval_id} ({a['action']}): {status}",
                       user_id=decided_by, task_id=a["task_id"])
        if a.get("requested_by"):
            self._notifica("approval_decided", f"{a['action']}: {status}", [a["requested_by"]], "approvals", approval_id)

    # --- API del Guardian Bridge (specchio delle funzioni RPC SQL) ------------
    def _device_by_token(self, token: str) -> dict:
        with self._lock:
            r = self._db.execute("SELECT * FROM devices WHERE token_hash=?", (hash_token(token or ""),)).fetchone()
        if not r:
            raise PermissionError("Token dispositivo non valido.")
        return dict(r)

    def bridge_heartbeat(self, token, stato="online", agent_name=None, model=None, current_task=None,
                         error=None, limit_reached=False) -> dict:
        d = self._device_by_token(token)
        stato = scegli(stato, DEVICE_STATI, "Stato")
        prima = d["stato"]
        self._x("UPDATE devices SET stato=?, agent_name=COALESCE(?, agent_name), model=COALESCE(?, model), "
                "current_task_id=?, error=?, limit_reached=?, last_seen=? WHERE id=?",
                (stato, pulisci(agent_name, 80) or None, pulisci(model, 80) or None, current_task,
                 pulisci(error, 500) or None, int(bool(limit_reached)), adesso(), d["id"]))
        if prima != stato or limit_reached or error:
            msg = f"{d['nome']}: {stato}" + (" (limite raggiunto)" if limit_reached else "") + (f" — {error}" if error else "")
            self.add_event("stato_dispositivo", msg, user_id=d["user_id"], agent_name=agent_name or d["agent_name"],
                           device_id=d["id"], task_id=current_task,
                           severity="warning" if (limit_reached or error) else "info")
        return self._q("SELECT * FROM devices WHERE id=?", (d["id"],))[0]

    def bridge_event(self, token, event_type, message, task_id=None, files=None, external_key=None) -> bool:
        d = self._device_by_token(token)
        return self.add_event(event_type, message, user_id=d["user_id"], agent_name=d["agent_name"],
                              task_id=task_id, device_id=d["id"], files=files, external_key=external_key)

    def bridge_task_update(self, token, task_id, stato=None, next_step=None, files=None) -> dict:
        d = self._device_by_token(token)
        campi = {k: v for k, v in (("stato", stato), ("next_step", next_step), ("files_changed", files)) if v}
        return self.update_task(task_id, by=d["user_id"], agent_name=d["agent_name"], device_id=d["id"], **campi)

    def bridge_checkpoint(self, token, **campi) -> int:
        d = self._device_by_token(token)
        if campi.get("from_agent_id"):
            self._agente_del_device(d, campi["from_agent_id"])
        campi = {k: v for k, v in campi.items() if v is not None}
        campi.setdefault("agent_name", d["agent_name"] or d["nome"])
        return self.add_handoff(Handoff(**campi), device_id=d["id"], user_id=d["user_id"])

    def bridge_handoff_take(self, token, handoff_id, agent_id) -> dict:
        d = self._device_by_token(token)
        a = self._agente_del_device(d, agent_id)
        return self.take_handoff(handoff_id, a["id"], d["user_id"])

    def bridge_memory_add(self, token, kind, content, source, project_id=None, task_id=None) -> int:
        d = self._device_by_token(token)
        return self.add_memory(kind, content, source, project_id, task_id, d["user_id"])

    def bridge_memory_search(self, token, q=None, project_id=None, task_id=None) -> list[dict]:
        self._device_by_token(token)
        return self.memories(project_id, task_id, q=q, limit=50)

    def bridge_pull_tasks(self, token) -> list[dict]:
        d = self._device_by_token(token)
        aperti = ",".join(f"'{s}'" for s in TASK_APERTI if s not in ("backlog",))
        return self._q(f"SELECT * FROM tasks WHERE responsabile=? AND stato IN ({aperti}) "
                       f"ORDER BY {ORDINE_PRIORITA}, updated_at DESC", (d["user_id"],))

    # --- Bridge v2: agenti (specchio di supabase/migrations/003_bridge_agenti.sql) -------------
    def _agente_del_device(self, d: dict, agent_id: str) -> dict:
        a = self.agent((agent_id or "").lower())
        if not a:
            raise ValidazioneError(f"Agente non registrato: {agent_id}")
        if a["user_id"] != d["user_id"]:
            raise PermissionError("Agente di un altro collaboratore.")
        return a

    def bridge_agent_register(self, token, agent_id, nome, tipo, capabilities=()) -> dict:
        d = self._device_by_token(token)
        a = self.agent((agent_id or "").lower())
        if a and a["user_id"] != d["user_id"]:
            raise PermissionError("Agente di un altro collaboratore.")
        caps = list(capabilities or []) or (a["capabilities"] if a else [])
        return self.upsert_agent(agent_id, d["user_id"], nome, tipo, device_id=d["id"], capabilities=caps,
                                 disponibile=a["disponibile"] if a else True)

    def bridge_agent_state(self, token, agent_id, stato, current_task=None, error=None, usage=None) -> dict:
        d = self._device_by_token(token)
        a = self._agente_del_device(d, agent_id)
        stato = scegli(stato, AGENT_STATI, "Stato agente")
        prima, ora = a["stato"], adesso()
        attivita = ora if (stato in ("working", "waiting", "needs_approval") or prima != stato) else a["last_activity"]
        self._x("UPDATE agents SET stato=?, current_task_id=?, error=?, usage=COALESCE(?, usage), last_heartbeat=?, "
                "device_id=?, last_activity=? WHERE id=?",
                (stato, current_task, pulisci(error, 500, nome="errore") or None,
                 json.dumps(usage) if usage is not None else None, ora, d["id"], attivita, a["id"]))
        if prima != stato:
            tipo = ("agent_disconnected" if stato == "offline" else "agent_connected" if prima in ("offline", "unknown")
                    else "error" if stato == "error" else "agent_state")
            sev = "error" if stato == "error" else "warning" if stato in ("needs_approval", "waiting") else "info"
            self.add_event(tipo, f"{a['nome']}: {prima} → {stato}" + (f" — {error}" if error else ""),
                           user_id=d["user_id"], agent_id=a["id"], agent_name=a["nome"], device_id=d["id"],
                           task_id=current_task, severity=sev)
            if stato == "error":
                self._notifica("agent_error", f"Agente {a['nome']} in errore: {error or 'senza dettagli'}",
                               [a["user_id"]], "agents", a["id"])
        return self.agent(a["id"])

    def bridge_agent_logs(self, token, agent_id, rows: list[dict]) -> int:
        d = self._device_by_token(token)
        a = self._agente_del_device(d, agent_id)
        if len(rows or []) > 500:
            raise ValidazioneError("Troppi log in una chiamata (max 500).")
        n = 0
        for r in rows or []:
            msg = (r.get("message") or "")[:400]
            if not msg:
                continue
            level = r.get("level") if r.get("level") in ("debug", "info", "warning", "error") else "info"
            self._insert("agent_logs", {"agent_id": a["id"], "device_id": d["id"], "task_id": r.get("task_id"),
                                        "level": level, "source": (r.get("source") or "bridge")[:20], "message": msg,
                                        "ts": r.get("ts") or adesso()})
            n += 1
        return n

    def bridge_claim_task(self, token, agent_id, task_id) -> dict:
        d = self._device_by_token(token)
        a = self._agente_del_device(d, agent_id)
        t = self.task(task_id)
        if not t:
            raise ValidazioneError("Task inesistente.")
        if t["responsabile"] != d["user_id"]:
            raise ValidazioneError("Task non assegnato a questo collaboratore.")
        if t["assigned_agent_id"] and t["assigned_agent_id"] != a["id"]:
            raise ValidazioneError("Task assegnato a un altro agente.")
        if t["stato"] != "ready":
            raise ValidazioneError(f"Il task deve essere ready per essere preso (ora: {t['stato']}).")
        self._x("UPDATE tasks SET stato='running', assigned_agent_id=?, updated_at=? WHERE id=?",
                (a["id"], adesso(), task_id))
        self._x("UPDATE agents SET current_task_id=?, stato='working', last_activity=? WHERE id=?",
                (task_id, adesso(), a["id"]))
        self.add_event("task_started", f"{a['nome']} ha preso il task #{task_id}: {t['titolo']}", user_id=d["user_id"],
                       agent_id=a["id"], agent_name=a["nome"], device_id=d["id"], task_id=task_id,
                       project_id=t.get("project_id"))
        return self.task(task_id)

    def agent_logs(self, agent_id=None, device_id=None, project_id=None, task_id=None, level=None, dal=None, al=None,
                   limit: int = 200) -> list[dict]:
        where, args = [], []
        for col, val in (("agent_id", agent_id), ("device_id", device_id), ("project_id", project_id),
                         ("task_id", task_id), ("level", level)):
            if val not in (None, ""):
                where.append(f"{col}=?")
                args.append(val)
        if dal:
            where.append("ts>=?")
            args.append(dal)
        if al:
            where.append("ts<=?")
            args.append(al)
        w = (" WHERE " + " AND ".join(where)) if where else ""
        return self._q(f"SELECT * FROM agent_logs{w} ORDER BY ts DESC, id DESC LIMIT ?", (*args, limit))

    def bridge_import_registro(self, token, rows: list[dict]) -> int:
        self._device_by_token(token)
        utenti = {u["id"] for u in self.users()}
        n = 0
        for r in rows:
            if r.get("chi") not in utenti:
                continue
            esito = r.get("esito") or ""
            if self.add_event("registro", f"{r.get('azione', '')}" + (f" [{esito}]" if esito else ""),
                              user_id=r["chi"], agent_name=r.get("agente") or None, files=r.get("file") or [],
                              external_key=r["external_key"], timestamp=r.get("ts"),
                              severity="warning" if esito in ("bloccato", "fallito") else "info"):
                n += 1
        return n

