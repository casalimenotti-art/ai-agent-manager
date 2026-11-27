import streamlit as st

from guardian.ui.components import Ctx, esegui, fa


def render(ctx: Ctx) -> None:
    st.caption("Le azioni esterne (email, pubblicazioni, pagamenti, cancellazioni) si registrano qui e restano "
               "ferme finché una persona le approva. Guardian non esegue l'azione: registra solo la decisione.")
    tasks = esegui(ctx.store.tasks) or []
    with st.expander("➕ Richiedi approvazione"):
        with st.form("appr", clear_on_submit=True):
            azione = st.text_input("Azione (es. Inviare email di preventivo a cliente X)")
            descr = st.text_area("Dettagli", height=70)
            tid = st.selectbox("Task collegato", [None] + [t["id"] for t in tasks],
                               format_func=lambda i: "— nessuno —" if i is None else f"#{i}")
            if st.form_submit_button("Invia richiesta"):
                if esegui(ctx.store.request_approval, azione, descr, tid, ctx.io["id"], ok="Richiesta registrata"):
                    st.rerun()
    lista = esegui(ctx.store.approvals) or []
    if not lista:
        st.info("Nessuna richiesta.")
    for a in lista:
        with st.container(border=True):
            st.markdown(f"**{a['action']}** · {a['status']}")
            st.caption(f"da {ctx.nome(a.get('requested_by'))} · {fa(a['created_at'])}"
                       f"{' · task #' + str(a['task_id']) if a.get('task_id') else ''}"
                       f"{' · deciso da ' + ctx.nome(a['decided_by']) if a.get('decided_by') else ''}")
            if a.get("description"):
                st.write(a["description"])
            if a["status"] == "richiesta":
                c = st.columns(2)
                if c[0].button("Approva", key=f"ok_{a['id']}", type="primary"):
                    esegui(ctx.store.decide_approval, a["id"], "approvata", ctx.io["id"], ok="Approvata")
                    st.rerun()
                if c[1].button("Rifiuta", key=f"no_{a['id']}"):
                    esegui(ctx.store.decide_approval, a["id"], "rifiutata", ctx.io["id"], ok="Rifiutata")
                    st.rerun()
