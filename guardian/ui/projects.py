import streamlit as st

from guardian.core.models import TASK_TERMINALI
from guardian.ui.components import Ctx, esegui


def render(ctx: Ctx) -> None:
    with st.expander("➕ Nuovo progetto"):
        with st.form("nuovo_progetto", clear_on_submit=True):
            nome = st.text_input("Nome *")
            descr = st.text_area("Descrizione", height=70)
            if st.form_submit_button("Crea progetto", type="primary"):
                if esegui(ctx.store.create_project, nome, descr, ctx.io["id"], ok="Progetto creato"):
                    st.rerun()
    progetti = esegui(ctx.store.projects) or []
    tasks = esegui(ctx.store.tasks) or []
    if not progetti:
        st.info("Nessun progetto. I task possono comunque esistere senza progetto.")
    for p in progetti:
        suoi = [t for t in tasks if t.get("project_id") == p["id"]]
        aperti = sum(t["stato"] not in TASK_TERMINALI for t in suoi)
        with st.container(border=True):
            c = st.columns([4, 1])
            c[0].markdown(f"**{p['nome']}** · {p['stato']}")
            c[0].caption(f"{len(suoi)} task ({aperti} aperti, {sum(t['stato'] == 'completed' for t in suoi)} completati)"
                         + (f" · {p['descrizione']}" if p.get("descrizione") else ""))
            nuovo = "archiviato" if p["stato"] == "attivo" else "attivo"
            if c[1].button("Archivia" if nuovo == "archiviato" else "Riattiva", key=f"prj_{p['id']}"):
                esegui(ctx.store.update_project, p["id"], nuovo, ok="Progetto aggiornato")
                st.rerun()
