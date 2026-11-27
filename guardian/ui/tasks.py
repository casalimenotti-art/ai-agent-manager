import streamlit as st

from guardian.core.models import PRIORITA, TASK_STATI
from guardian.ui.components import GRUPPI_TASK, ICONE_STATO, Ctx, esegui, fa


def _form_modifica(ctx: Ctx, t: dict) -> None:
    with st.form(f"edit_{t['id']}"):
        c = st.columns(3)
        stato = c[0].selectbox("Stato", TASK_STATI, index=TASK_STATI.index(t["stato"]))
        prio = c[1].selectbox("Priorità", PRIORITA, index=PRIORITA.index(t["priorita"]))
        ids = [""] + list(ctx.nomi)
        resp = c[2].selectbox("Responsabile", ids, index=ids.index(t["responsabile"]) if t.get("responsabile") in ids else 0,
                              format_func=lambda x: ctx.nome(x) if x else "—")
        agente = st.text_input("Agente", t.get("agente") or "")
        nxt = st.text_input("Prossimo passo", t.get("next_step") or "")
        files = st.text_area("File modificati (uno per riga)", "\n".join(t.get("files_changed") or []), height=80)
        if st.form_submit_button("Salva"):
            esegui(ctx.store.update_task, t["id"], by=ctx.io["id"], stato=stato, priorita=prio, responsabile=resp or None,
                   agente=agente, next_step=nxt, files_changed=files, ok="Task aggiornato")
            st.rerun()


def render(ctx: Ctx) -> None:
    with st.expander("➕ Nuovo task", expanded=False):
        with st.form("nuovo_task", clear_on_submit=True):
            titolo = st.text_input("Titolo")
            descr = st.text_area("Descrizione", height=80)
            c = st.columns(3)
            resp = c[0].selectbox("Responsabile", [""] + list(ctx.nomi), format_func=lambda x: ctx.nome(x) if x else "—")
            agente = c[1].text_input("Agente (es. Claude Code, Codex)")
            prio = c[2].selectbox("Priorità", PRIORITA, index=1)
            nxt = st.text_input("Prossimo passo")
            if st.form_submit_button("Crea task", type="primary"):
                if esegui(ctx.store.create_task, titolo, descr, resp or None, agente, prio, nxt, created_by=ctx.io["id"],
                          ok="Task creato"):
                    st.rerun()
    tasks = esegui(ctx.store.tasks) or []
    tabs = st.tabs([f"{g} ({sum(t['stato'] in stati for t in tasks)})" for g, stati in GRUPPI_TASK.items()])
    for tab, stati in zip(tabs, GRUPPI_TASK.values()):
        with tab:
            lista = [t for t in tasks if t["stato"] in stati]
            if not lista:
                st.caption("Nessun task.")
            for t in lista:
                with st.expander(f"{ICONE_STATO[t['stato']]} #{t['id']} [{t['priorita']}] {t['titolo']} — {ctx.nome(t.get('responsabile'))}"):
                    if t.get("descrizione"):
                        st.write(t["descrizione"])
                    st.caption(f"Agente: {t.get('agente') or '—'} · aggiornato {fa(t['updated_at'])} · "
                               f"prossimo passo: {t.get('next_step') or '—'}")
                    _form_modifica(ctx, t)
