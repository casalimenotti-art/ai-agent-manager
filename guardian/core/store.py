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
