import streamlit as st

from guardian.ui.components import Ctx, esegui, riga_evento


def render(ctx: Ctx) -> None:
    _feed(ctx)


@st.fragment(run_every=20)
def _feed(ctx: Ctx) -> None:
    eventi = esegui(ctx.store.events, 150) or []
    tipi = sorted({e["event_type"] for e in eventi})
    c = st.columns(2)
    filtro_tipo = c[0].multiselect("Tipo", tipi)
    filtro_chi = c[1].multiselect("Collaboratore", list(ctx.nomi), format_func=ctx.nome)
    st.caption("Aggiornamento automatico ogni 20 secondi (polling, non push).")
    eventi = [e for e in eventi if (not filtro_tipo or e["event_type"] in filtro_tipo)
              and (not filtro_chi or e.get("user_id") in filtro_chi)]
    if not eventi:
        st.info("Nessuna attività da mostrare.")
    for e in eventi:
        riga_evento(ctx, e)
