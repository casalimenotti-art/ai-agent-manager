"""Archivio di Guardian: funzioni comuni e scelta del backend.

- SqliteStore (core/store_sqlite.py): sviluppo locale e test, stesso schema delle migrazioni Supabase.
- SupabaseStore (core/store_supabase.py): produzione condivisa (Postgres + Auth + RLS).
"""
from __future__ import annotations

import hashlib
import json
import secrets

from .models import (PRIORITA, REPO, SEVERITA, TASK_STATI, TASK_STATI_V1, ValidazioneError, pulisci, pulisci_file,
                     scegli)

LIST_FIELDS = ("files_changed", "files", "depends_on", "capabilities")
JSON_FIELDS = ("usage", "piano")
TASK_TESTO = ("descrizione", "agente", "next_step", "result", "error", "expected_result", "completion_criteria")
TASK_ID = ("project_id", "plan_id")
TASK_MODIFICABILI = ("titolo", "responsabile", "priorita", "stato", "files_changed", "depends_on",
                     "assigned_agent_id", *TASK_TESTO, *TASK_ID)
MSG_DUPLICATO = "Esiste già un task aperto con questo titolo in questo progetto."
MSG_RUNNING = "Questo agente ha già un task in esecuzione: completalo o mettilo in attesa prima."
MSG_DIPENDENZE = "Il task ha dipendenze non ancora completate: non può essere ready/running."


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def nuovo_token() -> str:
    return "gdn_" + secrets.token_urlsafe(32)


def _valida_task(campi: dict) -> dict:
    out = {}
    for k, v in campi.items():
        if k not in TASK_MODIFICABILI:
            raise ValidazioneError(f"Campo non modificabile: {k}")
        if k == "stato":
            out[k] = scegli(TASK_STATI_V1.get(v, v), TASK_STATI, "Stato")
        elif k == "priorita":
            out[k] = scegli(v, PRIORITA, "Priorità")
        elif k == "files_changed":
            out[k] = pulisci_file(v)
        elif k == "depends_on":
            try:
                out[k] = sorted({int(x) for x in (v or [])})
            except (TypeError, ValueError):
                raise ValidazioneError("Dipendenze non valide: servono numeri di task.") from None
        elif k in TASK_ID:
            out[k] = int(v) if v not in (None, "") else None
        elif k == "titolo":
            out[k] = pulisci(v, 200, True, "titolo")
        elif k in ("responsabile", "assigned_agent_id"):
            out[k] = pulisci(v, 80, nome=k) or None
        else:
            out[k] = pulisci(v, 4000, nome=k) or None
    return out


def severita(s: str | None) -> str:
    return scegli(s or "info", SEVERITA, "Gravità")


def messaggio_db(e: Exception) -> str | None:
    """Traduce errori di vincolo del database (SQLite o Postgres) in messaggi leggibili; None se sconosciuto."""
    t = str(e)
    if "tasks_titolo_aperto" in t or ("UNIQUE" in t and "tasks" in t and "titolo" in t):
        return MSG_DUPLICATO
    if "tasks_un_running" in t or ("UNIQUE" in t and "assigned_agent_id" in t):
        return MSG_RUNNING
    if "dipendenze" in t.lower():
        return MSG_DIPENDENZE
    return None



def seed_users_da_registro(store) -> None:
    """Crea i collaboratori locali da registro/persone.json (solo modalità locale)."""
    try:
        persone = json.loads((REPO / "registro" / "persone.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for p in persone:
        store.upsert_user(p["id"], p.get("nome", p["id"]), None, p.get("ruolo", ""), p.get("agente", ""))


def crea_store_locale(path):
    """Factory per la modalità locale (SQLite) con i collaboratori di registro/persone.json."""
    from .store_sqlite import SqliteStore
    s = SqliteStore(path)
    seed_users_da_registro(s)
    return s


def valida_memoria(kind, content, source) -> dict:
    """Ogni voce di memoria ha tipo, contenuto e fonte (da dove viene l'informazione)."""
    from .models import MEMORY_KINDS
    return {"kind": scegli(kind, MEMORY_KINDS, "Tipo di memoria"),
            "content": pulisci(content, 4000, True, "contenuto"),
            "source": pulisci(source, 300, True, "fonte")}


def testo_ripresa(h) -> str:
    """Voce di memoria 'ripresa' creata da un handoff: dove eravamo e cosa fare dopo."""
    parti = [f"Prossimo passo: {h.next_step}", f"Stato: {h.summary[:1200]}"]
    if h.tests_pending:
        parti.append(f"Test ancora necessari: {h.tests_pending[:500]}")
    if h.important_notes:
        parti.append(f"Da non perdere: {h.important_notes[:800]}")
    return "\n".join(parti)


STATI_PIANO = ("bozza", "confermato", "scartato")


def conferma_piano(store, plan_id: int, by: str | None = None) -> list[int]:
    """Trasforma una bozza di piano in task reali (uguale per SQLite e Supabase).

    Ordine: i task senza dipendenze diventano ready, gli altri planned; le dipendenze indice -> id;
    i task che richiedono approvazione ricevono una richiesta di approvazione (e passano a needs_approval).
    Prima di creare qualcosa controlla i titoli già aperti nel progetto, per non lasciare piani a metà.
    """
    from guardian.planner.schema import da_dict
    from .models import TASK_TERMINALI
    p = store.plan(plan_id)
    if not p or p["stato"] != "bozza":
        raise ValidazioneError("Piano inesistente o già deciso.")
    piano = da_dict(p["piano"], p["goal"], [a["id"] for a in store.agents()])
    aperti = {t["titolo"].lower() for t in store.tasks(project_id=p.get("project_id"))
              if t["stato"] not in TASK_TERMINALI and t.get("project_id") == p.get("project_id")}
    doppi = [t.title for t in piano.tasks if t.title.lower() in aperti]
    if doppi:
        raise ValidazioneError(f"Esistono già task aperti con questi titoli: {', '.join(doppi)}")
    ids: list[int] = []
    for t in piano.tasks:
        creato = store.create_task(
            t.title, t.description, None, "", t.priority, "", created_by=by,
            stato="planned" if t.depends_on else "ready", project_id=p.get("project_id"),
            depends_on=[ids[j] for j in t.depends_on], assigned_agent_id=t.agent,
            expected_result=t.expected_result or None, completion_criteria=t.completion_criteria or None,
            plan_id=plan_id)
        ids.append(creato["id"])
        if t.requires_approval:
            store.request_approval(f"{t.title}", t.description, creato["id"], by, action_type=t.action_type,
                                   reason=t.approval_reason or "Richiesto dal piano", agent_id=t.agent)
    store.set_plan_state(plan_id, "confermato", by)
    return ids
