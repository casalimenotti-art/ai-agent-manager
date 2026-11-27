import streamlit as st

from guardian.core.models import TASK_STATI, eta_secondi, stato_agente, stato_dispositivo
from guardian.ui.components import Ctx, esegui, pill, riga_evento
from guardian.ui.status import render_barra


def render(ctx: Ctx) -> None:
    store = ctx.store
    devices = esegui(store.devices) or []
    agents = esegui(store.agents) or []
    tasks = esegui(store.tasks) or []
    render_barra(ctx, devices, agents)
    stati_ag = [stato_agente(a) for a in agents]
    conta = {s: sum(t["stato"] == s for t in tasks) for s in TASK_STATI}
    eventi = esegui(store.events, 200) or []
    errori_24h = sum(1 for e in eventi if e.get("severity") in ("error", "critical")
                     and (eta_secondi(e["timestamp"]) or 0) < 86400)
    c = st.columns(4)
    c[0].metric("Agenti al lavoro", sum(s in ("working", "waiting", "needs_approval") for s in stati_ag),
                help="Solo agenti con eventi reali recenti dal bridge")
    c[1].metric("Task in esecuzione", conta["running"])
    c[2].metric("In coda", conta["backlog"] + conta["planned"] + conta["ready"])
    c[3].metric("Completati", conta["completed"])
    c = st.columns(4)
    c[0].metric("Bloccati / in attesa", conta["blocked"] + conta["waiting"])
    c[1].metric("Falliti", conta["failed"])
    c[2].metric("Errori (24 h)", errori_24h + sum(s == "error" for s in stati_ag))
    c[3].metric("Approvazioni da decidere", len(esegui(store.approvals, "richiesta") or []))

    st.subheader("Collaboratori")
    utenti = esegui(store.users) or []
    for col, u in zip(st.columns(max(1, len(utenti))), utenti):
        pcs = [d for d in devices if d["user_id"] == u["id"]]
        suoi = [a for a in agents if a["user_id"] == u["id"]]
        pc_on = any(stato_dispositivo(d) != "offline" for d in pcs)
        with col.container(border=True):
            st.markdown(f"**{u['nome']}** · PC {pill('online' if pc_on else 'offline')}", unsafe_allow_html=True)
            st.caption(f"{u.get('agente') or '—'} · {u.get('ruolo') or ''}")
            if not pcs:
                st.caption("Nessun PC collegato: stato non disponibile")
            for a in suoi:
                st.markdown(f"<small>{a['nome']}: {pill(stato_agente(a))}</small>", unsafe_allow_html=True)

    st.subheader("Attività recenti")
    if not eventi:
        st.info("Nessuna attività registrata. Gli eventi arrivano dal bridge, dal registro (sync-registro) o dall'Hub.")
    for e in eventi[:10]:
        riga_evento(ctx, e)
