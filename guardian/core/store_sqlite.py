"""SqliteStore: archivio locale (sviluppo e test). Le funzioni bridge_* replicano le RPC SQL del Guardian Bridge."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path

from .models import APPROVAL_STATI, DEVICE_STATI, Handoff, ValidazioneError, adesso, pulisci, pulisci_file, scegli
from .store import LIST_FIELDS, _valida_task, hash_token, nuovo_token

SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, nome TEXT NOT NULL, email TEXT UNIQUE, ruolo TEXT,
  agente TEXT, stato TEXT NOT NULL DEFAULT 'attivo');
CREATE TABLE IF NOT EXISTS devices (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL REFERENCES users(id),
  nome TEXT NOT NULL, agent_name TEXT, model TEXT, stato TEXT NOT NULL DEFAULT 'offline', current_task_id INTEGER,
  error TEXT, limit_reached INTEGER NOT NULL DEFAULT 0, last_seen TEXT, last_checkpoint TEXT,
  token_hash TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, titolo TEXT NOT NULL, descrizione TEXT,
  responsabile TEXT REFERENCES users(id), agente TEXT, priorita TEXT NOT NULL DEFAULT 'media',
  stato TEXT NOT NULL DEFAULT 'in attesa', next_step TEXT, files_changed TEXT NOT NULL DEFAULT '[]',
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
CREATE INDEX IF NOT EXISTS idx_events_ts ON activity_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_stato ON tasks(stato);
"""



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
            self._db.executescript(SCHEMA_SQLITE)

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
            if "limit_reached" in d:
                d["limit_reached"] = bool(d["limit_reached"])
            d.pop("token_hash", None)
            out.append(d)
        return out

    def _x(self, sql: str, args=()) -> int:
        with self._lock:
            cur = self._db.execute(sql, args)
            self._db.commit()
            return cur.lastrowid

    def _insert(self, tabella: str, campi: dict) -> int:
        campi = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v) for k, v in campi.items()}
        cols = ", ".join(campi)
        return self._x(f"INSERT INTO {tabella} ({cols}) VALUES ({', '.join('?' * len(campi))})",
                       tuple(campi.values()))

    # --- utenti e dispositivi -------------------------------------------------
    def users(self) -> list[dict]:
        return self._q("SELECT * FROM users ORDER BY id")

    def upsert_user(self, id: str, nome: str, email: str | None = None, ruolo: str = "", agente: str = "",
                    stato: str = "attivo") -> None:
        self._x("INSERT INTO users (id, nome, email, ruolo, agente, stato) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET nome=excluded.nome, email=COALESCE(excluded.email, users.email), "
                "ruolo=excluded.ruolo, agente=excluded.agente, stato=excluded.stato",
                (id, nome, (email or None) and email.lower(), ruolo, agente, stato))

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

    # --- task ----------------------------------------------------------------
    def tasks(self, stato: str | None = None) -> list[dict]:
        if stato:
            return self._q("SELECT * FROM tasks WHERE stato=? ORDER BY updated_at DESC", (stato,))
        return self._q("SELECT * FROM tasks ORDER BY updated_at DESC")

    def task(self, task_id: int) -> dict | None:
        r = self._q("SELECT * FROM tasks WHERE id=?", (task_id,))
        return r[0] if r else None

    def create_task(self, titolo, descrizione="", responsabile=None, agente="", priorita="media",
                    next_step="", created_by=None) -> dict:
        campi = _valida_task({"titolo": titolo, "descrizione": descrizione, "responsabile": responsabile,
                              "agente": agente, "priorita": priorita, "next_step": next_step})
        ora = adesso()
        tid = self._insert("tasks", {**campi, "stato": "in attesa", "files_changed": [], "created_by": created_by,
                                     "created_at": ora, "updated_at": ora})
        self.add_event("task_creato", f"Creato task: {campi['titolo']}", user_id=created_by, task_id=tid)
        return self.task(tid)

    def update_task(self, task_id: int, by: str | None = None, agent_name: str | None = None,
                    device_id: int | None = None, **campi) -> dict:
        campi = _valida_task(campi)
        if not campi or not self.task(task_id):
            raise ValidazioneError("Task inesistente o nessuna modifica.")
        campi["updated_at"] = adesso()
        sets = ", ".join(f"{k}=?" for k in campi)
        vals = [json.dumps(v) if isinstance(v, list) else v for v in campi.values()]
        self._x(f"UPDATE tasks SET {sets} WHERE id=?", (*vals, task_id))
        descr = ", ".join(f"{k}={v}" for k, v in campi.items() if k in ("stato", "priorita", "responsabile", "agente"))
        self.add_event("task_aggiornato", f"Task #{task_id} aggiornato{': ' + descr if descr else ''}",
                       user_id=by, agent_name=agent_name, task_id=task_id, device_id=device_id,
                       files=campi.get("files_changed") or [])
        return self.task(task_id)

    # --- eventi --------------------------------------------------------------
    def events(self, limit: int = 100, task_id: int | None = None) -> list[dict]:
        if task_id:
            return self._q("SELECT * FROM activity_events WHERE task_id=? ORDER BY timestamp DESC, id DESC LIMIT ?",
                           (task_id, limit))
        return self._q("SELECT * FROM activity_events ORDER BY timestamp DESC, id DESC LIMIT ?", (limit,))

    def add_event(self, event_type, message, user_id=None, agent_name=None, task_id=None, device_id=None,
                  files=None, external_key=None, timestamp=None) -> bool:
        try:
            self._insert("activity_events", {
                "event_type": pulisci(event_type, 40, True, "tipo evento"), "message": pulisci(message, 1000, True, "messaggio"),
                "user_id": user_id, "agent_name": agent_name, "task_id": task_id, "device_id": device_id,
                "files": pulisci_file(files), "external_key": external_key, "timestamp": timestamp or adesso()})
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
        if h.task_id and not self.task(h.task_id):
            raise ValidazioneError(f"Task #{h.task_id} inesistente.")
        hid = self._insert("handoffs", {"task_id": h.task_id, "device_id": device_id, "agent_name": h.agent_name,
                                        "summary": h.summary, "completed_steps": h.completed_steps,
                                        "files_changed": h.files_changed, "decisions": h.decisions,
                                        "errors": h.errors, "tests": h.tests, "next_step": h.next_step,
                                        "timestamp": h.timestamp})
        if h.task_id:
            self._x("UPDATE tasks SET next_step=?, updated_at=? WHERE id=?", (h.next_step, adesso(), h.task_id))
        if device_id:
            self._x("UPDATE devices SET last_checkpoint=? WHERE id=?", (h.timestamp, device_id))
        self.add_event("checkpoint", f"Handoff salvato. Prossimo passo: {h.next_step}", user_id=user_id,
                       agent_name=h.agent_name, task_id=h.task_id, device_id=device_id, files=h.files_changed)
        return hid

    # --- approvazioni --------------------------------------------------------
    def approvals(self, status: str | None = None) -> list[dict]:
        if status:
            return self._q("SELECT * FROM approvals WHERE status=? ORDER BY created_at DESC", (status,))
        return self._q("SELECT * FROM approvals ORDER BY created_at DESC")

    def request_approval(self, action, description="", task_id=None, requested_by=None) -> int:
        aid = self._insert("approvals", {"task_id": task_id, "action": pulisci(action, 200, True, "azione"),
                                         "description": pulisci(description, 2000), "status": "richiesta",
                                         "requested_by": requested_by, "created_at": adesso()})
        self.add_event("approvazione_richiesta", f"Richiesta approvazione: {action}", user_id=requested_by,
                       task_id=task_id)
        return aid

    def decide_approval(self, approval_id: int, status: str, decided_by: str) -> None:
        status = scegli(status, APPROVAL_STATI[1:], "Decisione")
        self._x("UPDATE approvals SET status=?, decided_by=?, decided_at=? WHERE id=? AND status='richiesta'",
                (status, decided_by, adesso(), approval_id))
        self.add_event("approvazione_decisa", f"Approvazione #{approval_id}: {status}", user_id=decided_by)

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
                           device_id=d["id"], task_id=current_task)
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
        campi.setdefault("agent_name", d["agent_name"] or d["nome"])
        return self.add_handoff(Handoff(**campi), device_id=d["id"], user_id=d["user_id"])

    def bridge_pull_tasks(self, token) -> list[dict]:
        d = self._device_by_token(token)
        return self._q("SELECT * FROM tasks WHERE responsabile=? AND stato IN ('in attesa','in corso','bloccato') "
                       "ORDER BY CASE priorita WHEN 'urgente' THEN 0 WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END, "
                       "updated_at DESC", (d["user_id"],))

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
                              external_key=r["external_key"], timestamp=r.get("ts")):
                n += 1
        return n
