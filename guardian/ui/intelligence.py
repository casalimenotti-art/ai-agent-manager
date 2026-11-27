"""Guardian Intelligence: obiettivo → piano proposto → conferma umana; report e prossime azioni sempre disponibili."""
import streamlit as st

from guardian.core.models import ValidazioneError
from guardian.planner.planner import PlannerNonDisponibile, make_plan
from guardian.planner.report import report
from guardian.providers.base import ProviderErrore
from guardian.ui.components import Ctx, esegui, fa


def _router(ctx: Ctx):
    from guardian.providers.router import router_da_config

    def traccia(c):  # solo metadati della chiamata, mai prompt né risposta
        ctx.store.add_event("provider_call", f"{c.provider}/{c.model}: {c.esito} in {c.ms} ms"
                            + (f" ({c.dettaglio})" if c.dettaglio else ""), user_id=ctx.io["id"],
                            severity="warning" if c.esito != "ok" else "info")
    return router_da_config(on_call=traccia)


def _prossime_azioni(ctx: Ctx) -> None:
    st.subheader("Prossime azioni")
    r = esegui(report, ctx.store)
    if not r:
        return
    c = r["conteggi"]
    st.caption(f"Calcolate dai dati reali (nessun modello AI). Task aperti {r['aperti']} · in esecuzione {c['running']} · "
               f"bloccati {c['blocked']} · falliti {c['failed']} · approvazioni {r['approvazioni']}")
    if not r["prossime_azioni"]:
        st.success("Nessuna azione urgente.")
    icone = {1: "🔴", 2: "🟠", 3: "🔵"}
    for a in r["prossime_azioni"][:15]:
        st.markdown(f"{icone.get(a['priorita'], '•')} {a['testo']}")


def _anteprima(ctx: Ctx, p: dict, agenti: dict) -> None:
    piano = p["piano"]
    with st.container(border=True):
        st.markdown(f"**Piano #{p['id']}** — {p['goal']}")
        st.caption(f"Proposto {fa(p['created_at'])} da {p.get('provider') or '?'} / {p.get('model') or '?'}")
        if piano.get("summary"):
            st.write(piano["summary"])
        righe = []
        for i, t in enumerate(piano.get("tasks", [])):
            righe.append({"#": i, "task": t["title"], "priorità": t["priority"],
                          "dipende da": ", ".join(str(d) for d in t.get("depends_on", [])) or "—",
                          "agente": agenti.get(t.get("agent"), t.get("agent") or "—"),
                          "approvazione": t["action_type"] if t.get("requires_approval") else "—",
                          "criteri": t.get("completion_criteria") or ""})
        st.dataframe(righe, hide_index=True, use_container_width=True)
        for titolo, k in (("Assunzioni", "assumptions"), ("Integrazioni mancanti", "missing")):
            if piano.get(k):
                st.caption(f"{titolo}: " + "; ".join(piano[k]))
        c = st.columns(2)
        if c[0].button("✅ Conferma e crea i task", key=f"conf_{p['id']}", type="primary", use_container_width=True):
            from guardian.core.store import conferma_piano
            ids = esegui(conferma_piano, ctx.store, p["id"], ctx.io["id"])
            if ids:
                st.toast(f"Creati {len(ids)} task")
                st.rerun()
        if c[1].button("Scarta", key=f"scarta_{p['id']}", use_container_width=True):
            esegui(ctx.store.set_plan_state, p["id"], "scartato", ctx.io["id"], ok="Piano scartato")
            st.rerun()


def render(ctx: Ctx) -> None:
    router = _router(ctx)
    agents = esegui(ctx.store.agents) or []
    agenti = {a["id"]: a["nome"] for a in agents}
    progetti = {p["id"]: p["nome"] for p in (esegui(ctx.store.projects, True) or [])}
    utilizzabili = router.utilizzabili()
    st.subheader("Pianifica un obiettivo")
    if not utilizzabili:
        st.info("Planner AI non disponibile: nessun provider configurato e consentito. Guardian non genera piani finti. "
                "Per attivarlo aggiungi un provider OpenAI-compatibile nei Secrets (vedi .streamlit/secrets.toml.example). "
                "Intanto puoi creare i task a mano nella sezione Task.")
    with st.form("obiettivo", clear_on_submit=False):
        goal = st.text_area("Obiettivo", placeholder="Es. Preparare l'offerta per i 30 clienti di Cagliari entro venerdì")
        contesto = st.text_area("Contesto e vincoli", height=70)
        prog = st.selectbox("Progetto", [None, *progetti], format_func=lambda x: progetti.get(x, "—"))
        invia = st.form_submit_button("Proponi un piano", type="primary", disabled=not utilizzabili)
    if invia:
        with st.spinner("Guardian sta preparando il piano…"):
            try:
                piano, prov, model = make_plan(goal, contesto, agents, [{"nome": n} for n in progetti.values()], router,
                                               esegui(ctx.store.tasks) or [])
                esegui(ctx.store.create_plan, goal, piano.to_dict(), prog, prov, model, ctx.io["id"],
                       ok="Piano proposto: controllalo e confermalo")
            except PlannerNonDisponibile as e:
                st.warning(str(e))
            except (ProviderErrore, ValidazioneError) as e:
                st.error(f"Il piano non è utilizzabile: {e}")
    for p in esegui(ctx.store.plans, "bozza") or []:
        _anteprima(ctx, p, agenti)
    _prossime_azioni(ctx)
    with st.expander("Provider AI"):
        stato = router.stato()
        if not stato:
            st.caption("Nessun provider configurato.")
        for s in stato:
            st.markdown(f"- **{s['nome']}** · {s['model']} · {s['costo']} · "
                        + ("utilizzabile" if s["utilizzabile"] else f"non utilizzabile: {s['motivo']}"))
        st.caption("I modelli via API non usano gli abbonamenti personali di Claude Code o Codex.")
