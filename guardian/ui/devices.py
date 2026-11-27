import streamlit as st

from guardian.core.models import stato_dispositivo
from guardian.ui.components import Ctx, esegui, fa, pill


def render(ctx: Ctx) -> None:
    nuovo = st.session_state.pop("_token_nuovo", None)
    if nuovo:
        st.success("Dispositivo registrato. Copia ora il token: non verrà più mostrato.")
        st.code(nuovo, language=None)
        st.caption("Sul PC: mettilo in bridge/.env come GUARDIAN_DEVICE_TOKEN=… (file escluso da git).")
    ids = list(ctx.nomi) or [ctx.io["id"]]
    with st.expander("➕ Registra un PC"):
        with st.form("dev", clear_on_submit=True):
            uid = st.selectbox("Collaboratore", ids, format_func=ctx.nome,
                               index=ids.index(ctx.io["id"]) if ctx.io["id"] in ids else 0)
            nome_pc = st.text_input("Nome del PC (es. PC-Menotti)")
            agente = st.text_input("Agente principale (es. Claude Code)")
            if st.form_submit_button("Registra"):
                r = esegui(ctx.store.register_device, uid, nome_pc, agente)
                if r:
                    st.session_state["_token_nuovo"] = r[1]
                    st.rerun()
    devices = esegui(ctx.store.devices) or []
    if not devices:
        st.info("Nessun PC registrato.")
    for d in devices:
        with st.container(border=True):
            c = st.columns([4, 1])
            c[0].markdown(f"**{d['nome']}** · {ctx.nome(d['user_id'])} {pill(stato_dispositivo(d))}",
                          unsafe_allow_html=True)
            c[0].caption(f"Ultimo heartbeat: {fa(d.get('last_seen'))} · agente: {d.get('agent_name') or '—'}")
            if c[1].button("Revoca token", key=f"rev_{d['id']}", help="Il bridge di questo PC smette di funzionare"):
                esegui(ctx.store.revoke_device, d["id"], ok="Token revocato")
                st.rerun()
