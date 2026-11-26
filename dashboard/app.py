"""Guardian - centrale di controllo per Claude Code.   Avvio: streamlit run dashboard/app.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # import dei moduli accanto ad app.py

import streamlit as st

import chat
import config
import fonte as fonte_mod
import monitor
import skill
import theme

st.set_page_config(page_title="Guardian", page_icon="🛡️", layout="wide")

# Tema scuro: .streamlit/config.toml vale solo se si avvia da dashboard/, quindi forzo anche da qui.
try:
    for chiave, valore in (("base", "dark"), ("primaryColor", "#00F0FF"), ("backgroundColor", "#080A12"),
                           ("secondaryBackgroundColor", "#0D1020"), ("textColor", "#E8F1FF")):
        st._config.set_option(f"theme.{chiave}", valore)
except Exception:
    pass
st.markdown(theme.CSS, unsafe_allow_html=True)


@st.cache_resource
def get_fonte():
    return fonte_mod.crea_fonte()


try:
    fonte = get_fonte()
except ValueError as e:
    st.error(f"Configurazione sorgente non valida: {e}")
    st.stop()


def fa(ts: float) -> str:
    s = max(0, int(time.time() - ts))
    return f"{s}s fa" if s < 60 else f"{s // 60}m fa" if s < 3600 else f"{s // 3600}h {s % 3600 // 60}m fa"


def esegui_e_mostra(prompt: str, cwd: str, resume: str | None) -> chat.Risposta:
    """Esegue sulla fonte e aggiorna in streaming l'interfaccia."""
    r = chat.Risposta()
    box, info = st.empty(), st.empty()
    box.markdown("⏳ _Claude sta lavorando…_")
    for ev in fonte.esegui(prompt, cwd, resume):
        if r.aggiungi(ev):
            box.markdown(r.testo or "⏳ _Claude sta lavorando…_")
            if r.strumenti:
                info.caption("🔧 " + " → ".join(r.strumenti[-6:]))
    if r.errore:
        box.error(r.errore if not r.testo else r.testo)
        if r.testo:
            st.error(r.errore)
    elif not r.testo.strip():
        box.info("(nessuna risposta testuale)")
    return r


if st.get_option("server.address") not in ("localhost", "127.0.0.1"):
    st.warning("⚠️ Il server ascolta su tutte le interfacce e la chat può far eseguire comandi a Claude: "
               "riavvia con `streamlit run dashboard/app.py --server.address localhost`.")
st.markdown(theme.intestazione(fonte.nome, config.CHAT_PERMISSION_MODE, config.REFRESH_S), unsafe_allow_html=True)
tab_stat, tab_agenti, tab_chat, tab_skill = st.tabs(["Statistiche", "Agenti", "Agente centrale", "Skill"])


# ---------------------------------------------------------------- 1. Statistiche
@st.fragment(run_every=config.REFRESH_S)
def vista_statistiche():
    p, c = fonte.processi(), fonte.cpu_totale()
    t = monitor.riepilogo_token(fonte.sessioni())
    a, b, c3, d = st.columns(4)
    a.markdown(theme.metrica("Processi Claude", str(p["n"]), sub="claude / @anthropic-ai/claude-code"), unsafe_allow_html=True)
    b.markdown(theme.metrica("CPU Claude", f"{p['cpu']:.1f}", "% core", f"{c['storico'][-1][2]:.1f}% della macchina",
                             pct=c["storico"][-1][2]), unsafe_allow_html=True)
    c3.markdown(theme.metrica("RAM Claude", f"{p['ram_mb']:.0f}", "MB", f"macchina: {c['ram_pct']:.0f}% di {c['ram_tot_mb']} MB",
                              pct=c["ram_pct"]), unsafe_allow_html=True)
    d.markdown(theme.metrica("CPU macchina", f"{c['cpu']:.0f}", "%", f"{c['n_core']} core", pct=c["cpu"]), unsafe_allow_html=True)
    sx, dx = st.columns([3, 2])
    with sx:
        st.subheader("CPU · ultimi 2 minuti")
        st.markdown(theme.legenda_cpu(), unsafe_allow_html=True)
        st.altair_chart(theme.grafico_cpu(c["storico"], c["n_core"]), width="stretch", theme=None)
    with dx:
        st.subheader("Token e costo (stima)")
        if t["ultima"]:
            u = t["ultima"]
            st.caption(f"sessione più recente · {u['progetto']}")
            m1, m2 = st.columns(2)
            m1.markdown(theme.metrica("Token in/out", f"{u['token_in'] + u['token_out']:,}", sub=f"in {u['token_in']:,} · out {u['token_out']:,}"),
                        unsafe_allow_html=True)
            m2.markdown(theme.metrica("Costo ≈", f"${u['costo']:.2f}", sub=f"cache {u['cache']:,}"), unsafe_allow_html=True)
            st.markdown(theme.metrica(f"Ultime {t['ore']:.0f}h · tutte le sessioni", f"${t['totale']['costo']:.2f}",
                                      sub=f"{t['totale']['token_out']:,} token output"), unsafe_allow_html=True)
        else:
            st.info("Nessuna sessione trovata in ~/.claude/projects")
    st.subheader("Processi")
    if p["lista"]:
        st.markdown(theme.tabella_processi(p["lista"]), unsafe_allow_html=True)
    else:
        st.caption("Nessun processo Claude Code in esecuzione.")


with tab_stat:
    vista_statistiche()


# ---------------------------------------------------------------- 2. Monitor agenti
@st.fragment(run_every=config.REFRESH_S)
def vista_agenti():
    righe = fonte.sessioni()
    al_lavoro = sum(r["stato"] == "al lavoro" for r in righe)
    st.caption(f"{al_lavoro} al lavoro · {len(righe) - al_lavoro} fermi · soglia {config.IDLE_THRESHOLD_S:.0f}s "
               f"· dati: JSONL" + (" + hook" if any(r["fonte"] == "hook" for r in righe) else " (hook non attivi)"))
    if not righe:
        st.info("Nessuna sessione recente in ~/.claude/projects")
        return
    st.markdown(theme.tabella_agenti(righe, fa), unsafe_allow_html=True)


with tab_agenti:
    vista_agenti()
    with st.expander("Attivare gli hook (aggiornamento immediato, opzionale)"):
        hook = (Path(__file__).resolve().parent / "hooks" / "guardian_hook.py")
        st.markdown("Aggiungi in `~/.claude/settings.json` (Guardian **non** lo modifica da solo):")
        voce = lambda: [{"hooks": [{"type": "command", "command": f"python3 {hook}"}]}]
        st.json({"hooks": {"UserPromptSubmit": voce(), "PreToolUse": [{"matcher": "*", **voce()[0]}],
                           "PostToolUse": [{"matcher": "*", **voce()[0]}], "Stop": voce()}})


# ---------------------------------------------------------------- 3. Agente centrale
def scegli_cartella(chiave: str) -> str:
    opzioni = fonte.progetti()
    ALTRA = "➕ Altra cartella…"
    scelta = st.selectbox("Cartella progetto", opzioni + [ALTRA], key=f"sel_{chiave}")
    if scelta == ALTRA or not opzioni:
        return st.text_input("Percorso cartella", key=f"txt_{chiave}", placeholder="/percorso/del/progetto").strip()
    return scelta


with tab_chat:
    st.session_state.setdefault("chat", {})  # cwd -> {"sid": ..., "msgs": [...]}
    cwd = scegli_cartella("chat")
    conv = st.session_state["chat"].setdefault(cwd, {"sid": None, "msgs": []})
    c1, c2 = st.columns([4, 1])
    c1.caption(f"Contesto: {'sessione ' + conv['sid'][:8] if conv['sid'] else 'nuova conversazione'}")
    if c2.button("Nuova conversazione", disabled=not conv["msgs"]):
        st.session_state["chat"][cwd] = {"sid": None, "msgs": []}
        st.rerun()
    for m in conv["msgs"]:
        with st.chat_message(m["ruolo"]):
            st.markdown(m["testo"])
            if m.get("nota"):
                st.caption(m["nota"])
    domanda = st.chat_input("Scrivi una domanda per Claude Code…", key="chat_in")
    if domanda:
        if not cwd:
            st.warning("Scegli una cartella progetto.")
        else:
            conv["msgs"].append({"ruolo": "user", "testo": domanda})
            with st.chat_message("user"):
                st.markdown(domanda)
            with st.chat_message("assistant"):
                r = esegui_e_mostra(domanda, cwd, conv["sid"])
            if r.session_id and not r.errore:
                conv["sid"] = r.session_id
            nota = " · ".join(x for x in (("🔧 " + ", ".join(r.strumenti)) if r.strumenti else "",
                                          f"≈${r.costo:.3f}" if r.costo else "") if x)
            conv["msgs"].append({"ruolo": "assistant", "testo": r.testo or (r.errore or ""), "nota": nota})


# ---------------------------------------------------------------- 4/5. Skill
with tab_skill:
    st.subheader("Skill installate")
    skills = fonte.skill_elenco()
    if not skills:
        st.info("Nessuna skill in ~/.claude/skills/*/SKILL.md")
    cols = st.columns(3)
    for i, s in enumerate(skills):
        with cols[i % 3]:
            st.markdown(theme.card_skill(s["nome"], s["descrizione"]), unsafe_allow_html=True)
            if st.button("Usa", key=f"usa_{s['cartella']}", use_container_width=True):
                st.session_state["skill_sel"] = s["nome"]
                st.session_state.pop("skill_out", None)
    sel = st.session_state.get("skill_sel")
    if sel:
        st.divider()
        with st.form("form_skill"):
            st.markdown(f"#### Skill · {sel}")
            richiesta = st.text_area("Cosa deve fare", placeholder="Descrivi il compito…")
            cartella_skill = scegli_cartella("skill")
            invia = st.form_submit_button("Esegui", type="primary")
        if invia:
            if not richiesta.strip() or not cartella_skill:
                st.warning("Compila 'cosa deve fare' e la cartella.")
            else:
                p = skill.prompt_skill(sel, richiesta)
                st.caption(f"Prompt inviato: `{p}`")
                with st.chat_message("assistant"):
                    esegui_e_mostra(p, cartella_skill, None)

    st.divider()
    st.subheader("Installa una skill da GitHub")
    with st.form("form_install", clear_on_submit=False):
        url = st.text_input("URL del repository", placeholder="https://github.com/utente/repo")
        ok = st.form_submit_button("Clona in ~/.claude/skills")
    if ok:
        if not skill.valida_url(url):
            st.error("Accetto solo URL del tipo https://github.com/<utente>/<repo>")
        else:
            with st.spinner("Clonazione in corso…"):
                res = fonte.installa_skill(url)
            (st.success if res["ok"] else st.error)(res["messaggio"])
            if res["ok"]:
                st.info("Ricarica la pagina per vedere la nuova card.")
