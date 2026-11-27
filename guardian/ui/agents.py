import streamlit as st

from guardian.core.models import stato_agente, stato_dispositivo
from guardian.ui.components import Ctx, esegui, fa, pill

FONTI = {"claude-code": "hook di Claude Code", "codex": "notify di Codex (da verificare)", "api": "provider API",
         "manuale": "aggiornamenti manuali"}


def _usage(u: dict | None) -> str:
    if not u:
        return ""
    nomi = {"five_hour": "5 ore", "seven_day": "7 giorni"}
    return " · ".join(f"{nomi.get(k, k)} {v['pct']:.0f}%" for k, v in u.items() if isinstance(v, dict) and "pct" in v)


def render(ctx: Ctx) -> None:
    agenti = esegui(ctx.store.agents) or []
    devices = {d["id"]: d for d in (esegui(ctx.store.devices) or [])}
    tasks = {t["id"]: t for t in (esegui(ctx.store.tasks) or [])}
    st.caption("Lo stato di un agente arriva solo da eventi reali (hook/notify) inviati dal Guardian Bridge. "
               "Un PC acceso non rende «online» il suo agente: senza eventi recenti lo stato è «unknown».")
    if not agenti:
        st.info("Nessun agente registrato. Sul PC: configura GUARDIAN_CLAUDE_AGENT_ID / GUARDIAN_CODEX_AGENT_ID in "
                "bridge/.env e avvia `python bridge/guardian_bridge.py run` (guida: docs/guardian-setup.md).")
    cols = st.columns(3)
    for i, a in enumerate(agenti):
        s = stato_agente(a)
        d = devices.get(a.get("device_id"))
        with cols[i % 3].container(border=True):
            st.markdown(f"**{a['nome']}** {pill(s)}", unsafe_allow_html=True)
            pc = f"{d['nome']} ({stato_dispositivo(d)})" if d else "PC non indicato"
            st.caption(f"`{a['id']}` · {ctx.nome(a['user_id'])} · {pc}")
            t = tasks.get(a.get("current_task_id"))
            st.write(f"Task: #{t['id']} {t['titolo']}" if t else "Task: nessuno")
            st.caption(f"Ultimo segnale: {fa(a.get('last_heartbeat'))} · ultima attività: {fa(a.get('last_activity'))}"
                       + ("" if a.get("disponibile", True) else " · non disponibile"))
            if a.get("capabilities"):
                st.caption("Capacità: " + ", ".join(a["capabilities"]))
            if _usage(a.get("usage")):
                st.caption("Utilizzo: " + _usage(a.get("usage")))
            if a.get("error"):
                st.error(a["error"])
            st.caption(f"Fonte dello stato: {FONTI.get(a['tipo'], a['tipo'])}")
