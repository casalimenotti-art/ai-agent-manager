#!/usr/bin/env python3
"""Smoke test di Guardian sul progetto Supabase reale (da eseguire dal titolare, una volta dopo il setup).

  SUPABASE_URL=https://….supabase.co SUPABASE_ANON_KEY=… python scripts/smoke_supabase.py tua@email
  (la password viene chiesta a terminale e non viene salvata)
  Facoltativo: GUARDIAN_DEVICE_TOKEN=… per provare anche le RPC del bridge.

Crea un task di prova, lo porta a 'cancelled' e lascia traccia nella timeline: nessun altro dato viene modificato.
"""
from __future__ import annotations

import getpass
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def passi_store(store, user_id: str) -> list[tuple[str, bool, str]]:
    """Controlli che valgono per qualsiasi store (testati anche su SQLite)."""
    esiti = []

    def passo(nome, fn):
        try:
            dettaglio = fn()
            esiti.append((nome, True, str(dettaglio or "")))
        except Exception as e:  # il test deve proseguire e riportare tutto
            esiti.append((nome, False, f"{type(e).__name__}: {e}"[:200]))

    passo("database raggiungibile", lambda: store.ping() and "ok")
    passo("collaboratori visibili", lambda: f"{len(store.users())} utenti")
    titolo = f"Smoke test Guardian {time.strftime('%Y-%m-%d %H:%M:%S')}"
    creato = {}
    passo("crea task", lambda: creato.update(t=store.create_task(titolo, "prova automatica", created_by=user_id)) or creato["t"]["id"])
    passo("chiudi task", lambda: store.update_task(creato["t"]["id"], by=user_id, stato="cancelled")["stato"])
    passo("timeline", lambda: f"{len(store.events(5))} eventi recenti")
    passo("notifiche personali", lambda: f"{len(store.notifications(user_id))} notifiche")
    passo("memoria", lambda: f"{len(store.memories(limit=5))} voci")
    return esiti


def passi_bridge(url: str, key: str, token: str) -> list[tuple[str, bool, str]]:
    from bridge.guardian_bridge import RpcClient
    c = RpcClient(url, key, token)
    try:
        r = c.call("bridge_heartbeat", stato="online", agent_name=None, model=None, current_task=None, error=None,
                   limit_reached=False)
        return [("bridge: heartbeat del PC", True, r.get("nome", ""))]
    except Exception as e:
        return [("bridge: heartbeat del PC", False, f"{type(e).__name__}: {e}"[:200])]


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    url, key = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_ANON_KEY", "")
    if not (url and key and argv):
        print(__doc__)
        return 2
    from guardian.core.store_supabase import SupabaseStore
    store = SupabaseStore(url, key)
    try:
        utente = store.login(argv[0], getpass.getpass("Password Guardian: "))
    except Exception as e:
        print(f"Login non riuscito: {type(e).__name__}: {e}")
        return 1
    esiti = passi_store(store, utente["id"])
    if os.environ.get("GUARDIAN_DEVICE_TOKEN"):
        esiti += passi_bridge(url, key, os.environ["GUARDIAN_DEVICE_TOKEN"])
    for nome, ok, dettaglio in esiti:
        print(f"{'OK  ' if ok else 'FAIL'} {nome}{' — ' + dettaglio if dettaglio else ''}")
    store.logout()
    return 0 if all(ok for _, ok, _ in esiti) else 1


if __name__ == "__main__":
    raise SystemExit(main())
