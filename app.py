import json
import os
import time
import uuid
from datetime import datetime, timezone

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(
    page_title="AI Agent Manager",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}
.hero {padding: 1.25rem 1.4rem; border: 1px solid rgba(128,128,128,.25); border-radius: 16px; margin-bottom: 1rem;}
.muted {color: var(--text-color); opacity: .72;}
div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.2); padding: .8rem; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

AGENTS = [
    {"id": "planner", "name": "Planner", "role": "Scompone obiettivi in compiti ordinati e dipendenze.", "icon": "🧭"},
    {"id": "research", "name": "Research", "role": "Raccoglie e sintetizza informazioni usando solo strumenti configurati.", "icon": "🔎"},
    {"id": "creator", "name": "Creator", "role": "Produce bozze, testi, piani e contenuti originali.", "icon": "✍️"},
    {"id": "operator", "name": "Operator", "role": "Esegue solo strumenti esplicitamente implementati e autorizzati.", "icon": "⚙️"},
    {"id": "quality", "name": "Quality & Safety", "role": "Controlla completezza, rischi, duplicati e necessità di approvazione.", "icon": "🛡️"},
    {"id": "analyst", "name": "Analyst", "role": "Definisce metriche e riassume i risultati.", "icon": "📊"},
]

SYSTEM_PROMPT = """Sei il Planner centrale di un sistema multi-agent chiamato AI Agent Manager.
Trasforma la richiesta dell'utente in un piano concreto e realistico.
Non affermare di aver eseguito azioni esterne: in questa demo non esistono integrazioni reali.
Non inventare accessi, risultati di ricerca o pubblicazioni.
Rendi espliciti i prerequisiti, gli strumenti mancanti, i rischi e i punti che richiedono approvazione umana.
Non suggerire di aggirare termini di servizio, copyright, controlli di accesso o limiti delle API.
Restituisci SOLO JSON valido con questa struttura:
{
 "summary": "breve descrizione",
 "tasks": [
  {"title":"...", "agent":"planner|research|creator|operator|quality|analyst",
   "description":"...", "depends_on":[0], "status":"In attesa",
   "requires_approval": true, "risk":"basso|medio|alto", "success_criteria":"..."}
 ],
 "assumptions":["..."],
 "approvals":["..."],
 "missing_integrations":["..."]
}
Crea da 3 a 8 compiti. Usa indici numerici per depends_on. Le azioni esterne, pubblicazioni, invii, acquisti, cancellazioni o modifiche ad account devono richiedere approvazione.
"""

def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)

def get_client():
    key = get_secret("OPENAI_API_KEY")
    if not key or OpenAI is None:
        return None
    return OpenAI(api_key=key)

def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end+1]
    return json.loads(text)

def fallback_plan(goal):
    return {
        "summary": "Piano iniziale generato in modalità demo. Collega un modello API per la pianificazione AI.",
        "tasks": [
            {"title":"Chiarire obiettivo e vincoli","agent":"planner","description":f"Definire risultato atteso, scadenza, budget e limiti per: {goal}","depends_on":[],"status":"In attesa","requires_approval":False,"risk":"basso","success_criteria":"Obiettivo e vincoli sono espliciti."},
            {"title":"Raccogliere informazioni e prerequisiti","agent":"research","description":"Identificare dati, account, file e strumenti necessari. Nessuna ricerca web è eseguita in questa demo.","depends_on":[0],"status":"In attesa","requires_approval":False,"risk":"basso","success_criteria":"Elenco dei prerequisiti e delle fonti disponibili."},
            {"title":"Preparare una bozza del risultato","agent":"creator","description":"Creare una prima bozza o piano operativo senza effettuare azioni esterne.","depends_on":[1],"status":"In attesa","requires_approval":False,"risk":"basso","success_criteria":"Output controllabile e coerente con l'obiettivo."},
            {"title":"Controllo qualità e rischi","agent":"quality","description":"Verificare completezza, autorizzazioni, copyright, sicurezza e possibili errori.","depends_on":[2],"status":"In attesa","requires_approval":False,"risk":"medio","success_criteria":"Checklist qualità completata."},
            {"title":"Approvazione prima di azioni esterne","agent":"operator","description":"Se servono pubblicazioni, invii, acquisti o modifiche, attendere conferma umana e integrazione autorizzata.","depends_on":[3],"status":"Richiede approvazione","requires_approval":True,"risk":"alto","success_criteria":"L'utente approva esplicitamente l'azione dopo averne esaminato i dettagli."},
            {"title":"Misurare e riferire i risultati","agent":"analyst","description":"Definire le metriche e produrre un report dopo l'esecuzione effettiva.","depends_on":[4],"status":"In attesa","requires_approval":False,"risk":"basso","success_criteria":"Report con risultati verificati e attività non completate."}
        ],
        "assumptions":["Gli strumenti esterni non sono ancora collegati."],
        "approvals":["Qualsiasi azione che pubblica, invia, acquista, cancella o modifica dati esterni."],
        "missing_integrations":["Connettori specifici per le azioni richieste","Archivio persistente per lavori tra sessioni"]
    }

def make_plan(goal, context):
    client = get_client()
    if client is None:
        return fallback_plan(goal), "demo"
    model = get_secret("OPENAI_MODEL", "gpt-4.1-mini")
    user_prompt = f"Richiesta utente:\n{goal}\n\nVincoli aggiuntivi:\n{context or 'Nessuno specificato'}"
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":user_prompt},
            ],
        )
        plan = parse_json(response.choices[0].message.content or "")
        if not isinstance(plan.get("tasks"), list) or not plan["tasks"]:
            raise ValueError("Il modello non ha restituito compiti validi.")
        valid_agents = {a["id"] for a in AGENTS}
        for i, task in enumerate(plan["tasks"]):
            if task.get("agent") not in valid_agents:
                task["agent"] = "planner"
            task.setdefault("depends_on", [])
            task.setdefault("status", "In attesa")
            task.setdefault("requires_approval", task.get("risk") == "alto")
            task.setdefault("risk", "medio")
            task.setdefault("success_criteria", "Risultato verificato.")
            task.setdefault("description", "")
            task.setdefault("title", f"Compito {i+1}")
            if task.get("risk") == "alto":
                task["requires_approval"] = True
                task["status"] = "Richiede approvazione"
        plan.setdefault("summary", "Piano creato.")
        plan.setdefault("assumptions", [])
        plan.setdefault("approvals", [])
        plan.setdefault("missing_integrations", [])
        return plan, "api"
  except Exception as e:
    st.error(
        f"Errore API OpenAI: {type(e).__name__}: {e}"
    )
    return fallback_plan(goal), "demo"

def init_state():
    defaults = {
        "jobs": [],
        "messages": [{"role":"assistant","content":"Ciao! Descrivimi un obiettivo. Creo un piano di lavoro e mostro quali attività richiedono approvazione. In questa versione gli strumenti esterni non sono ancora collegati."}],
        "active_job_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

with st.sidebar:
    st.markdown("## 🧠 AI Agent Manager")
    st.caption("Prototipo multi-agent • Streamlit")
    page = st.radio("Navigazione", ["Chat & Manager", "Dashboard", "Agenti", "Impostazioni & limiti"], label_visibility="collapsed")
    st.divider()
    api_ready = bool(get_secret("OPENAI_API_KEY")) and OpenAI is not None
    st.metric("Motore di pianificazione", "API AI" if api_ready else "Modalità demo")
    st.caption("La pianificazione non esegue automaticamente azioni esterne.")
    st.divider()
    if st.button("🧹 Cancella cronologia sessione", use_container_width=True):
        st.session_state.jobs = []
        st.session_state.messages = []
        st.session_state.active_job_id = None
        st.rerun()

st.markdown('<div class="hero"><h1>🧠 AI Agent Manager</h1><p class="muted">Un unico punto di controllo per pianificare lavori, coordinare agenti e approvare azioni sensibili.</p></div>', unsafe_allow_html=True)

if page == "Chat & Manager":
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.subheader("Chat centrale")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        prompt = st.chat_input("Es. Prepara una strategia di contenuti per YouTube Shorts...")
        with st.expander("Opzioni del nuovo lavoro"):
            context = st.text_area("Vincoli, scadenza, budget, account o preferenze", placeholder="Es. Budget massimo 20 €, solo contenuti originali, nessuna pubblicazione senza conferma.")
        if prompt:
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.spinner("Il Manager sta preparando il piano..."):
                plan, mode = make_plan(prompt, context)
            job = {
                "id": str(uuid.uuid4())[:8],
                "goal": prompt,
                "context": context,
                "plan": plan,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
                "status": "Richiede approvazione" if any(t.get("requires_approval") for t in plan["tasks"]) else "Pianificato",
            }
            st.session_state.jobs.insert(0, job)
            st.session_state.active_job_id = job["id"]
            st.session_state.messages.append({"role":"assistant","content":f"**Piano creato** · ID `{job['id']}`\n\n{plan.get('summary','')}\n\nHo preparato {len(plan['tasks'])} compiti. Le azioni esterne non vengono eseguite finché non saranno collegati gli strumenti e ottenute le approvazioni necessarie."})
            st.rerun()
    with right:
        st.subheader("Lavoro selezionato")
        if st.session_state.jobs:
            job_ids = [j["id"] for j in st.session_state.jobs]
            selected = st.selectbox("Seleziona un lavoro", job_ids, index=job_ids.index(st.session_state.active_job_id) if st.session_state.active_job_id in job_ids else 0)
            job = next(j for j in st.session_state.jobs if j["id"] == selected)
            st.session_state.active_job_id = selected
            st.markdown(f"**{job['goal']}**")
            st.caption(f"ID: {job['id']} · Modalità: {job['mode']} · Creato: {job['created_at'][:19]} UTC")
            st.info(job["status"])
            for i, task in enumerate(job["plan"]["tasks"]):
                with st.container(border=True):
                    st.markdown(f"**{i+1}. {task['title']}**")
                    st.caption(f"Agente: {task['agent']} · Rischio: {task.get('risk','medio')}")
                    st.write(task.get("description",""))
                    st.caption(f"Successo: {task.get('success_criteria','')}")
                    if task.get("requires_approval"):
                        st.warning("Questa attività richiede approvazione umana.")
                        approval_key = f"approval_{job['id']}_{i}"
                        approved = st.checkbox("Approvo l'avvio di questa attività", key=approval_key)
                        if approved:
                            st.caption("Approvazione registrata solo in questa sessione. Non è stata eseguita alcuna azione esterna.")
            with st.expander("Assunzioni, approvazioni e integrazioni mancanti"):
                st.markdown("**Assunzioni**")
                for x in job["plan"].get("assumptions", []): st.write(f"- {x}")
                st.markdown("**Approvazioni**")
                for x in job["plan"].get("approvals", []): st.write(f"- {x}")
                st.markdown("**Integrazioni mancanti**")
                for x in job["plan"].get("missing_integrations", []): st.write(f"- {x}")
        else:
            st.info("Scrivi un obiettivo nella chat per creare il primo piano.")

elif page == "Dashboard":
    jobs = st.session_state.jobs
    task_count = sum(len(j["plan"].get("tasks", [])) for j in jobs)
    approval_count = sum(1 for j in jobs for t in j["plan"].get("tasks", []) if t.get("requires_approval"))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Lavori creati", len(jobs))
    c2.metric("Compiti pianificati", task_count)
    c3.metric("In attesa di approvazione", approval_count)
    c4.metric("Agenti disponibili", len(AGENTS))
    st.subheader("Cronologia lavori")
    if not jobs:
        st.info("Non ci sono ancora lavori. Vai su Chat & Manager per crearne uno.")
    else:
        for job in jobs:
            with st.container(border=True):
                col1,col2 = st.columns([4,1])
                col1.markdown(f"**{job['goal']}**")
                col1.caption(f"ID {job['id']} · {job['created_at'][:19]} UTC · {len(job['plan']['tasks'])} compiti")
                col2.write(job["status"])
                if st.button("Apri", key=f"open_{job['id']}"):
                    st.session_state.active_job_id = job["id"]
                    st.info("Apri la pagina Chat & Manager per esaminare il lavoro selezionato.")

elif page == "Agenti":
    st.subheader("Registro degli agenti")
    st.caption("In questa versione gli agenti sono ruoli di pianificazione. Gli esecutori reali si aggiungono collegando strumenti e API autorizzati.")
    for agent in AGENTS:
        with st.container(border=True):
            a,b = st.columns([1,5])
            a.markdown(f"# {agent['icon']}")
            b.markdown(f"**{agent['name']}** · `{agent['id']}`")
            b.write(agent["role"])
            b.caption("Stato: configurato come ruolo · Esecuzione esterna: non collegata")

elif page == "Impostazioni & limiti":
    st.subheader("Configurazione")
    st.write("Per attivare il piano AI, aggiungi i Secrets nell'area di gestione della tua app Streamlit.")
    st.code('OPENAI_API_KEY = "inserisci-la-tua-chiave"\nOPENAI_MODEL = "gpt-4.1-mini"', language="toml")
    st.warning("Non inserire mai chiavi API nel codice o in un repository pubblico.")
    st.markdown("### Limiti attuali")
    st.markdown("""
- I lavori e la cronologia sono conservati in `st.session_state`: non sono un archivio permanente e possono sparire quando la sessione viene riavviata.
- La modalità demo non usa un modello AI e non esegue ricerche sul web.
- La modalità API genera piani, ma non esegue strumenti esterni.
- Non ci sono ancora worker persistenti, code, scheduler 24/7 o integrazioni YouTube.
- Le caselle di approvazione sono dimostrative: non rappresentano un sistema di autorizzazione sicuro per azioni reali.
- Per la produzione occorrono autenticazione, database persistente, audit log, permessi per utente e backend separato.
""")
    st.markdown("### Prossimi connettori possibili")
    st.write("Ricerca web, archiviazione file, e-mail, Google Drive, API YouTube, scheduler e notifiche. Implementali uno alla volta, ciascuno con permessi minimi e test.")

st.divider()
st.caption("AI Agent Manager · Starter MVP · Non esegue azioni esterne. Controlla sempre output e autorizzazioni.")
