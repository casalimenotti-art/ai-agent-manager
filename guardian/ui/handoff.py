"""Handoff tra agenti: passaggio di lavoro completo, preso in carico e chiuso. Non è un semplice cambio di modello."""
import streamlit as st

from guardian.core.models import HANDOFF_STATI, TASK_TERMINALI, Handoff
from guardian.ui.components import Ctx, esegui, fa

COLORE = {"aperto": "waiting", "preso": "working", "chiuso": "ok"}


def _form(ctx: Ctx, tasks: dict, agenti: dict) -> None:
    with st.expander("💾 Salva handoff / checkpoint", expanded=False):
        with st.form("handoff", clear_on_submit=True):
            c = st.columns(3)
            tid = c[0].selectbox("Task", [None, *tasks], format_func=lambda i: "— nessuno —" if i is None else f"#{i} {tasks[i]}")
            da = c[1].selectbox("Da (agente)", [None, *agenti], format_func=lambda x: agenti.get(x, "— (persona)"))
            per = c[2].selectbox("Per (agente)", [None, *agenti], format_func=lambda x: agenti.get(x, "— chiunque"))
            summary = st.text_area("Obiettivo originale e stato attuale *", height=90)
            c = st.columns(2)
            done = c[0].text_area("Lavoro completato", height=70)
            dec = c[1].text_area("Decisioni prese", height=70)
            err = c[0].text_area("Problemi incontrati", height=70)
            tests = c[1].text_area("Test eseguiti", height=70)
            pending = c[0].text_area("Test ancora necessari", height=70)
            deps = c[1].text_area("Dipendenze", height=70)
            note = st.text_area("Informazioni importanti da non perdere", height=60)
            files = st.text_area("File modificati (uno per riga)", height=60)
            nxt = st.text_input("Prossimo passo preciso *")
            if st.form_submit_button("Salva handoff", type="primary"):
                h = Handoff(agent_name=agenti.get(da, ctx.io["nome"]).split(" (")[0], summary=summary, next_step=nxt,
                            task_id=tid, completed_steps=done, decisions=dec, errors=err, tests=tests,
                            tests_pending=pending, dependencies=deps, important_notes=note,
                            files_changed=files.splitlines(), from_agent_id=da, to_agent_id=per)
                if esegui(ctx.store.add_handoff, h, user_id=ctx.io["id"], ok="Handoff salvato"):
                    st.rerun()


def render(ctx: Ctx) -> None:
    st.caption("Un handoff conserva tutto il contesto per riprendere il lavoro: chi lo prende parte dal «Prossimo passo». "
               "Cambiare modello o provider non è un handoff.")
    tasks = {t["id"]: t["titolo"] for t in (esegui(ctx.store.tasks) or []) if t["stato"] not in TASK_TERMINALI}
    agenti = {a["id"]: f"{a['nome']} ({ctx.nome(a['user_id'])})" for a in (esegui(ctx.store.agents) or [])}
    _form(ctx, tasks, agenti)
    filtro = st.segmented_control("Stato", HANDOFF_STATI, default="aperto", key="filtro_handoff")
    lista = [r for r in (esegui(ctx.store.handoffs) or []) if not filtro or (r.get("stato") or "aperto") == filtro]
    if not lista:
        st.info("Nessun handoff in questo stato.")
    for r in lista:
        h = Handoff.da_riga(r)
        task = f" · task #{r['task_id']}" if r.get("task_id") else ""
        per = f" → {agenti.get(h.to_agent_id, h.to_agent_id)}" if h.to_agent_id else ""
        with st.container(border=True):
            st.markdown(f"**{r['agent_name']}{per}** <span class='g-pill g-{COLORE[h.stato]}'>{h.stato}</span> "
                        f"<small>{fa(r['timestamp'])}{task}</small>", unsafe_allow_html=True)
            st.markdown(f"**Prossimo passo:** {h.next_step}")
            with st.expander("Dettagli completi"):
                st.markdown(h.markdown())
            c = st.columns(3)
            c[0].download_button("Scarica .md", h.markdown(), file_name=f"handoff-{r['id']}.md", key=f"dl_{r['id']}")
            if h.stato == "aperto":
                chi = c[1].selectbox("Chi lo prende", [None, *agenti], key=f"chi_{r['id']}",
                                     format_func=lambda x: agenti.get(x, "— io"), label_visibility="collapsed")
                if c[2].button("Prendi in carico", key=f"take_{r['id']}", type="primary"):
                    esegui(ctx.store.take_handoff, r["id"], chi, ctx.io["id"], ok="Handoff preso")
                    st.rerun()
            elif h.stato == "preso" and c[2].button("Chiudi", key=f"close_{r['id']}"):
                esegui(ctx.store.close_handoff, r["id"], ctx.io["id"], ok="Handoff chiuso")
                st.rerun()
