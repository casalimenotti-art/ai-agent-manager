import streamlit as st

from guardian.core.models import ACTION_TYPES, TASK_TERMINALI
from guardian.ui.components import Ctx, esegui, fa

ETICHETTE = {"email": "Invio email", "pubblicazione": "Pubblicazione", "contatto_cliente": "Contatto con clienti",
             "spesa": "Spesa", "pagamento": "Pagamento", "irreversibile": "Modifica irreversibile",
             "account_esterno": "Operazione su account esterno", "comando_pericoloso": "Comando potenzialmente pericoloso",
             "altro": "Altro"}


def _scheda(ctx: Ctx, a: dict, agenti: dict) -> None:
    with st.container(border=True):
        stato = {"richiesta": "waiting", "approvata": "ok", "rifiutata": "error"}[a["status"]]
        st.markdown(f"**{a['action']}** <span class='g-pill g-{stato}'>{a['status']}</span>", unsafe_allow_html=True)
        st.caption(f"{ETICHETTE.get(a.get('action_type'), a.get('action_type'))} · proposta da "
                   f"{agenti.get(a.get('agent_id')) or ctx.nome(a.get('requested_by'))} · {fa(a['created_at'])}"
                   + (f" · task #{a['task_id']}" if a.get("task_id") else ""))
        for k, nome in (("reason", "Motivo"), ("impact", "Impatto previsto"), ("data_involved", "Dati coinvolti"),
                        ("description", "Dettagli")):
            if a.get(k):
                st.markdown(f"**{nome}:** {a[k]}")
        if a.get("decided_by"):
            st.caption(f"Deciso da {ctx.nome(a['decided_by'])} · {fa(a.get('decided_at'))}")
        if a["status"] == "richiesta":
            c = st.columns(2)
            if c[0].button("✅ Approva", key=f"ok_{a['id']}", type="primary", use_container_width=True):
                esegui(ctx.store.decide_approval, a["id"], "approvata", ctx.io["id"], ok="Approvata")
                st.rerun()
            if c[1].button("❌ Rifiuta", key=f"no_{a['id']}", use_container_width=True):
                esegui(ctx.store.decide_approval, a["id"], "rifiutata", ctx.io["id"], ok="Rifiutata")
                st.rerun()


def render(ctx: Ctx) -> None:
    st.caption("Azioni esterne o irreversibili restano ferme finché una persona le approva. Guardian registra solo la "
               "decisione e non esegue l'azione. Un task con un'approvazione aperta resta in «needs_approval».")
    tasks = {t["id"]: t["titolo"] for t in (esegui(ctx.store.tasks) or []) if t["stato"] not in TASK_TERMINALI}
    agenti = {a["id"]: a["nome"] for a in (esegui(ctx.store.agents) or [])}
    with st.expander("➕ Richiedi approvazione"):
        with st.form("appr", clear_on_submit=True):
            azione = st.text_input("Azione proposta *", placeholder="Es. Inviare il preventivo via email a Ottica X")
            c = st.columns(2)
            tipo = c[0].selectbox("Tipo", ACTION_TYPES, format_func=ETICHETTE.get)
            ag = c[1].selectbox("Agente che la propone", [None, *agenti], format_func=lambda x: agenti.get(x, "— (persona)"))
            motivo = st.text_input("Motivo")
            impatto = st.text_input("Impatto previsto")
            dati = st.text_input("Dati coinvolti", help="Descrivi i dati, non incollarli (niente password o dati personali)")
            tid = st.selectbox("Task collegato", [None, *tasks], format_func=lambda i: "— nessuno —" if i is None else f"#{i} {tasks[i]}")
            descr = st.text_area("Altri dettagli", height=60)
            if st.form_submit_button("Invia richiesta", type="primary"):
                if esegui(ctx.store.request_approval, azione, descr, tid, ctx.io["id"], action_type=tipo, reason=motivo,
                          impact=impatto, data_involved=dati, agent_id=ag, ok="Richiesta registrata"):
                    st.rerun()
    tutte = esegui(ctx.store.approvals) or []
    da_decidere = [a for a in tutte if a["status"] == "richiesta"]
    st.subheader(f"Da decidere ({len(da_decidere)})")
    if not da_decidere:
        st.caption("Nessuna richiesta in attesa.")
    for a in da_decidere:
        _scheda(ctx, a, agenti)
    storico = [a for a in tutte if a["status"] != "richiesta"]
    if storico:
        with st.expander(f"Storico ({len(storico)})"):
            for a in storico:
                _scheda(ctx, a, agenti)
