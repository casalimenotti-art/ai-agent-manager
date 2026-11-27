"""Guardian — NEXO AI Command Center (Streamlit). Solo accesso e navigazione: le pagine sono in guardian/ui/.

Avvio:  streamlit run guardian/app.py
- Con SUPABASE_URL e SUPABASE_ANON_KEY (st.secrets o variabili d'ambiente): dati condivisi + login.
- Senza: modalità locale su SQLite (GUARDIAN_DB, default ~/.guardian/hub.db), dati NON condivisi.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from guardian.core.store import crea_store_locale  # noqa: E402
from guardian.ui import (activity, agents, approvals, devices, handoff, logs, memory, notifications,  # noqa: E402
                         overview, projects, tasks)
from guardian.ui.components import CSS, Ctx, esegui, segreto  # noqa: E402

PAGINE = {"Overview": overview, "Agenti": agents, "Task": tasks, "Progetti": projects, "Attività": activity,
          "Log": logs, "Handoff": handoff, "Memoria": memory, "Approvazioni": approvals, "Notifiche": notifications,
          "Dispositivi": devices}

st.set_page_config(page_title="Guardian", page_icon="🛡️", layout="wide", initial_sidebar_state="auto")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def store_locale(path: str):
    return crea_store_locale(path)


def _login(url: str, key: str):
    from guardian.core.store_supabase import SupabaseStore
    st.title("🛡️ Guardian")
    st.caption("Accesso riservato ai collaboratori di NEXO.")
    with st.form("login"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        entra = st.form_submit_button("Entra", type="primary")
    if entra:
        s = SupabaseStore(url, key)
        try:
            s.login(email, pw)
            st.session_state["_store"] = s
            st.rerun()
        except PermissionError as e:
            st.error(str(e))
        except Exception:
            st.error("Email o password non validi.")
    st.stop()


def ottieni_store():
    url, key = segreto("SUPABASE_URL"), segreto("SUPABASE_ANON_KEY")
    if not (url and key):
        s = store_locale(os.environ.get("GUARDIAN_DB") or str(Path.home() / ".guardian" / "hub.db"))
        utenti = {u["id"]: u["nome"] for u in s.users()}
        with st.sidebar:
            st.warning("Modalità locale: dati su questo computer, NON condivisi. Configura Supabase per il team.")
            scelto = st.selectbox("Chi sei?", list(utenti) or ["locale"], format_func=lambda i: utenti.get(i, i))
        return s, {"id": scelto, "nome": utenti.get(scelto, scelto)}
    s = st.session_state.get("_store")
    if s is None or getattr(s, "user", None) is None:
        _login(url, key)
    return s, s.user


store, io = ottieni_store()
with st.sidebar:
    st.markdown(f"**{io['nome']}** · `{io['id']}`")
    if store.modalita == "supabase" and st.button("Esci"):
        store.logout()
        st.session_state.pop("_store", None)
        st.rerun()

ctx = Ctx(store=store, io=io, nomi={u["id"]: u["nome"] for u in (esegui(store.users) or [])})
st.markdown("## 🛡️ Guardian")
n_notifiche = notifications.non_lette(ctx)
pagina = st.segmented_control(
    "Sezione", list(PAGINE), default="Overview", label_visibility="collapsed", key="pagina",
    format_func=lambda p: f"Notifiche ({n_notifiche})" if p == "Notifiche" and n_notifiche else p) or "Overview"
PAGINE[pagina].render(ctx)
st.caption(f"Guardian · {store.modalita} · {datetime.now(timezone.utc):%H:%M} UTC")
