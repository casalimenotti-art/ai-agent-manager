"""Archivio di Guardian: funzioni comuni e scelta del backend.

- SqliteStore (core/store_sqlite.py): sviluppo locale e test, stesso schema delle migrazioni Supabase.
- SupabaseStore (core/store_supabase.py): produzione condivisa (Postgres + Auth + RLS).
"""
from __future__ import annotations

import hashlib
import json
import secrets

from .models import PRIORITA, REPO, TASK_STATI, ValidazioneError, pulisci, pulisci_file, scegli

LIST_FIELDS = ("files_changed", "files")
TASK_MODIFICABILI = ("titolo", "descrizione", "responsabile", "agente", "priorita", "stato", "next_step",
                     "files_changed")


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
            out[k] = scegli(v, TASK_STATI, "Stato")
        elif k == "priorita":
            out[k] = scegli(v, PRIORITA, "Priorità")
        elif k == "files_changed":
            out[k] = pulisci_file(v)
        elif k == "titolo":
            out[k] = pulisci(v, 200, True, "titolo")
        else:
            out[k] = pulisci(v, 4000, nome=k) or None
    return out



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
