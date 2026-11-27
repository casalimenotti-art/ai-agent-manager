"""Log degli agenti: solo ciò che arriva dagli hook/notify tramite il bridge (metadati + richieste troncate)."""
from datetime import date, datetime, time, timedelta, timezone

import streamlit as st

from guardian.ui.components import Ctx, esegui, fa

LIVELLI = ("debug", "info", "warning", "error")


def render(ctx: Ctx) -> None:
    agenti = {a["id"]: a["nome"] for a in (esegui(ctx.store.agents) or [])}
    pcs = {d["id"]: d["nome"] for d in (esegui(ctx.store.devices) or [])}
    progetti = {p["id"]: p["nome"] for p in (esegui(ctx.store.projects) or [])}
    c = st.columns(3)
    ag = c[0].selectbox("Agente", [None, *agenti], format_func=lambda x: agenti.get(x, "Tutti"))
    pc = c[1].selectbox("Computer", [None, *pcs], format_func=lambda x: pcs.get(x, "Tutti"))
    pr = c[2].selectbox("Progetto", [None, *progetti], format_func=lambda x: progetti.get(x, "Tutti"))
    c = st.columns(3)
    lv = c[0].selectbox("Livello", [None, *LIVELLI], format_func=lambda x: x or "Tutti")
    task = c[1].number_input("Task #", min_value=0, step=1, value=0, help="0 = tutti")
    oggi = date.today()
    periodo = c[2].date_input("Periodo", (oggi - timedelta(days=7), oggi))
    dal = al = None
    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        dal = datetime.combine(periodo[0], time.min, timezone.utc).isoformat()
        al = datetime.combine(periodo[1], time.max, timezone.utc).isoformat()
    logs = esegui(ctx.store.agent_logs, agent_id=ag, device_id=pc, project_id=pr, task_id=int(task) or None,
                  level=lv, dal=dal, al=al, limit=300) or []
    st.caption("Fonte: hook di Claude Code / notify di Codex tramite il bridge. Mai l'output degli strumenti; "
               "le richieste sono troncate a 200 caratteri e ripulite dai segreti riconosciuti.")
    if not logs:
        st.info("Nessun log nel periodo scelto. I log arrivano solo dai PC con il bridge e gli hook attivi.")
        return
    st.dataframe([{"quando": fa(r["ts"]), "agente": agenti.get(r.get("agent_id"), r.get("agent_id")),
                   "PC": pcs.get(r.get("device_id"), ""), "livello": r["level"], "fonte": r["source"],
                   "task": r.get("task_id") or "", "messaggio": r["message"]} for r in logs],
                 hide_index=True, use_container_width=True)
