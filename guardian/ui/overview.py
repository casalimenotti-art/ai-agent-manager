import streamlit as st

from guardian.core.models import TASK_STATI, stato_dispositivo
from guardian.ui.components import Ctx, esegui, pill, riga_evento


def render(ctx: Ctx) -> None:
    store = ctx.store
    devices = esegui(store.devices) or []
    tasks = esegui(store.tasks) or []
    stati_dev = [stato_dispositivo(d) for d in devices]
    online = sum(s != "offline" for s in stati_dev)
    attivi = sum(1 for d, s in zip(devices, stati_dev) if s in ("online", "occupato") and d.get("agent_name"))
    conta = {s: sum(t["stato"] == s for t in tasks) for s in TASK_STATI}
    errori = sum(s in ("errore", "limite") for s in stati_dev)
    attese = len(esegui(store.approvals, "richiesta") or [])
    c = st.columns(4)
    c[0].metric("PC online", f"{online}/{len(devices)}")
    c[1].metric("Agenti attivi", attivi)
    c[2].metric("Task in corso", conta["in corso"])
    c[3].metric("Task completati", conta["completato"])
    c = st.columns(4)
    c[0].metric("In attesa", conta["in attesa"])
    c[1].metric("Bloccati", conta["bloccato"])
    c[2].metric("Errori / limiti", errori)
    c[3].metric("Approvazioni da decidere", attese)
    st.subheader("Collaboratori")
    utenti = esegui(store.users) or []
    for col, u in zip(st.columns(max(1, len(utenti))), utenti):
        suoi = [(d, s) for d, s in zip(devices, stati_dev) if d["user_id"] == u["id"]]
        stato = "online" if any(s != "offline" for _, s in suoi) else "offline"
        with col.container(border=True):
            st.markdown(f"**{u['nome']}** {pill(stato)}", unsafe_allow_html=True)
            st.caption(f"{u.get('agente') or '—'} · {u.get('ruolo') or ''}")
            st.caption(f"{len(suoi)} PC registrati" if suoi else "Nessun PC collegato: stato non disponibile")
    st.subheader("Attività recenti")
    eventi = esegui(store.events, 10) or []
    if not eventi:
        st.info("Nessuna attività registrata. Gli eventi arrivano dal bridge o dal registro (sync-registro).")
    for e in eventi:
        riga_evento(ctx, e)
