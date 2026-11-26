"""Guardian - centrale di controllo per Claude Code.   Avvio: streamlit run dashboard/app.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # import dei moduli accanto ad app.py

import pandas as pd
import streamlit as st

import chat
import config
import fonte as fonte_mod
import monitor
import skill

st.set_page_config(page_title="Guardian", page_icon="🛡️", layout="wide")

# Tema scuro: .streamlit/config.toml vale solo se si avvia da dashboard/, quindi forzo anche da qui.
try:
    st._config.set_option("theme.base", "dark")
except Exception:
    pass
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp, [data-testid="stHeader"] { background: #0e1117; color: #e6e6e6; }
[data-testid="stMetric"], .gcard { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: .7rem .9rem; }
.gcard { min-height: 7.2rem; margin-bottom: .3rem; }
.gcard b { color: #9db4ff; } .gcard span { color: #9aa4b2; font-size: .85rem; }
.block-container { padding-top: 2.2rem; max-width: 1400px; }
</style>""", unsafe_allow_html=True)


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
st.title("🛡️ Guardian")
st.caption(f"Sorgente: **{fonte.nome}** · aggiornamento ogni {config.REFRESH_S}s · "
           f"permessi chat: `{config.CHAT_PERMISSION_MODE}`")
tab_stat, tab_agenti, tab_chat, tab_skill = st.tabs(["📊 Statistiche", "🤖 Agenti", "💬 Agente centrale", "🧩 Skill"])


# ---------------------------------------------------------------- 1. Statistiche
@st.fragment(run_every=config.REFRESH_S)
def vista_statistiche():
    p, c = fonte.processi(), fonte.cpu_totale()
    sessioni = fonte.sessioni()
    t = monitor.riepilogo_token(sessioni)
    a, b, c3, d = st.columns(4)
    a.metric("Processi Claude Code", p["n"])
    b.metric("CPU Claude (% di un core)", f"{p['cpu']:.1f}")
    c3.metric("RAM Claude", f"{p['ram_mb']:.0f} MB")
    d.metric("CPU totale macchina", f"{c['cpu']:.0f}%", help=f"{c['n_core']} core · RAM usata {c['ram_pct']:.0f}% di {c['ram_tot_mb']} MB")
    sx, dx = st.columns([3, 2])
    with sx:
        st.subheader("CPU totale · ultimi 2 minuti")
        df = pd.DataFrame(c["storico"], columns=["s", "CPU %"]).set_index("s")
        st.line_chart(df, height=240, y_label="CPU %", x_label="secondi fa")
    with dx:
        st.subheader("Token e costo (stima)")
        if t["ultima"]:
            u = t["ultima"]
            st.markdown(f"**Sessione più recente** · {u['progetto']}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Input/Output", f"{u['token_in'] + u['token_out']:,}", help=f"in {u['token_in']:,} · out {u['token_out']:,}")
            m2.metric("Cache", f"{u['cache']:,}")
            m3.metric("Costo ≈", f"${u['costo']:.2f}")
            st.caption(f"Ultime {t['ore']:.0f}h, tutte le sessioni: ${t['totale']['costo']:.2f} · "
                       f"{t['totale']['token_out']:,} token output")
        else:
            st.info("Nessuna sessione trovata in ~/.claude/projects")
    st.subheader("Processi")
    if p["lista"]:
        st.dataframe(pd.DataFrame(p["lista"]).rename(columns={"nome": "Nome", "cpu": "CPU %", "ram_mb": "RAM MB", "cmd": "Comando"}),
                     hide_index=True, use_container_width=True)
    else:
        st.caption("Nessun processo Claude Code in esecuzione.")


with tab_stat:
    vista_statistiche()


# ---------------------------------------------------------------- 2. Monitor agenti
@st.fragment(run_every=config.REFRESH_S)
def vista_agenti():
    righe = fonte.sessioni()
    al_lavoro = sum(r["stato"] == "al lavoro" for r in righe)
    st.markdown(f"**{al_lavoro}** al lavoro · {len(righe) - al_lavoro} fermi · soglia {config.IDLE_THRESHOLD_S:.0f}s "
                f"· dati: JSONL" + (" + hook" if any(r["fonte"] == "hook" for r in righe) else " (hook non attivi)"))
    if not righe:
        st.info("Nessuna sessione recente in ~/.claude/projects")
        return
    df = pd.DataFrame([{
        "Stato": ("🟢 " if r["stato"] == "al lavoro" else "⚪ ") + r["stato"],
        "Progetto": r["progetto"],
        "Tipo": r["tipo"] + (f" {r['agente'][:7]}" if r["agente"] else ""),
        "Ultimo strumento": r["strumento"] or "—",
        "Ultimo messaggio": r["messaggio"][:160],
        "Aggiornato": fa(r["ultimo_agg"]),
        "Costo ≈": f"${r['costo']:.2f}",
    } for r in righe])
    st.dataframe(df, hide_index=True, use_container_width=True, height=min(600, 44 + 35 * len(df)))


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
    if c2.button("🗑️ Nuova conversazione", disabled=not conv["msgs"]):
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
            desc = s["descrizione"] if len(s["descrizione"]) < 180 else s["descrizione"][:177] + "…"
            st.markdown(f"<div class='gcard'><b>{s['nome']}</b><br><span>{desc}</span></div>", unsafe_allow_html=True)
            if st.button("Usa", key=f"usa_{s['cartella']}", use_container_width=True):
                st.session_state["skill_sel"] = s["nome"]
                st.session_state.pop("skill_out", None)
    sel = st.session_state.get("skill_sel")
    if sel:
        st.divider()
        with st.form("form_skill"):
            st.markdown(f"#### Skill **{sel}**")
            richiesta = st.text_area("Cosa deve fare", placeholder="Descrivi il compito…")
            cartella_skill = scegli_cartella("skill")
            invia = st.form_submit_button("▶️ Esegui", type="primary")
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
        ok = st.form_submit_button("⬇️ Clona in ~/.claude/skills")
    if ok:
        if not skill.valida_url(url):
            st.error("Accetto solo URL del tipo https://github.com/<utente>/<repo>")
        else:
            with st.spinner("Clonazione in corso…"):
                res = fonte.installa_skill(url)
            (st.success if res["ok"] else st.error)(res["messaggio"])
            if res["ok"]:
                st.info("Ricarica la pagina per vedere la nuova card.")
