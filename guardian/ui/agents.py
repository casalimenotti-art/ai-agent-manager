import streamlit as st

from guardian.core.adapters import ADAPTERS_PREVISTI
from guardian.core.models import stato_dispositivo
from guardian.ui.components import Ctx, esegui, fa, pill


def render(ctx: Ctx) -> None:
    devices = esegui(ctx.store.devices) or []
    tasks = {t["id"]: t for t in (esegui(ctx.store.tasks) or [])}
    if not devices:
        st.info("Nessun PC collegato. Registra un dispositivo in «Dispositivi» e avvia il Guardian Bridge: "
                "senza bridge lo stato degli agenti non è disponibile.")
    cols = st.columns(3)
    for i, d in enumerate(devices):
        s = stato_dispositivo(d)
        with cols[i % 3].container(border=True):
            st.markdown(f"**{d.get('agent_name') or 'agente non indicato'}** {pill(s)}", unsafe_allow_html=True)
            st.caption(f"{ctx.nome(d['user_id'])} · {d['nome']} · {d.get('model') or 'modello non indicato'}")
            t = tasks.get(d.get("current_task_id"))
            st.write(f"Task: #{t['id']} {t['titolo']}" if t else "Task: nessuno")
            st.caption(f"Ultimo aggiornamento: {fa(d.get('last_seen'))} · ultimo checkpoint: {fa(d.get('last_checkpoint'))}")
            if d.get("limit_reached"):
                st.warning("Limite di utilizzo raggiunto: salvare un handoff e passare il task.")
            if d.get("error"):
                st.error(d["error"])
    with st.expander("Integrazioni agenti"):
        st.markdown("- **Attive:** bridge (heartbeat, eventi, checkpoint), file di stato locale, registro git.")
        for a in ADAPTERS_PREVISTI:
            st.markdown(f"- {a.nome}: _non collegato_ — {a.motivo}")
