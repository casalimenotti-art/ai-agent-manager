import streamlit as st

from guardian.core.models import PRIORITA, TASK_STATI, TASK_TERMINALI
from guardian.ui.components import GRUPPI_TASK, ICONE_STATO, Ctx, esegui, fa

STATI_INIZIALI = ("backlog", "planned", "ready")


def _opzioni(ctx: Ctx):
    progetti = {p["id"]: p["nome"] for p in (esegui(ctx.store.projects, True) or [])}
    agenti = {a["id"]: f"{a['nome']} ({ctx.nome(a['user_id'])})" for a in (esegui(ctx.store.agents) or [])}
    return progetti, agenti


def _idx(opz: list, val) -> int:
    return opz.index(val) if val in opz else 0


def _form_modifica(ctx: Ctx, t: dict, progetti: dict, agenti: dict, aperti: dict) -> None:
    with st.form(f"edit_{t['id']}"):
        c = st.columns(3)
        stato = c[0].selectbox("Stato", TASK_STATI, index=TASK_STATI.index(t["stato"]))
        prio = c[1].selectbox("Priorità", PRIORITA, index=PRIORITA.index(t["priorita"]))
        ids = [None, *ctx.nomi]
        resp = c[2].selectbox("Responsabile", ids, index=_idx(ids, t.get("responsabile")),
                              format_func=lambda x: ctx.nome(x) if x else "—")
        c = st.columns(2)
        pids, aids = [None, *progetti], [None, *agenti]
        prog = c[0].selectbox("Progetto", pids, index=_idx(pids, t.get("project_id")),
                              format_func=lambda x: progetti.get(x, "—"))
        ag = c[1].selectbox("Agente assegnato", aids, index=_idx(aids, t.get("assigned_agent_id")),
                            format_func=lambda x: agenti.get(x, "—"))
        dip_opz = sorted(set(aperti) | set(t.get("depends_on") or []) - {t["id"]})
        deps = st.multiselect("Dipende da", dip_opz, default=t.get("depends_on") or [],
                              format_func=lambda i: f"#{i} {aperti.get(i, '(chiuso)')}")
        nxt = st.text_input("Prossimo passo", t.get("next_step") or "")
        c = st.columns(2)
        result = c[0].text_area("Risultato", t.get("result") or "", height=70)
        error = c[1].text_area("Errore", t.get("error") or "", height=70)
        files = st.text_area("File modificati (uno per riga)", "\n".join(t.get("files_changed") or []), height=70)
        if st.form_submit_button("Salva"):
            if esegui(ctx.store.update_task, t["id"], by=ctx.io["id"], stato=stato, priorita=prio, responsabile=resp,
                      project_id=prog, assigned_agent_id=ag, depends_on=deps, next_step=nxt, result=result,
                      error=error, files_changed=files, ok="Task aggiornato"):
                st.rerun()


def _form_nuovo(ctx: Ctx, progetti: dict, agenti: dict, aperti: dict) -> None:
    with st.expander("➕ Nuovo task", expanded=False):
        with st.form("nuovo_task", clear_on_submit=True):
            titolo = st.text_input("Titolo *")
            descr = st.text_area("Descrizione", height=70)
            c = st.columns(3)
            prog = c[0].selectbox("Progetto", [None, *progetti], format_func=lambda x: progetti.get(x, "—"))
            resp = c[1].selectbox("Responsabile", [None, *ctx.nomi], format_func=lambda x: ctx.nome(x) if x else "—")
            ag = c[2].selectbox("Agente", [None, *agenti], format_func=lambda x: agenti.get(x, "—"))
            c = st.columns(2)
            prio = c[0].selectbox("Priorità", PRIORITA, index=1)
            stato = c[1].selectbox("Stato iniziale", STATI_INIZIALI)
            deps = st.multiselect("Dipende da", list(aperti), format_func=lambda i: f"#{i} {aperti[i]}")
            atteso = st.text_input("Risultato atteso")
            criteri = st.text_input("Criteri di completamento")
            nxt = st.text_input("Prossimo passo")
            if st.form_submit_button("Crea task", type="primary"):
                if esegui(ctx.store.create_task, titolo, descr, resp, "", prio, nxt, created_by=ctx.io["id"],
                          stato=stato, project_id=prog, depends_on=deps, assigned_agent_id=ag,
                          expected_result=atteso, completion_criteria=criteri, ok="Task creato"):
                    st.rerun()


def render(ctx: Ctx) -> None:
    progetti, agenti = _opzioni(ctx)
    tutti = esegui(ctx.store.tasks) or []
    aperti = {t["id"]: t["titolo"] for t in tutti if t["stato"] not in TASK_TERMINALI}
    _form_nuovo(ctx, progetti, agenti, aperti)
    filtro = st.selectbox("Progetto", [None, *progetti], format_func=lambda x: progetti.get(x, "Tutti i progetti"))
    tasks = [t for t in tutti if not filtro or t.get("project_id") == filtro]
    tabs = st.tabs([f"{g} ({sum(t['stato'] in stati for t in tasks)})" for g, stati in GRUPPI_TASK.items()])
    for tab, stati in zip(tabs, GRUPPI_TASK.values()):
        with tab:
            lista = [t for t in tasks if t["stato"] in stati]
            if not lista:
                st.caption("Nessun task.")
            for t in lista:
                titolo = (f"{ICONE_STATO[t['stato']]} #{t['id']} [{t['priorita']}] {t['titolo']} — "
                          f"{agenti.get(t.get('assigned_agent_id')) or ctx.nome(t.get('responsabile'))}")
                with st.expander(titolo):
                    if t.get("descrizione"):
                        st.write(t["descrizione"])
                    righe = [f"Stato: **{t['stato']}** · progetto: {progetti.get(t.get('project_id'), '—')} · "
                             f"aggiornato {fa(t['updated_at'])}"]
                    if t.get("depends_on"):
                        righe.append("Dipende da: " + ", ".join(f"#{d}" for d in t["depends_on"]))
                    for k, nome in (("expected_result", "Risultato atteso"), ("completion_criteria", "Criteri"),
                                    ("next_step", "Prossimo passo"), ("result", "Risultato"), ("error", "Errore")):
                        if t.get(k):
                            righe.append(f"{nome}: {t[k]}")
                    st.caption("  \n".join(righe))
                    _form_modifica(ctx, t, progetti, agenti, aperti)
