"""Guardian Hub — dashboard condivisa di Nexo (Streamlit).

Avvio:  streamlit run guardian_hub/app.py
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
from guardian_hub.adapters import ADAPTERS_PREVISTI  # noqa: E402
from guardian_hub.models import (PRIORITA, TASK_STATI, Handoff, ValidazioneError, eta_secondi,  # noqa: E402
                                 stato_dispositivo)
from guardian_hub.store import SqliteStore, SupabaseStore, seed_users_da_registro  # noqa: E402

st.set_page_config(page_title="Guardian Hub", page_icon="🛡️", layout="wide", initial_sidebar_state="auto")
st.markdown("""<style>
.block-container{padding-top:1.2rem;max-width:1300px}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.25);border-radius:12px;padding:.6rem .8rem}
.g-pill{display:inline-block;padding:.05rem .55rem;border-radius:999px;font-size:.8rem;font-weight:600}
.g-online{background:#1f9d5533;color:#1f9d55}.g-offline{background:#8884;color:inherit;opacity:.8}
.g-occupato{background:#2b7de933;color:#2b7de9}.g-limite,.g-errore{background:#d9480f33;color:#d9480f}
</style>""", unsafe_allow_html=True)

ICONE_STATO = {"in attesa": "⏳", "in corso": "🔄", "bloccato": "⛔", "completato": "✅"}


def segreto(nome: str) -> str:
    try:
        v = st.secrets.get(nome)
        if v:
            return str(v)
    except Exception:
        pass
    return os.environ.get(nome, "")


@st.cache_resource
def store_locale(path: str) -> SqliteStore:
    s = SqliteStore(path)
    seed_users_da_registro(s)
    return s


def fa(ts) -> str:
    sec = eta_secondi(ts)
    if sec is None:
        return "mai"
    if sec < 90:
        return "ora"
    if sec < 3600:
        return f"{int(sec // 60)} min fa"
    if sec < 86400:
        return f"{int(sec // 3600)} h fa"
    return str(ts)[:10]


def pill(stato: str) -> str:
    return f'<span class="g-pill g-{stato}">{stato}</span>'


def esegui(fn, *a, ok: str | None = None, **kw):
    """Esegue un'operazione sull'archivio mostrando errori leggibili, mai dettagli interni o segreti."""
    try:
        r = fn(*a, **kw)
        if ok:
            st.toast(ok)
        return r
    except (ValidazioneError, PermissionError) as e:
        st.error(str(e))
    except Exception as e:  # errori di rete/DB
        st.error(f"Operazione non riuscita ({type(e).__name__}). Riprova o controlla la connessione.")
    return None


# ------------------------------------------------------------------ accesso
def ottieni_store():
    url, key = segreto("SUPABASE_URL"), segreto("SUPABASE_ANON_KEY")
    if not (url and key):
        s = store_locale(os.environ.get("GUARDIAN_DB") or str(Path.home() / ".guardian" / "hub.db"))
        utenti = s.users()
        with st.sidebar:
            st.warning("Modalità locale: dati su questo computer, NON condivisi. Configura Supabase per il team.")
            ids = [u["id"] for u in utenti] or ["locale"]
            scelto = st.selectbox("Chi sei?", ids, format_func=lambda i: next((u["nome"] for u in utenti if u["id"] == i), i))
        return s, {"id": scelto, "nome": next((u["nome"] for u in utenti if u["id"] == scelto), scelto)}
    s = st.session_state.get("_store")
    if s is None or getattr(s, "user", None) is None:
        st.title("🛡️ Guardian Hub")
        st.caption("Accesso riservato ai collaboratori di Nexo.")
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
    return s, s.user


store, io = ottieni_store()
with st.sidebar:
    st.markdown(f"**{io['nome']}** · `{io['id']}`")
    if store.modalita == "supabase" and st.button("Esci"):
        store.logout()
        st.session_state.pop("_store", None)
        st.rerun()

utenti = esegui(store.users) or []
NOMI = {u["id"]: u["nome"] for u in utenti}


def nome(uid) -> str:
    return NOMI.get(uid, uid or "—")


st.markdown("## 🛡️ Guardian Hub")
PAGINE = ["Overview", "Agenti", "Task", "Attività", "Handoff", "Approvazioni", "Dispositivi"]
pagina = st.segmented_control("Sezione", PAGINE, default="Overview", label_visibility="collapsed",
                              key="pagina") or "Overview"


def riga_evento(e: dict) -> None:
    chi = " · ".join(x for x in (nome(e.get("user_id")) if e.get("user_id") else "", e.get("agent_name") or "") if x)
    task = f" · task #{e['task_id']}" if e.get("task_id") else ""
    st.markdown(f"**{e['event_type']}** — {e['message']}  \n"
                f"<small>{fa(e['timestamp'])} · {chi or 'sistema'}{task}"
                f"{' · ' + ', '.join(e['files'][:5]) if e.get('files') else ''}</small>", unsafe_allow_html=True)


# ------------------------------------------------------------------ pagine
def pagina_overview():
    devices = esegui(store.devices) or []
    tasks = esegui(store.tasks) or []
    stati_dev = [stato_dispositivo(d) for d in devices]
    online = sum(s != "offline" for s in stati_dev)
    attivi = sum(1 for d, s in zip(devices, stati_dev) if s in ("online", "occupato") and d.get("agent_name"))
    conta = {s: sum(t["stato"] == s for t in tasks) for s in TASK_STATI}
    errori = sum(s in ("errore", "limite") for s in stati_dev)
    attese = len(esegui(store.approvals, "richiesta") or [])
    c = st.columns(4)
    c[0].metric("PC online", f"{online}/{len(devices)}")
    c[1].metric("Agenti attivi", attivi)
    c[2].metric("Task in corso", conta["in corso"])
    c[3].metric("Task completati", conta["completato"])
    c = st.columns(4)
    c[0].metric("In attesa", conta["in attesa"])
    c[1].metric("Bloccati", conta["bloccato"])
    c[2].metric("Errori / limiti", errori)
    c[3].metric("Approvazioni da decidere", attese)
    st.subheader("Collaboratori")
    cols = st.columns(max(1, len(utenti)))
    for col, u in zip(cols, utenti):
        suoi = [(d, s) for d, s in zip(devices, stati_dev) if d["user_id"] == u["id"]]
        stato = "online" if any(s != "offline" for _, s in suoi) else "offline"
        with col.container(border=True):
            st.markdown(f"**{u['nome']}** {pill(stato)}", unsafe_allow_html=True)
            st.caption(f"{u.get('agente') or '—'} · {u.get('ruolo') or ''}")
            st.caption(f"{len(suoi)} PC registrati" if suoi else "Nessun PC collegato: stato non disponibile")
    st.subheader("Attività recenti")
    eventi = esegui(store.events, 10) or []
    if not eventi:
        st.info("Nessuna attività registrata. Gli eventi arrivano dal bridge o dal registro (sync-registro).")
    for e in eventi:
        riga_evento(e)


def pagina_agenti():
    devices = esegui(store.devices) or []
    tasks = {t["id"]: t for t in (esegui(store.tasks) or [])}
    if not devices:
        st.info("Nessun PC collegato. Registra un dispositivo in «Dispositivi» e avvia il Guardian Bridge: "
                "senza bridge lo stato degli agenti non è disponibile.")
    cols = st.columns(3)
    for i, d in enumerate(devices):
        s = stato_dispositivo(d)
        with cols[i % 3].container(border=True):
            st.markdown(f"**{d.get('agent_name') or 'agente non indicato'}** {pill(s)}", unsafe_allow_html=True)
            st.caption(f"{nome(d['user_id'])} · {d['nome']} · {d.get('model') or 'modello non indicato'}")
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


def form_task_modifica(t: dict):
    with st.form(f"edit_{t['id']}"):
        c = st.columns(3)
        stato = c[0].selectbox("Stato", TASK_STATI, index=TASK_STATI.index(t["stato"]))
        prio = c[1].selectbox("Priorità", PRIORITA, index=PRIORITA.index(t["priorita"]))
        ids = [""] + list(NOMI)
        resp = c[2].selectbox("Responsabile", ids, index=ids.index(t["responsabile"]) if t.get("responsabile") in ids else 0,
                              format_func=lambda x: nome(x) if x else "—")
        agente = st.text_input("Agente", t.get("agente") or "")
        nxt = st.text_input("Prossimo passo", t.get("next_step") or "")
        files = st.text_area("File modificati (uno per riga)", "\n".join(t.get("files_changed") or []), height=80)
        if st.form_submit_button("Salva"):
            esegui(store.update_task, t["id"], by=io["id"], stato=stato, priorita=prio, responsabile=resp or None,
                   agente=agente, next_step=nxt, files_changed=files, ok="Task aggiornato")
            st.rerun()


def pagina_task():
    with st.expander("➕ Nuovo task", expanded=False):
        with st.form("nuovo_task", clear_on_submit=True):
            titolo = st.text_input("Titolo")
            descr = st.text_area("Descrizione", height=80)
            c = st.columns(3)
            resp = c[0].selectbox("Responsabile", [""] + list(NOMI), format_func=lambda x: nome(x) if x else "—")
            agente = c[1].text_input("Agente (es. Claude Code, Codex)")
            prio = c[2].selectbox("Priorità", PRIORITA, index=1)
            nxt = st.text_input("Prossimo passo")
            if st.form_submit_button("Crea task", type="primary"):
                if esegui(store.create_task, titolo, descr, resp or None, agente, prio, nxt, created_by=io["id"],
                          ok="Task creato"):
                    st.rerun()
    tasks = esegui(store.tasks) or []
    tabs = st.tabs([f"{ICONE_STATO[s]} {s} ({sum(t['stato'] == s for t in tasks)})" for s in TASK_STATI])
    for tab, s in zip(tabs, TASK_STATI):
        with tab:
            lista = [t for t in tasks if t["stato"] == s]
            if not lista:
                st.caption("Nessun task.")
            for t in lista:
                with st.expander(f"#{t['id']} [{t['priorita']}] {t['titolo']} — {nome(t.get('responsabile'))}"):
                    if t.get("descrizione"):
                        st.write(t["descrizione"])
                    st.caption(f"Agente: {t.get('agente') or '—'} · aggiornato {fa(t['updated_at'])} · "
                               f"prossimo passo: {t.get('next_step') or '—'}")
                    form_task_modifica(t)


@st.fragment(run_every=20)
def pagina_attivita():
    eventi = esegui(store.events, 150) or []
    tipi = sorted({e["event_type"] for e in eventi})
    c = st.columns(2)
    filtro_tipo = c[0].multiselect("Tipo", tipi)
    filtro_chi = c[1].multiselect("Collaboratore", list(NOMI), format_func=nome)
    st.caption("Aggiornamento automatico ogni 20 secondi.")
    eventi = [e for e in eventi if (not filtro_tipo or e["event_type"] in filtro_tipo)
              and (not filtro_chi or e.get("user_id") in filtro_chi)]
    if not eventi:
        st.info("Nessuna attività da mostrare.")
    for e in eventi:
        riga_evento(e)


def pagina_handoff():
    tasks = esegui(store.tasks) or []
    with st.expander("💾 Salva handoff / checkpoint", expanded=False):
        with st.form("handoff", clear_on_submit=True):
            opz = [None] + [t["id"] for t in tasks]
            tid = st.selectbox("Task", opz, format_func=lambda i: "— nessuno —" if i is None else
                               f"#{i} {next(t['titolo'] for t in tasks if t['id'] == i)}")
            agente = st.text_input("Agente", "")
            summary = st.text_area("Obiettivo e stato attuale *", height=90)
            done = st.text_area("Lavoro completato", height=70)
            dec = st.text_area("Decisioni prese", height=60)
            err = st.text_area("Problemi incontrati", height=60)
            tests = st.text_area("Test eseguiti", height=60)
            files = st.text_area("File modificati (uno per riga)", height=60)
            nxt = st.text_input("Prossimo passo preciso *")
            if st.form_submit_button("Salva handoff", type="primary"):
                h = Handoff(agent_name=agente or io["nome"], summary=summary, next_step=nxt, task_id=tid,
                            completed_steps=done, decisions=dec, errors=err, tests=tests,
                            files_changed=files.splitlines())
                if esegui(store.add_handoff, h, user_id=io["id"], ok="Handoff salvato"):
                    st.rerun()
    lista = esegui(store.handoffs) or []
    if not lista:
        st.info("Nessun handoff salvato.")
    for r in lista:
        h = Handoff(agent_name=r["agent_name"], summary=r["summary"], next_step=r["next_step"], task_id=r.get("task_id"),
                    completed_steps=r.get("completed_steps") or "", files_changed=r.get("files_changed") or [],
                    decisions=r.get("decisions") or "", errors=r.get("errors") or "", tests=r.get("tests") or "",
                    timestamp=str(r["timestamp"]))
        with st.expander(f"{fa(r['timestamp'])} · {r['agent_name']}"
                         f"{' · task #' + str(r['task_id']) if r.get('task_id') else ''} → {r['next_step'][:80]}"):
            st.markdown(h.markdown())
            st.download_button("Scarica .md", h.markdown(), file_name=f"handoff-{r['id']}.md", key=f"dl_{r['id']}")


def pagina_approvazioni():
    st.caption("Le azioni esterne (email, pubblicazioni, pagamenti, cancellazioni) si registrano qui e restano "
               "ferme finché una persona le approva. Guardian non esegue l'azione: registra solo la decisione.")
    tasks = esegui(store.tasks) or []
    with st.expander("➕ Richiedi approvazione"):
        with st.form("appr", clear_on_submit=True):
            azione = st.text_input("Azione (es. Inviare email di preventivo a cliente X)")
            descr = st.text_area("Dettagli", height=70)
            opz = [None] + [t["id"] for t in tasks]
            tid = st.selectbox("Task collegato", opz, format_func=lambda i: "— nessuno —" if i is None else f"#{i}")
            if st.form_submit_button("Invia richiesta"):
                if esegui(store.request_approval, azione, descr, tid, io["id"], ok="Richiesta registrata"):
                    st.rerun()
    lista = esegui(store.approvals) or []
    if not lista:
        st.info("Nessuna richiesta.")
    for a in lista:
        with st.container(border=True):
            st.markdown(f"**{a['action']}** · {a['status']}")
            st.caption(f"da {nome(a.get('requested_by'))} · {fa(a['created_at'])}"
                       f"{' · task #' + str(a['task_id']) if a.get('task_id') else ''}"
                       f"{' · deciso da ' + nome(a['decided_by']) if a.get('decided_by') else ''}")
            if a.get("description"):
                st.write(a["description"])
            if a["status"] == "richiesta":
                c = st.columns(2)
                if c[0].button("Approva", key=f"ok_{a['id']}", type="primary"):
                    esegui(store.decide_approval, a["id"], "approvata", io["id"], ok="Approvata")
                    st.rerun()
                if c[1].button("Rifiuta", key=f"no_{a['id']}"):
                    esegui(store.decide_approval, a["id"], "rifiutata", io["id"], ok="Rifiutata")
                    st.rerun()


def pagina_dispositivi():
    nuovo = st.session_state.pop("_token_nuovo", None)
    if nuovo:
        st.success("Dispositivo registrato. Copia ora il token: non verrà più mostrato.")
        st.code(nuovo, language=None)
        st.caption("Sul PC: mettilo in bridge/.env come GUARDIAN_DEVICE_TOKEN=… (file escluso da git).")
    with st.expander("➕ Registra un PC"):
        with st.form("dev", clear_on_submit=True):
            uid = st.selectbox("Collaboratore", list(NOMI) or [io["id"]], format_func=nome,
                               index=(list(NOMI).index(io["id"]) if io["id"] in NOMI else 0))
            nome_pc = st.text_input("Nome del PC (es. PC-Menotti)")
            agente = st.text_input("Agente principale (es. Claude Code)")
            if st.form_submit_button("Registra"):
                r = esegui(store.register_device, uid, nome_pc, agente)
                if r:
                    st.session_state["_token_nuovo"] = r[1]
                    st.rerun()
    devices = esegui(store.devices) or []
    if not devices:
        st.info("Nessun PC registrato.")
    for d in devices:
        with st.container(border=True):
            c = st.columns([4, 1])
            c[0].markdown(f"**{d['nome']}** · {nome(d['user_id'])} {pill(stato_dispositivo(d))}", unsafe_allow_html=True)
            c[0].caption(f"Ultimo heartbeat: {fa(d.get('last_seen'))} · agente: {d.get('agent_name') or '—'}")
            if c[1].button("Revoca token", key=f"rev_{d['id']}", help="Il bridge di questo PC smette di funzionare"):
                esegui(store.revoke_device, d["id"], ok="Token revocato")
                st.rerun()


{"Overview": pagina_overview, "Agenti": pagina_agenti, "Task": pagina_task, "Attività": pagina_attivita,
 "Handoff": pagina_handoff, "Approvazioni": pagina_approvazioni, "Dispositivi": pagina_dispositivi}[pagina]()
st.caption(f"Guardian Hub · {store.modalita} · {datetime.now(timezone.utc):%H:%M} UTC")
