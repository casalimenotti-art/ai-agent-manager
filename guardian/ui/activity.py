import streamlit as st

from guardian.core.models import SEVERITA
from guardian.ui.components import Ctx, esegui, riga_evento
from guardian.ui.status import POLLING_SECONDI


def render(ctx: Ctx) -> None:
    _feed(ctx)


@st.fragment(run_every=POLLING_SECONDI)
def _feed(ctx: Ctx) -> None:
    eventi = esegui(ctx.store.events, 300) or []
    agenti = sorted({e.get("agent_id") or e.get("agent_name") for e in eventi} - {None, ""})
    c = st.columns(4)
    f_tipo = c[0].multiselect("Tipo", sorted({e["event_type"] for e in eventi}))
    f_sev = c[1].multiselect("Gravità", SEVERITA)
    f_chi = c[2].multiselect("Collaboratore", list(ctx.nomi), format_func=ctx.nome)
    f_ag = c[3].multiselect("Agente", agenti)
    f_task = st.text_input("Task # (opzionale)", "")
    st.caption(f"Aggiornamento automatico ogni {POLLING_SECONDI} secondi (polling, non push). Ultimi 300 eventi.")
    eventi = [e for e in eventi
              if (not f_tipo or e["event_type"] in f_tipo) and (not f_sev or e.get("severity", "info") in f_sev)
              and (not f_chi or e.get("user_id") in f_chi)
              and (not f_ag or (e.get("agent_id") or e.get("agent_name")) in f_ag)
              and (not f_task.strip().lstrip("#").isdigit() or e.get("task_id") == int(f_task.strip().lstrip("#")))]
    if not eventi:
        st.info("Nessuna attività da mostrare.")
    for e in eventi:
        riga_evento(ctx, e)
