import streamlit as st

from guardian.core.models import Handoff
from guardian.ui.components import Ctx, esegui, fa


def _da_riga(r: dict) -> Handoff:
    return Handoff(agent_name=r["agent_name"], summary=r["summary"], next_step=r["next_step"], task_id=r.get("task_id"),
                   completed_steps=r.get("completed_steps") or "", files_changed=r.get("files_changed") or [],
                   decisions=r.get("decisions") or "", errors=r.get("errors") or "", tests=r.get("tests") or "",
                   timestamp=str(r["timestamp"]))


def render(ctx: Ctx) -> None:
    tasks = esegui(ctx.store.tasks) or []
    titoli = {t["id"]: t["titolo"] for t in tasks}
    with st.expander("💾 Salva handoff / checkpoint", expanded=False):
        with st.form("handoff", clear_on_submit=True):
            tid = st.selectbox("Task", [None, *titoli],
                               format_func=lambda i: "— nessuno —" if i is None else f"#{i} {titoli[i]}")
            agente = st.text_input("Agente", "")
            summary = st.text_area("Obiettivo e stato attuale *", height=90)
            done = st.text_area("Lavoro completato", height=70)
            dec = st.text_area("Decisioni prese", height=60)
            err = st.text_area("Problemi incontrati", height=60)
            tests = st.text_area("Test eseguiti", height=60)
            files = st.text_area("File modificati (uno per riga)", height=60)
            nxt = st.text_input("Prossimo passo preciso *")
            if st.form_submit_button("Salva handoff", type="primary"):
                h = Handoff(agent_name=agente or ctx.io["nome"], summary=summary, next_step=nxt, task_id=tid,
                            completed_steps=done, decisions=dec, errors=err, tests=tests,
                            files_changed=files.splitlines())
                if esegui(ctx.store.add_handoff, h, user_id=ctx.io["id"], ok="Handoff salvato"):
                    st.rerun()
    lista = esegui(ctx.store.handoffs) or []
    if not lista:
        st.info("Nessun handoff salvato.")
    for r in lista:
        h = _da_riga(r)
        task = f" · task #{r['task_id']}" if r.get("task_id") else ""
        with st.expander(f"{fa(r['timestamp'])} · {r['agent_name']}{task} → {r['next_step'][:80]}"):
            st.markdown(h.markdown())
            st.download_button("Scarica .md", h.markdown(), file_name=f"handoff-{r['id']}.md", key=f"dl_{r['id']}")
