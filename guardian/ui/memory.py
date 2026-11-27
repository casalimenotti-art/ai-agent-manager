"""Memoria condivisa: informazioni durevoli per progetto e task, sempre con fonte e data."""
import streamlit as st

from guardian.core.models import MEMORY_KINDS, TASK_TERMINALI
from guardian.ui.components import Ctx, esegui, fa

ETICHETTE = {"obiettivo": "Obiettivo", "decisione": "Decisione", "info_progetto": "Info progetto",
             "preferenza": "Preferenza operativa", "risultato": "Risultato", "errore": "Errore",
             "procedura": "Procedura", "ripresa": "Punto di ripresa"}


def render(ctx: Ctx) -> None:
    progetti = {p["id"]: p["nome"] for p in (esegui(ctx.store.projects) or [])}
    tutti = esegui(ctx.store.tasks) or []
    tasks = {t["id"]: t["titolo"] for t in tutti}
    aperti = {t["id"]: t["titolo"] for t in tutti if t["stato"] not in TASK_TERMINALI}
    st.caption("Ciò che deve sopravvivere alle chat: obiettivi, decisioni, procedure, risultati, punti di ripresa. "
               "Ogni voce ha una fonte. Gli handoff con un task creano da soli un «punto di ripresa».")
    with st.expander("➕ Aggiungi alla memoria"):
        with st.form("nuova_memoria", clear_on_submit=True):
            c = st.columns(3)
            kind = c[0].selectbox("Tipo", MEMORY_KINDS, format_func=ETICHETTE.get)
            prog = c[1].selectbox("Progetto", [None, *progetti], format_func=lambda x: progetti.get(x, "—"))
            task = c[2].selectbox("Task", [None, *aperti], format_func=lambda x: f"#{x} {aperti[x]}" if x else "—")
            testo = st.text_area("Contenuto *", height=90)
            fonte = st.text_input("Fonte *", placeholder="Es. riunione del 27/11, GUARDIAN_DECISIONS.md, email del cliente")
            sostituisce = st.number_input("Sostituisce la voce # (facoltativo)", min_value=0, step=1, value=0)
            if st.form_submit_button("Salva", type="primary"):
                mid = esegui(ctx.store.add_memory, kind, testo, fonte, prog, task, ctx.io["id"])
                if mid and sostituisce:
                    esegui(ctx.store.supersede_memory, int(sostituisce), mid)
                if mid:
                    st.toast("Salvato in memoria")
                    st.rerun()
    c = st.columns(4)
    q = c[0].text_input("Cerca", placeholder="parole chiave")
    f_prog = c[1].selectbox("Progetto ", [None, *progetti], format_func=lambda x: progetti.get(x, "Tutti"))
    f_task = c[2].selectbox("Task ", [None, *tasks], format_func=lambda x: f"#{x} {tasks[x]}" if x else "Tutti")
    f_kind = c[3].selectbox("Tipo ", [None, *MEMORY_KINDS], format_func=lambda x: ETICHETTE.get(x, "Tutti"))
    superate = st.toggle("Mostra anche le voci superate", value=False)
    voci = esegui(ctx.store.memories, f_prog, f_task, f_kind, q, superate) or []
    if not voci:
        st.info("Nessuna voce trovata.")
    for m in voci:
        with st.container(border=True):
            contesto = " · ".join(x for x in (progetti.get(m.get("project_id"), ""),
                                              f"task #{m['task_id']}" if m.get("task_id") else "") if x)
            st.markdown(f"**{ETICHETTE.get(m['kind'], m['kind'])}** <small>#{m['id']}"
                        f"{' · ' + contesto if contesto else ''}</small>", unsafe_allow_html=True)
            st.markdown(m["content"].replace("\n", "  \n"))
            st.caption(f"Fonte: {m['source']} · {fa(m['created_at'])} · {ctx.nome(m.get('created_by'))}"
                       + (f" · superata da #{m['superseded_by']}" if m.get("superseded_by") else ""))
