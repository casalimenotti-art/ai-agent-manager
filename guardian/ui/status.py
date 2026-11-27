"""Stato reale del sistema: app, database, aggiornamento, bridge e agenti. Nessun indicatore inventato."""
from __future__ import annotations

import time

import streamlit as st

from guardian.core.models import stato_agente, stato_dispositivo
from guardian.ui.components import Ctx, pill

POLLING_SECONDI = 20


def misura_db(store) -> tuple[bool, float | None, str]:
    t0 = time.perf_counter()
    try:
        store.ping()
        return True, (time.perf_counter() - t0) * 1000, ""
    except Exception as e:  # rete, credenziali, DB in pausa
        return False, None, type(e).__name__


def stato_sistema(ctx: Ctx, devices: list[dict], agents: list[dict]) -> dict:
    ok, ms, errore = misura_db(ctx.store)
    return {
        "db_ok": ok, "db_ms": ms, "db_errore": errore,
        "backend": "Supabase (condiviso)" if ctx.store.modalita == "supabase" else "SQLite locale (non condiviso)",
        "pc_online": sum(stato_dispositivo(d) != "offline" for d in devices), "pc_totali": len(devices),
        "agenti_con_segnale": sum(stato_agente(a) not in ("unknown", "offline") for a in agents),
        "agenti_totali": len(agents),
    }


def render_barra(ctx: Ctx, devices: list[dict], agents: list[dict]) -> dict:
    s = stato_sistema(ctx, devices, agents)
    db = (f"{pill('ok')} {s['db_ms']:.0f} ms" if s["db_ok"] else f"{pill('error')} non raggiungibile ({s['db_errore']})")
    bridge = pill("ok") if s["pc_online"] else pill("unknown")
    st.markdown(
        f"<small>**App** {pill('ok')} &nbsp; **Database** {db} &nbsp; **Backend** {s['backend']} &nbsp; "
        f"**Aggiornamento** polling ogni {POLLING_SECONDI} s (non push) &nbsp; "
        f"**Bridge** {bridge} {s['pc_online']}/{s['pc_totali']} PC · {s['agenti_con_segnale']}/{s['agenti_totali']} agenti con segnale"
        f"</small>", unsafe_allow_html=True)
    return s
