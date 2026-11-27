import streamlit as st

from guardian.ui.components import Ctx, esegui, fa


def non_lette(ctx: Ctx) -> int:
    return len(esegui(ctx.store.notifications, ctx.io["id"], True) or [])


def render(ctx: Ctx) -> None:
    lista = esegui(ctx.store.notifications, ctx.io["id"]) or []
    if any(n.get("read_at") is None for n in lista) and st.button("Segna tutte come lette"):
        esegui(ctx.store.mark_read, ctx.io["id"], ok="Fatto")
        st.rerun()
    if not lista:
        st.info("Nessuna notifica. Arrivano per: approvazioni da decidere, decisioni sulle tue richieste, "
                "task falliti, agenti in errore.")
    for n in lista:
        with st.container(border=True):
            c = st.columns([5, 1])
            nuova = n.get("read_at") is None
            c[0].markdown(f"{'🔵 ' if nuova else ''}**{n['kind'].replace('_', ' ')}** — {n['message']}")
            c[0].caption(fa(n["created_at"]) + (f" · {n['ref_table']} #{n['ref_id']}" if n.get("ref_id") else ""))
            if nuova and c[1].button("Letta", key=f"nr_{n['id']}"):
                esegui(ctx.store.mark_read, ctx.io["id"], n["id"])
                st.rerun()
