"""Guardian - centrale di controllo per Claude Code.   Avvio: streamlit run dashboard/app.py"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # import dei moduli accanto ad app.py

import streamlit as st

import avatar
import catalogo
import chat
import clienti
import config
import fonte as fonte_mod
import hashlib
import monitor
import plancia
import siti_demo
import skill
import storico as storico_conv
import team
import theme
import voce
import mic
import voce_out
from frame import html_frame

_FAVICON = Path(__file__).resolve().parent / "assets" / "logo" / "favicon.svg"
st.set_page_config(page_title="Guardian", page_icon=str(_FAVICON) if _FAVICON.exists() else "🛡️", layout="wide", initial_sidebar_state="auto")

# Tema scuro: .streamlit/config.toml vale solo se si avvia da dashboard/, quindi forzo anche da qui.
try:
    for chiave, valore in (("base", "dark"), ("primaryColor", "#00F0FF"), ("backgroundColor", "#080A12"),
                           ("secondaryBackgroundColor", "#0D1020"), ("textColor", "#E8F1FF")):
        st._config.set_option(f"theme.{chiave}", valore)
except Exception:
    pass
st.markdown(theme.CSS + theme.CSS_EXTRA + theme.CSS_PLANCIA + "<style>"
            + (Path(__file__).parent / "componenti/avatar/stile.css").read_text(encoding="utf-8") + "</style>",
            unsafe_allow_html=True)

import accesso
accesso.richiedi_pin(st)  # da remoto (Host non locale) serve il PIN; dal PC no


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


# Letture costose di fonte: cache breve (TTL in secondi) condivisa dai fragment e dal resto della pagina.
@st.cache_data(ttl=2, show_spinner=False)
def dati_sessioni(_f):
    return _f.sessioni()


@st.cache_data(ttl=2, show_spinner=False)
def dati_attivita(_f, limite: int, tipi: tuple | None = None):
    return _f.attivita(limite, set(tipi) if tipi else None)


@st.cache_data(ttl=10, show_spinner=False)
def dati_costi(_f, giorni: int):
    return _f.costi(giorni)


@st.cache_data(ttl=10, show_spinner=False)
def dati_skill(_f):
    return _f.skill_elenco()


@st.cache_data(ttl=60, show_spinner=False)
def mappa_skill_it() -> dict:
    return catalogo.carica_mappa_it()


@st.cache_data(ttl=10, show_spinner=False)
def dati_clienti(_f):
    return _f.clienti()


@st.cache_data(ttl=30, show_spinner=False)
def siti_salvati(cartella: str) -> frozenset:
    """Nomi dei file nella cartella siti-demo (una sola os.listdir invece di un exists() per scheda)."""
    try:
        return frozenset(os.listdir(cartella))
    except OSError:
        return frozenset()


@st.cache_data(ttl=30, show_spinner=False)
def dati_progetti(_f):
    return _f.progetti()


@st.cache_data(ttl=30, show_spinner=False)
def dati_scoperte(_f):
    return _f.scoperte()


def parla_ora(frasi: list[str], slot) -> None:
    """Accoda le frasi nella sintesi vocale del browser (la coda vive nella finestra principale)."""
    if frasi:
        with slot:
            html_frame(voce_out.js_parla(frasi), height=0)


def esegui_e_mostra(prompt: str, cwd: str, resume: str | None, agente: str | None = None, parla: bool = False) -> chat.Risposta:
    """Esegue sulla fonte e aggiorna in streaming l'interfaccia; con `parla` Guardian dice le frasi man mano che arrivano."""
    r = chat.Risposta()
    st.session_state["_rx"] = "pensiero"
    if (rx := st.session_state.get("_rx_ph")) is not None:
        rx.markdown(avatar.visuale("pensiero"), unsafe_allow_html=True)
    box, info, voce_slot, lavora_slot = st.empty(), st.empty(), st.empty(), st.empty()
    box.markdown("⏳ _Claude sta lavorando…_")
    with lavora_slot:
        html_frame(voce_out.js_lavora(True), height=0)       # il microfono a mani libere aspetta
    parlato = ""
    for ev in fonte.esegui(prompt, cwd, resume, agente):
        if r.aggiungi(ev):
            box.markdown(r.testo or "⏳ _Claude sta lavorando…_")
            if r.strumenti:
                info.caption("🔧 " + " → ".join(r.strumenti[-6:]))
            if parla and not r.errore:
                frasi, parlato = voce_out.prossimo_pezzo(voce_out.pulisci_per_voce(r.testo), parlato)
                parla_ora(frasi, voce_slot)
    if parla and not r.errore:                                  # ciò che resta (l'ultima frase)
        frasi, parlato = voce_out.prossimo_pezzo(voce_out.pulisci_per_voce(r.testo), parlato, finale=True)
        parla_ora(frasi, voce_slot)
    with lavora_slot:
        html_frame(voce_out.js_lavora(False), height=0)
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
st.markdown(theme.intestazione(fonte.nome, config.CHAT_PERMISSION_MODE, max(8, config.REFRESH_S)), unsafe_allow_html=True)
# ---------------------------------------------------------------- 1. Statistiche
@st.fragment(run_every=max(8, config.REFRESH_S))
def vista_statistiche():
    p, c = fonte.processi(), fonte.cpu_totale()
    t = monitor.riepilogo_token(dati_sessioni(fonte))
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


def sez_consumi():
    vista_statistiche()


# ---------------------------------------------------------------- 1b. Costi & output
@st.fragment(run_every=max(10, config.REFRESH_S * 5))
def vista_costi():
    k = dati_costi(fonte, 30)
    ric = fonte.ricavi()
    ricavo_mese = ric.get(k["mese_id"], 0.0)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(theme.metrica("Spesa oggi", f"${k['oggi']:.2f}", sub="stima a listino API"), unsafe_allow_html=True)
    c2.markdown(theme.metrica("Ultimi 7 giorni", f"${k['ultimi7']:.2f}", sub=f"media ${k['media7']:.2f}/giorno"), unsafe_allow_html=True)
    c3.markdown(theme.metrica("Questo mese", f"${k['mese']:.2f}", sub=f"proiezione fine mese ${k['proiezione_mese']:.2f}"), unsafe_allow_html=True)
    c4.markdown(theme.metrica("Ultimi 30 giorni", f"${k['ultimi30']:.2f}"), unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    b1.markdown(theme.metrica("Finestra ultime 5 ore", f"${k['ultime_5h']:.2f}", sub="spesa stimata nelle ultime 5 ore"), unsafe_allow_html=True)
    b2.markdown(theme.metrica("Burn rate", f"${k['burn_orario']:.2f}", "/ora", "media oraria sulle ultime 5 ore"), unsafe_allow_html=True)
    st.subheader("Spesa giornaliera · 30 giorni")
    st.altair_chart(theme.grafico_costi(k["giorni"]), width="stretch", theme=None)
    st.subheader("Mappa di calore · 12 settimane")
    st.altair_chart(theme.heatmap_giorni(dati_costi(fonte, 84)["giorni"]), width="content", theme=None)
    oggi = k["giorni"][-1]
    tot = {x: sum(g[x] for g in k["giorni"]) for x in ("msgs", "tools", "edits", "token_out")}
    st.subheader("Output · cosa produci")
    o1, o2, o3, o4 = st.columns(4)
    o1.markdown(theme.metrica("Risposte di Claude", f"{tot['msgs']:,}", sub=f"oggi {oggi['msgs']:,}"), unsafe_allow_html=True)
    o2.markdown(theme.metrica("Azioni (strumenti)", f"{tot['tools']:,}", sub=f"oggi {oggi['tools']:,}"), unsafe_allow_html=True)
    o3.markdown(theme.metrica("File modificati", f"{tot['edits']:,}", sub=f"oggi {oggi['edits']:,} · Edit/Write"), unsafe_allow_html=True)
    per_msg = k["ultimi30"] / tot["msgs"] if tot["msgs"] else 0
    o4.markdown(theme.metrica("Costo / risposta", f"${per_msg:.3f}", sub=f"{tot['token_out']:,} token output"), unsafe_allow_html=True)
    sx, dx = st.columns(2)
    with sx:
        st.subheader("Per progetto")
        st.markdown(theme.barre_orizzontali([(p["progetto"], p["costo"]) for p in k["progetti"]]), unsafe_allow_html=True)
    with dx:
        st.subheader("Per modello")
        st.markdown(theme.barre_orizzontali([(m["modello"], m["costo"]) for m in k["modelli"]]), unsafe_allow_html=True)
    st.subheader("Quanto guadagni · margine")
    r1, r2 = st.columns([1, 2])
    with r1:
        with st.form("form_ricavi"):
            nuovo = st.number_input(f"Ricavi di {k['mese_id']} (USD)", min_value=0.0, value=float(ricavo_mese), step=50.0)
            if st.form_submit_button("Salva ricavi"):
                try:
                    fonte.imposta_ricavo(k["mese_id"], float(nuovo))
                    st.rerun(scope="fragment")
                except ValueError as e:
                    st.error(str(e))
    with r2:
        if ricavo_mese > 0:
            margine = ricavo_mese - k["mese"]
            st.markdown(theme.metrica("Margine del mese", f"${margine:,.2f}",
                                      sub=f"ricavi ${ricavo_mese:,.2f} − spesa ${k['mese']:.2f} · ritorno {ricavo_mese / max(k['mese'], 0.01):.1f}×"),
                        unsafe_allow_html=True)
        else:
            st.caption("Inserisci a mano quanto incassi: Guardian non può saperlo da solo. Calcolerà margine e ritorno sulla spesa.")
    st.caption("Costi = token × prezzi di listino configurabili (PRICES_JSON). Con un abbonamento a tariffa fissa non è ciò che paghi davvero.")


def sez_costi():
    vista_costi()


# ---------------------------------------------------------------- 2. Monitor agenti
TIPI_FEED = {"delega": ["delega"], "web": ["web-ricerca", "web-apri", "browser"], "file": ["file"], "comando": ["comando"],
             "dice": ["dice"], "lettura": ["lettura"], "strumenti": ["strumento"]}


@st.fragment(run_every=2)
def vista_palcoscenico():
    """Cosa fanno gli agenti adesso: chi delega a chi, cosa cercano sul web, quali pagine aprono, cosa ne ricavano."""
    righe = dati_sessioni(fonte)
    al_lavoro = sum(r["stato"] == "al lavoro" for r in righe)
    scelte = st.pills("Mostra", list(TIPI_FEED), selection_mode="multi", default=["delega", "web", "file", "comando", "strumenti"],
                      key="f_att", label_visibility="collapsed") or list(TIPI_FEED)
    tipi = {x for k in scelte for x in TIPI_FEED[k]}
    ev = dati_attivita(fonte, 80, tuple(sorted(tipi)))
    ora = time.time()
    recenti = [e for e in ev if ora - e["ts"] < 600]
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(theme.tessera("Al lavoro", str(al_lavoro), f"{len(righe) - al_lavoro} fermi"), unsafe_allow_html=True)
    k2.markdown(theme.tessera("Eventi · 10 min", str(len(recenti)), "deleghe, ricerche, file"), unsafe_allow_html=True)
    k3.markdown(theme.tessera("Pagine aperte", str(sum(e["tipo"] in ("web-apri", "browser") for e in recenti)), "negli ultimi 10 min"), unsafe_allow_html=True)
    k4.markdown(theme.tessera("Deleghe", str(sum(e["tipo"] == "delega" for e in recenti)), "ordini del manager"), unsafe_allow_html=True)
    sx = dx = st.container()
    with sx:
        st.subheader("Diretta degli agenti")
        visto = st.session_state.get("_att_visto", 0.0)
        st.markdown(theme.feed_attivita(ev, fa, ora, visto), unsafe_allow_html=True)
        if ev:
            st.session_state["_att_visto"] = max(visto, max(e["ts"] for e in ev))
        st.caption("Le pagine si aprono nel browser dell'agente: qui vedi dove va e cosa ne ricava. Per vederle scorrere dal vivo, "
                   "usa Claude in Chrome (le schede appaiono nel tuo Chrome).")
    with dx:
        st.subheader("Chi lavora")
        if righe:
            st.markdown(theme.tabella_agenti(righe, fa), unsafe_allow_html=True)
        else:
            st.info("Nessuna sessione recente in ~/.claude/projects")
        st.caption(f"Soglia {config.IDLE_THRESHOLD_S:.0f}s · dati: JSONL" + (" + hook" if any(r["fonte"] == "hook" for r in righe) else " (hook non attivi)"))


def _schede_complete():
    """Schede agente con TUTTI gli eventi e i file (la griglia ne mostra solo i più recenti)."""
    return plancia.raggruppa_agenti(dati_sessioni(fonte), dati_attivita(fonte, 2000), max_eventi=1000, max_file=100)


def _chiudi_dettaglio():
    st.session_state.pop("_det_agente", None)


@st.dialog("Dettagli agente", width="large", on_dismiss=_chiudi_dettaglio)
def dettaglio_agente(chiave: str):
    c = next((x for x in _schede_complete() if x["chiave"] == chiave), None)
    if c is None:
        st.info("Questo agente non è più attivo o recente.")
        return
    st.markdown(theme.dettaglio_agente(c, fa), unsafe_allow_html=True)
    if not accesso.e_ospite(st) and st.button("Chiedi a Guardian di questo agente", icon=":material/forum:", type="primary", use_container_width=True,
                 key=f"chiedi_{plancia.chiave_widget(chiave)}"):
        st.session_state["_invio_guardian"] = (plancia.domanda_agente(c), f"Agente «{c['nome']}»: chiedo a Guardian")
        _chiudi_dettaglio()
        st.rerun()


@st.fragment(run_every=8)
def griglia_agenti():
    """Una scheda per agente attivo o recente (<= 2 h): le schede si dividono lo spazio in colonne."""
    schede = plancia.raggruppa_agenti(dati_sessioni(fonte), dati_attivita(fonte, 300))
    lavoro, finiti = plancia.dividi_agenti(schede)
    ro = plancia.riepilogo_oggi(dati_attivita(fonte, 300), dati_sessioni(fonte), time.time())
    u = ro["ultimo"]
    r1, r2, r3, r4 = st.columns(4, gap="small")
    r1.markdown(theme.tessera("Oggi · agenti finiti", str(ro["finiti"]), "compiti conclusi"), unsafe_allow_html=True)
    r2.markdown(theme.tessera("Oggi · file modificati", str(ro["file"]), "percorsi diversi"), unsafe_allow_html=True)
    r3.markdown(theme.tessera("Oggi · ricerche web", str(ro["ricerche"]), "fatte dagli agenti"), unsafe_allow_html=True)
    r4.markdown(theme.tessera("Ultimo finito", f"{u['minuti']} min fa" if u else "—", f"{u['nome']} · {u['compito'][:40]}" if u else "nessuno oggi"),
                unsafe_allow_html=True)
    if not schede:
        st.info("Nessun agente attivo o recente (ultime 2 ore). Quando un agente lavora compare qui la sua scheda. "
                "Suggerimento: apri lo spazio Squadra e premi «Assegna un compito».")
        return
    if not lavoro:
        st.info("Nessun agente al lavoro in questo momento. Qui sotto gli ultimi che hanno finito.")
    for i in range(0, len(lavoro), 5):
        gruppo = lavoro[i:i + 5]
        for col, c in zip(st.columns(len(gruppo), gap="small"), gruppo):
            with col.container(key=f"agc_{plancia.chiave_widget(c['chiave'])}"):
                st.markdown(theme.scheda_agente(c, fa), unsafe_allow_html=True)
                if st.button("Dettagli", icon=":material/open_in_full:", key=f"det_{plancia.chiave_widget(c['chiave'])}",
                             use_container_width=True, help=f"Apri i dettagli di {c['nome']}"):
                    st.session_state["_det_agente"] = c["chiave"]
                    st.rerun()   # rerun completo: il dialog nasce fuori dal fragment che si aggiorna ogni 3 s
    if finiti:
        with st.expander(f"Finiti di recente ({len(finiti)})", expanded=not lavoro):
            for c in finiti:
                r = st.columns([8, 1.4], vertical_alignment="center")
                r[0].markdown(f"<div class='g-fin-riga'><b>{theme.esc(c['nome'])}</b><span>{theme.esc(c['compito'][:90] or '—')}</span>"
                              f"<span class='q'>{theme.esc(fa(c['ultimo_agg']))}</span></div>", unsafe_allow_html=True)
                if r[1].button("Dettagli", key=f"det_{plancia.chiave_widget(c['chiave'])}", use_container_width=True):
                    st.session_state["_det_agente"] = c["chiave"]
                    st.rerun()


def sez_agenti():
    vista_palcoscenico()
    griglia_agenti()
    if st.session_state.get("_det_agente"):
        dettaglio_agente(st.session_state["_det_agente"])


def sez_squadra():
    st.subheader("Squadra di agenti")
    st.caption("Agenti Claude Code specializzati. Fanno solo ricerca e bozze: nessuno invia messaggi o contatta clienti da solo.")
    membri = fonte.squadra()
    if msg := st.session_state.pop("_lancio_msg", None):
        st.success(msg)
    for l in chat.LANCI[-5:]:
        st.caption(f"{theme.esc(l['agente'])} · {l['stato']} · {theme.esc(l['compito'][:80])}" + (f" · {theme.esc(l['errore'])}" if l["errore"] else ""))
    for i, m in enumerate(membri):
        with (cs := (st.columns(3) if i % 3 == 0 else cs))[i % 3].container(key=f"skc_sq_{plancia.chiave_widget(m['nome'])}"):
            st.markdown(theme.card_skill(plancia.nome_ruolo(m["nome"]), m["descrizione"], "installata" if m["installata"] else "da installare", slug=m["nome"]), unsafe_allow_html=True)
            if st.button("Assegna un compito", key=f"asg_{m['nome']}", disabled=not m["installata"], icon=":material/assignment:", use_container_width=True):
                dialog_lancia_agente(m["nome"], "", "sq")
    if any(not m["installata"] for m in membri) and st.button("Installa la squadra", type="primary", key="inst_squadra"):
        res = fonte.installa_squadra()
        (st.success if res["ok"] else st.error)(res["messaggio"])
        st.rerun()
    with st.form("form_azienda"):
        st.markdown("#### Profilo azienda · lo leggono tutti gli agenti")
        testo_az = st.text_area("Cosa vendi, a chi, zona, prezzo, cosa NON fare", value=fonte.azienda(), height=200)
        if st.form_submit_button("Salva profilo"):
            res = fonte.imposta_azienda(testo_az)
            (st.success if res["ok"] else st.error)(res["messaggio"])
    st.caption("Per usarli, in Claude Code scrivi: «usa cacciatore-clienti per trovare 20 clienti a …», poi «redattore-outreach» per le bozze "
               "e «analista-risultati» quando hai gli esiti.")
    with st.expander("Attivare gli hook (aggiornamento immediato, opzionale)"):
        hook = (Path(__file__).resolve().parent / "hooks" / "guardian_hook.py")
        st.markdown("Aggiungi in `~/.claude/settings.json` (Guardian **non** lo modifica da solo):")
        voce_hook = lambda: [{"hooks": [{"type": "command", "command": f"python3 {hook}"}]}]
        st.json({"hooks": {"UserPromptSubmit": voce_hook(), "PreToolUse": [{"matcher": "*", **voce_hook()[0]}],
                           "PostToolUse": [{"matcher": "*", **voce_hook()[0]}], "Stop": voce_hook()}})


# ---------------------------------------------------------------- 2b. Clienti (lead + visite di persona)
@st.dialog("Scheda di visita", width="large")
def dialog_scheda_visita(slug: str, azienda: str):
    st.markdown(f"**{azienda}**")
    sch = fonte.scheda_visita(slug)
    if sch:
        st.markdown(sch)   # testo scritto da un agente: Markdown senza HTML (unsafe_allow_html resta spento)
    else:
        st.info("Nessuna scheda di visita preparata per questo cliente (visite/" + slug + ".md).")


def sez_clienti():
    leads = dati_clienti(fonte)
    if not leads:
        st.info("Nessun lead ancora. In Claude Code scrivi «usa cacciatore-clienti per trovare 20 clienti a Cagliari»: "
                "i risultati compaiono qui (cartella leads/).")
    else:
        conta = lambda s: sum(1 for x in leads if x["stato"] == s)
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(theme.metrica("Lead", str(len(leads)), sub=f"{sum(1 for x in leads if x['adattamento'] >= 4)} con fit ≥ 4"), unsafe_allow_html=True)
        k2.markdown(theme.metrica("Da visitare", str(conta("da visitare"))), unsafe_allow_html=True)
        k3.markdown(theme.metrica("Interessati", str(conta("interessato")), sub=f"da richiamare {conta('richiamare')}"), unsafe_allow_html=True)
        k4.markdown(theme.metrica("Visitati", str(conta("visitato") + conta("interessato") + conta("richiamare") + conta("no"))), unsafe_allow_html=True)
        f1, f2, f3 = st.columns([2, 1, 1])
        cat = f1.multiselect("Categoria", sorted({x.get("categoria", "—") for x in leads}), key="cl_cat", placeholder="Tutte")
        minfit = f2.slider("Fit minimo", 0, 5, 3, key="cl_fit")
        st_f = f3.selectbox("Stato", ["tutti"] + list(__import__("clienti").STATI), key="cl_stato")
        vis = [x for x in leads if x["adattamento"] >= minfit and (not cat or x.get("categoria", "—") in cat)
               and (st_f == "tutti" or x["stato"] == st_f)]
        st.caption(f"{len(vis)} attività")
        st.markdown(theme.tabella_clienti(vis), unsafe_allow_html=True)
        if vis:
            st.subheader("Scheda e visita")
            sc1, sc2 = st.columns([3, 1], vertical_alignment="bottom")
            scelto = sc1.selectbox("Attività", [x["azienda"] for x in vis], key="cl_sel")
            c = next(x for x in vis if x["azienda"] == scelto)
            if sc2.button("Apri scheda visita", icon=":material/description:", key="cl_apri", use_container_width=True,
                          help=f"Apre visite/{c['slug']}.md in una finestra"):
                dialog_scheda_visita(c["slug"], c["azienda"])
            slug = c["slug"]
            a1, a2 = st.columns(2)
            if a1.button("Manda il web-designer su questo cliente", key="cl_wd", icon=":material/web:", use_container_width=True):
                dialog_lancia_agente("web-designer", f"Migliora siti-demo/{slug}.html usando la scheda visite/{slug}.md e il lead di {c['azienda']} (leads/). "
                                     "Modifica solo quel file e non contattare nessuno.", f"cl_{slug}")
            if a2.button("Prepara bozza di contatto", key="cl_ro", icon=":material/edit_note:", use_container_width=True):
                dialog_lancia_agente("redattore-outreach", f"Prepara solo una BOZZA di primo contatto per {c['azienda']} (slug {slug}), usando il lead e visite/{slug}.md. "
                                     "Non inviare nulla.", f"cl_{slug}")
            cx, cy = st.columns([3, 2])
            with cx:
                st.markdown(f"**{c['azienda']}** · {c.get('categoria', '—')} · {c.get('zona', '—')}")
                st.markdown(f"**Prova:** {c.get('prova', 'non verificato')}")
                if c.get("opportunita"):
                    st.markdown(f"**Opportunità:** {c['opportunita']}")
                st.markdown(f"**Contatto pubblico:** {c.get('contatto', 'non pubblico')}")
                if c.get("da_verificare", "").lower() in ("sì", "si", "yes", "true", "1"):
                    st.warning("Da verificare prima della visita.")
                sch = fonte.scheda_visita(c["slug"])
                if sch:
                    with st.expander("Scheda di visita preparata dall'agente"):
                        st.markdown(sch)
            with cy:
                with st.form(f"visita_{c['slug']}"):
                    stati = list(__import__("clienti").STATI)
                    nuovo = st.selectbox("Stato", stati, index=stati.index(c["stato"]))
                    note = st.text_area("Note", value=c["note"], height=110)
                    cons = st.checkbox("Il titolare mi ha dato il permesso di fotografare", value=c["consenso_foto"])
                    foto_up = st.file_uploader("Foto (JPG/PNG/WEBP)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
                    if st.form_submit_button("Salva visita"):
                        r = fonte.imposta_visita(c["slug"], nuovo, note, cons)
                        dati_clienti.clear()
                        (st.success if r["ok"] else st.error)(r["messaggio"])
                        for fl in foto_up or []:
                            rf = fonte.salva_foto(c["slug"], fl.getvalue(), cons)
                            (st.success if rf["ok"] else st.error)(rf["messaggio"])
                ft = fonte.foto(c["slug"])
                if ft:
                    st.image([f["dati"] for f in ft], caption=[f["nome"] for f in ft], width=120)


# ---------------------------------------------------------------- 3. Agente centrale
REPO = Path(__file__).resolve().parent.parent   # cartella predefinita del progetto: il repo che contiene dashboard/


def scegli_cartella(chiave: str) -> str:
    opzioni = [str(REPO)] + [p for p in dati_progetti(fonte) if p != str(REPO)]
    ALTRA = "➕ Altra cartella…"
    scelta = st.selectbox("Cartella progetto", opzioni + [ALTRA], key=f"sel_{chiave}")
    if scelta == ALTRA:
        return st.text_input("Percorso cartella", key=f"txt_{chiave}", placeholder="/percorso/del/progetto").strip()
    return scelta


@st.dialog("Assegna un compito", width="large")
def dialog_lancia_agente(agente: str, compito: str = "", chiave: str = "sq"):
    """Nessun avvio senza conferma: anteprima di ciò che verrà eseguito, poi «Conferma e lancia»."""
    st.markdown(f"**Agente:** `{agente}`")
    testo = st.text_area("Compito", value=compito, height=140, key=f"lc_t_{chiave}_{agente}")
    cwd = scegli_cartella(f"lc_{chiave}_{agente}")
    lancio = chat.prepara_lancio(agente, testo, cwd)
    st.caption(f"Modalità permessi: **{lancio['modo']}** (la stessa della chat; i lanci dalla dashboard non usano bypassPermissions).")
    if lancio["ok"]:
        st.markdown("**Verrà eseguito:**")
        st.code(chat.anteprima_lancio(lancio), language="text")
    else:
        st.warning(lancio["errore"])
    if st.button("Conferma e lancia", type="primary", key=f"lc_ok_{chiave}_{agente}", disabled=not lancio["ok"]):
        chat.lancia_in_background(fonte.esegui, lancio, agente)
        st.session_state["_lancio_msg"] = f"{agente} avviato in background: comparirà nello spazio Agenti."
        st.rerun()


@st.cache_data(ttl=300, show_spinner=False)
def _motore_voce() -> dict:
    return voce.motore_riconoscimento()


def microfono() -> str | None:
    """Registra, trascrive IN LOCALE (faster-whisper o riconoscimento di Windows), mostra il testo e chiede conferma."""
    mot = _motore_voce()
    if not mot["motore"]:
        st.warning(mot["mancante"])
        if voce.python_ok_per_whisper() and st.button("Installa il riconoscimento vocale locale", key="inst_voce",
                                                      disabled=fonte.nome.startswith("DEMO")):
            with st.spinner("Installazione in corso (alcuni minuti)…"):
                res = voce.installa()
            _motore_voce.clear()
            (st.success if res["ok"] else st.error)(res["messaggio"])
        return None
    st.caption("Riconoscimento locale: " + {"sherpa": "sherpa-onnx Parakeet v3 (offline, italiano)",
                                           "whisper": "faster-whisper (il primo uso scarica il modello ~140 MB)"}.get(mot["motore"], "Windows offline (it-IT)")
               + ". L'audio non viene inviato online. "
               "Vedi cosa ho capito e confermi tu.")
    audio = st.audio_input("Premi per registrare, premi di nuovo per fermare", key="mic")
    if audio is None:
        return None
    dati = audio.getvalue()
    h = hashlib.sha1(dati).hexdigest()
    if st.session_state.get("_voce_h") != h:
        with st.spinner("Ascolto…"):
            r = voce.trascrivi_locale(dati, mot["motore"])
        st.session_state.update(_voce_h=h, _voce_r=r)
    r = st.session_state["_voce_r"]
    if not r["ok"]:
        st.warning(r["messaggio"])
        return None
    testo = st.text_area("Ho capito (puoi correggere):", value=r["testo"], key=f"voce_t_{h}", height=90)
    cmd = plancia.riconosci_comando(testo)
    if cmd:
        st.caption("Lo eseguo come comando: " + {"riassunto": "riassunto agenti", "nuova": "nuova conversazione",
                                                  "apri": f"apri {cmd['valore']}", "voce": "voce " + ("on" if cmd["valore"] else "off")}[cmd["tipo"]])
    return testo if st.button("Invia a Guardian", type="primary", key=f"voce_i_{h}") else None


@st.dialog("Come si usa Guardian", width="large")
def dialog_guida():
    st.markdown(plancia.GUIDA)


@st.dialog("Conversazioni passate", width="large")
def dialog_conversazioni():
    giorni = storico_conv.elenco_giorni()
    if not giorni:
        st.info("Nessuna conversazione salvata.")
        return
    g = st.selectbox("Giorno", giorni, key="conv_giorno")
    for m in storico_conv.carica_giorno(g):
        chi = "Tu" if m["ruolo"] == "user" else "Guardian"
        st.markdown(f"**{chi}**", help=None)
        st.markdown(f'<div style="white-space:pre-wrap">{theme.esc(m["testo"])}</div>', unsafe_allow_html=True)


NOTA_PARLA = ("Guardian legge la risposta ad alta voce, frase per frase, con una voce italiana femminile del tuo sistema "
              "(su Windows «Microsoft Elsa», locale: il testo non esce dal PC). Le voci «online» del browser lo mandano al suo servizio: "
              "il pannello Voce le segnala.")


def conversazione_voce() -> str | None:
    """Mani libere: il browser rileva le pause, Whisper locale trascrive, il testo (sempre mostrato) va a Guardian."""
    mot = _motore_voce()
    if not mot["motore"]:
        st.warning(mot["mancante"])
        return None
    st.caption("Conversazione a voce: parli, fai una pausa, capisco in locale (l'audio non esce dal PC) e Guardian risponde a voce. "
               "Tace mentre Guardian lavora o parla.")
    v = mic.mic_continuo("mic_cont")
    if v and v["id"] != st.session_state.get("_mic_id"):
        st.session_state["_mic_id"] = v["id"]
        with st.spinner("Ascolto…"):
            rv = voce.trascrivi_locale(mic.decodifica(v), mot["motore"])
        st.session_state["_mic_ultimo"] = (f"Ho capito: «{rv['testo']}»" if rv["ok"] else f"Non ho capito: {rv['messaggio']}")
        if rv["ok"] and rv["testo"].strip():
            return rv["testo"].strip()
    if st.session_state.get("_mic_ultimo"):
        st.caption(st.session_state["_mic_ultimo"])
    return None


def sez_guardian():
    """Guardian compatto: storico a altezza fissa con scroll interno, input in fondo, microfono e riassunto agenti."""
    st.session_state.setdefault("chat", {})  # cwd -> {"sid": ..., "msgs": [...]}
    cmd = plancia.riconosci_comando(st.session_state.pop("_testo_voce", None))   # comando vocale confermato (widget non ancora creati)
    if cmd and cmd["tipo"] == "apri":
        st.session_state["spazio"] = cmd["valore"]
    elif cmd and cmd["tipo"] == "voce":
        st.session_state["voce_on"] = cmd["valore"]
    if not fonte.nome.startswith("DEMO") and not chat.agente_installato(config.MANAGER_AGENT):
        st.caption(f"⚠️ L'agente `{config.MANAGER_AGENT}` non è installato (pannello Squadra): rispondo come un normale Claude Code.")
    html_frame(avatar.modello(), height=345)
    reattore = st.empty()
    st.session_state["_rx_ph"] = reattore
    with st.container(key="g_barra"):
        c_mic, c_riass, c_voce, c_imp = st.columns(4, vertical_alignment="center")
        with c_mic.popover("Mic", icon=":material/mic:", use_container_width=True, help="Microfono", key="mic_pop"):
            testo_voce = microfono()
            st.toggle("Conversazione a voce (mani libere)", key="conv_voce", help="Parli, Guardian risponde a voce e ti riascolta. Serve il permesso del microfono nel browser.")
        if testo_voce and plancia.riconosci_comando(testo_voce):
            st.session_state["_testo_voce"] = testo_voce   # comando: applicato al giro successivo, prima dei widget
            st.rerun()
        riassunto = c_riass.button("Riassunto", icon=":material/summarize:", use_container_width=True, key="btn_riassunto",
                                   help="Manda a Guardian un riassunto (max 2000 caratteri) di agenti e attività correnti")
        voce_on = c_voce.toggle("Voce", value=True, key="voce_on", help=NOTA_PARLA)
        with c_imp.popover("Opzioni", icon=":material/tune:", use_container_width=True, help="Impostazioni"):
            cwd = scegli_cartella("chat")
            conv_tmp = st.session_state["chat"].get(cwd)
            if (cmd and cmd["tipo"] == "nuova") or st.button("Nuova conversazione", disabled=not (conv_tmp and conv_tmp["msgs"]), key="nuova_conv"):
                st.session_state["chat"][cwd] = {"sid": None, "msgs": []}   # conv è letta subito dopo: niente rerun
            if st.button("Conversazioni passate", key="conv_passate"):
                dialog_conversazioni()
            st.caption(NOTA_PARLA)
            html_frame(voce_out.html_impostazioni(), height=230)
    if st.session_state.get("conv_voce"):
        with st.container(key="g_conv"):
            testo_conv = conversazione_voce()
        if testo_conv and not testo_voce:
            testo_voce = testo_conv
    conv = st.session_state["chat"].setdefault(cwd, {"sid": None, "msgs": []})
    caricati = st.session_state.setdefault("_stor_caricato", set())
    if cwd not in caricati:   # una sola volta per sessione e cartella: «Nuova conversazione» non ricarica
        caricati.add(cwd)
        if not conv["msgs"]:
            conv["msgs"] = [{"ruolo": m["ruolo"], "testo": m["testo"]} for m in storico_conv.carica_oggi()]
    vuota = None
    if not conv["msgs"] and "_invio_guardian" not in st.session_state:
        vuota = st.empty()
        with vuota.expander("Comandi suggeriti", expanded=False):
            st.caption(f"Parli con **Guardian**, il manager (`{config.MANAGER_AGENT}`). Cartella: `{cwd}`")
            cols = st.columns(len(plancia.SUGGERIMENTI))
            for col, (chiave, etichetta) in zip(cols, plancia.SUGGERIMENTI):
                if col.button(etichetta, key=f"sugg_{chiave}", use_container_width=True):
                    st.session_state["_invio_guardian"] = plancia.costruisci_suggerimento(
                        chiave, dati_sessioni(fonte), dati_attivita(fonte, 200), dati_clienti(fonte), fonte.documenti_radice())
                    st.rerun()
        storico = None
    else:
        storico = st.container(height=190, border=True, key="chat_storico")
    domanda = st.chat_input("Scrivi a Guardian…", key="chat_in")
    invio = st.session_state.pop("_invio_guardian", None)   # (prompt, testo mostrato): es. dal pulsante «Usa» delle skill
    if invio:
        pass
    elif domanda:
        invio = (domanda, domanda)
    elif testo_voce:
        invio = (testo_voce, testo_voce)
    elif riassunto or (cmd and cmd["tipo"] == "riassunto"):
        invio = (plancia.domanda_riassunto(dati_sessioni(fonte), dati_attivita(fonte, 200)), "📋 Riassunto agenti (dati correnti allegati)")
    gesto = avatar.comando_da_testo(invio[0]) if invio and (domanda or testo_voce) else None
    if gesto:
        invio = None
        st.session_state["_avatar_gesto"] = gesto
    stato_avatar = "ascolto" if st.session_state.get("conv_voce") or st.session_state.get("mic") is not None else "riposo"
    reattore.markdown(avatar.visuale(stato_avatar, st.session_state.pop("_avatar_gesto", None)), unsafe_allow_html=True)
    if vuota is not None and invio:
        vuota.empty()
    if storico is None and invio:   # prima domanda dal chat_input/voce: i suggerimenti sono già stati disegnati, mostro lo storico sotto
        storico = st.container(height=190, border=True, key="chat_storico")
    if storico is None:
        return
    with storico:
        # Ordine DOM invertito + flex column-reverse (CSS): il riquadro resta ancorato in fondo, ultimo messaggio sempre visibile.
        nuovo_a = st.container() if invio else None
        nuovo_u = st.container() if invio else None
        for m in reversed(conv["msgs"]):
            with st.chat_message(m["ruolo"]):
                st.markdown(m["testo"])
                if m.get("nota"):
                    st.caption(m["nota"])
                if m.get("audio"):
                    st.audio(m["audio"]["dati"], format=m["audio"]["mime"])
        if invio:
            if not cwd:
                st.warning("Scegli una cartella progetto.")
            else:
                prompt, mostra = invio
                conv["msgs"].append({"ruolo": "user", "testo": mostra})
                salva_storico({"ruolo": "user", "testo": mostra})
                with nuovo_u:
                    with st.chat_message("user"):
                        st.text(mostra)
                with nuovo_a:
                  with st.chat_message("assistant"):
                    r = esegui_e_mostra(prompt, cwd, conv["sid"], config.MANAGER_AGENT, parla=bool(voce_on))
                    msg = {"ruolo": "assistant", "testo": r.testo or (r.errore or ""),
                           "nota": " · ".join(x for x in (("🔧 " + ", ".join(r.strumenti)) if r.strumenti else "",
                                                          f"≈${r.costo:.3f}" if r.costo else "") if x)}
                if r.session_id and not r.errore:
                    conv["sid"] = r.session_id
                conv["msgs"].append(msg)
                salva_storico({"ruolo": "assistant", "testo": msg["testo"]})
                reattore.markdown(avatar.visuale("errore" if r.errore else "felice"), unsafe_allow_html=True)


def salva_storico(msg: dict) -> bool:
    """Salva nello storico; se la cartella non è scrivibile la chat continua e l'avviso compare una sola volta."""
    try:
        ok = storico_conv.aggiungi(msg)
    except Exception:
        ok = False
    if not ok and msg.get("testo") and not st.session_state.get("_storico_avvisato"):
        st.session_state["_storico_avvisato"] = True
        st.caption("Storico non salvato: la cartella delle conversazioni non è scrivibile. La chat funziona lo stesso.")
    return ok


# ---------------------------------------------------------------- 4/5. Skill
def sez_skill():
    st.subheader("Skill installate")
    skills = dati_skill(fonte)
    if not skills:
        st.info("Nessuna skill trovata. Installane una dallo Store o da un URL GitHub qui sotto.")
    elif (cerca_q := st.session_state.get("cerca_skill", "").strip()) and not any(
            cerca_q.lower() in (s["nome"] + " " + s["descrizione"]).lower() for s in skills):
        st.info(f"Nessun risultato per «{cerca_q}»")
    f1, f2 = st.columns([3, 1])
    cerca = f1.text_input("Cerca", placeholder="nome o parola della descrizione…", label_visibility="collapsed", key="cerca_skill")
    origini = sorted({s.get("origine", "installata") for s in skills})
    scelta = f2.selectbox("Origine", ["tutte"] + origini, label_visibility="collapsed", key="orig_skill",
                          format_func=lambda o: "Origine: tutte" if o == "tutte" else f"Origine: {theme.ETICHETTA_ORIGINE.get(o, o)}",
                          help="Da dove arriva la skill (installata a mano, sincronizzata da claude.ai, plugin)")
    skills = [s for s in skills if (scelta == "tutte" or s.get("origine", "installata") == scelta)
              and (not cerca.strip() or cerca.strip().lower() in (s["nome"] + " " + s["descrizione"] + " " + mappa_skill_it().get(s["nome"], "")).lower())]
    conteggi = plancia.conta_categorie(skills)
    cat = st.pills("Categoria", ["Tutte"] + list(conteggi), format_func=lambda c: f"Tutte ({len(skills)})" if c == "Tutte" else f"{c} ({conteggi[c]})",
                   default="Tutte", key="cat_skill", label_visibility="collapsed") or "Tutte"
    if cat != "Tutte":
        skills = [s for s in skills if plancia.categoria_skill(s["nome"], s["descrizione"]) == cat]
    st.caption(f"{len(skills)} skill · Le skill si attivano da sole: Guardian e gli agenti scelgono quella giusta leggendo la "
               "descrizione, quando il compito corrisponde. «Usa» serve solo a imporne una precisa.")
    sel = st.session_state.get("skill_sel")
    if sel:   # il modulo sta IN CIMA allo spazio, così si vede subito dopo il clic
        with st.form("form_skill"):
            st.markdown(f"#### Usa la skill · {sel}")
            richiesta = st.text_area("Cosa deve fare", placeholder="Descrivi il compito… (la risposta arriva nella chat di Guardian, in alto)")
            b1, b2 = st.columns([1, 1])
            invia = b1.form_submit_button("Manda a Guardian", type="primary", use_container_width=True)
            annulla = b2.form_submit_button("Annulla", use_container_width=True)
        if annulla:
            st.session_state.pop("skill_sel", None)
            st.rerun()
        if invia:
            if not richiesta.strip():
                st.warning("Scrivi cosa deve fare.")
            else:
                st.session_state["_invio_guardian"] = (skill.prompt_skill(sel, richiesta), f"Skill «{sel}»: {richiesta.strip()}")
                st.session_state.pop("skill_sel", None)
                st.rerun()
    for i, s in enumerate(skills):
        chiave = plancia.chiave_widget(f"{s.get('origine', 'i')}_{s['cartella']}")
        with (cols := (st.columns(3) if i % 3 == 0 else cols))[i % 3].container(key=f"skc_{chiave}"):
            st.markdown(theme.card_skill(s["nome"], catalogo.descrizione_it(s["nome"], s["descrizione"], mappa_skill_it()), s.get("origine", "installata")), unsafe_allow_html=True)
            if st.button("Usa", key=f"usa_{chiave}", use_container_width=True, icon=":material/play_arrow:"):
                st.session_state["skill_sel"] = s["nome"]
                st.toast(f"Skill «{s['nome']}» scelta: scrivi il compito in cima allo spazio Skill.")
                st.rerun()

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
            dati_skill.clear()
            if res["ok"]:
                st.info("Ricarica la pagina per vedere la nuova card.")


# ---------------------------------------------------------------- 6. Store (catalogo verificato)
def sez_store():
    st.subheader("Skill di design verificate")
    st.caption("Catalogo fisso: ogni skill è stata letta e scansionata prima di entrare in elenco (solo testo e asset, nessuno script). "
               "Si installano in ~/.claude/skills e non sovrascrivono nulla di esistente.")
    voci = fonte.catalogo()
    mancanti = [v for v in voci if not v["installata"]]
    if mancanti and st.button(f"Installa tutte le {len(mancanti)} mancanti", type="primary", key="inst_tutte"):
        with st.spinner("Installazione in corso…"):
            for v in mancanti:
                res = fonte.installa_catalogo(v["id"])
                (st.success if res["ok"] else st.error)(f"{v['titolo']}: {res['messaggio']}")
        st.rerun()
    for i, v in enumerate(voci):
        with (colonne := (st.columns(3) if i % 3 == 0 else colonne))[i % 3].container(key=f"skc_store_{plancia.chiave_widget(v['id'])}"):
            st.markdown(theme.card_store(v), unsafe_allow_html=True)
            if v["installata"]:
                st.button("Installata", key=f"inst_{v['id']}", use_container_width=True, disabled=True, icon=":material/check:")
            elif st.button("Installa", key=f"inst_{v['id']}", use_container_width=True, icon=":material/download:"):
                with st.spinner(f"Installo {v['titolo']}…"):
                    res = fonte.installa_catalogo(v["id"])
                (st.success if res["ok"] else st.error)(res["messaggio"])
                if res["ok"]:
                    st.rerun()


# ---------------------------------------------------------------- Siti demo
def sez_siti():
    st.subheader("Siti demo dei clienti")
    st.caption("Per ogni cliente trovato genero un sito dimostrativo da mostrare di persona. Non invento nulla sull'attività: "
               "orari, contatti e prezzi restano «da inserire». Nessuna richiesta di rete: i siti "
               "personalizzati usano solo piccoli script locali (moduli demo che non inviano nulla, anteprime).")
    leads = dati_clienti(fonte)
    if not leads:
        st.info("Nessun cliente ancora: quando gli agenti trovano i lead (cartella leads/) compaiono qui.")
        return
    cartella = config.LEADS_DIR.parent / "siti-demo"
    tutti = st.session_state.get("siti_tutti", False)
    visibili = leads if tutti else leads[:9]
    presenti = siti_salvati(str(cartella))
    for i, x in enumerate(visibili):
        slug = siti_demo.slug_file(x["azienda"])
        stato_sito = "salvato" if f"{slug}.html" in presenti else "generato"
        with (cg := (st.columns(3) if i % 3 == 0 else cg))[i % 3].container(key=f"skc_sd_{slug}"):
            st.markdown(theme.card_skill(x["azienda"], f"{x.get('zona', '') or '—'}", f"{x.get('categoria', '') or '—'} · sito {stato_sito}"),
                        unsafe_allow_html=True)
            if st.button("Anteprima", key=f"sd_anteprima_{slug}", use_container_width=True, help=f"Anteprima del sito di {x['azienda']}"):
                st.session_state["siti_sel"] = x["azienda"]
    if len(leads) > 9:
        if st.button("Mostra meno" if tutti else f"Mostra tutti ({len(leads)})", key="siti_tutti_btn"):
            st.session_state["siti_tutti"] = not tutti
            st.rerun()
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    nome = c1.selectbox("Cliente", [x["azienda"] for x in leads], key="siti_sel")
    tema = c2.selectbox("Stile", list(siti_demo.TEMI), key="siti_tema")
    c = next(x for x in leads if x["azienda"] == nome)
    pagina, salvato = siti_demo.pagina(cartella, c["azienda"], c.get("categoria", ""), c.get("zona", ""), tema,
                                       c.get("opportunita", ""))
    if salvato:
        st.caption(f"Versione salvata in siti-demo/{siti_demo.slug_file(nome)}.html (personalizzata o già salvata): "
                   "lo stile scelto vale solo per i siti non ancora salvati.")
    with st.container(key="siti_cornice"):
        st.iframe(pagina, height=560)
    b1, b2 = st.columns(2)
    b1.download_button("Scarica questo sito (HTML)", data=pagina, file_name=f"{siti_demo.slug_file(nome)}.html", mime="text/html",
                       use_container_width=True)
    if b2.button("Salva i mancanti in siti-demo/", use_container_width=True, disabled=fonte.nome.startswith("DEMO")):
        cartella.mkdir(parents=True, exist_ok=True)
        siti_salvati.clear()
        nuovi = 0
        for x in leads:
            p = cartella / f"{siti_demo.slug_file(x['azienda'])}.html"
            if p.exists():   # mai sovrascrivere un sito già salvato o personalizzato
                continue
            p.write_text(siti_demo.genera_sito(x["azienda"], x.get("categoria", ""), x.get("zona", ""), tema,
                                               x.get("opportunita", "")), encoding="utf-8")
            nuovi += 1
        siti_salvati.clear()
        st.success(f"{nuovi} siti nuovi salvati in {cartella} (quelli già presenti non sono stati toccati)")


def pannello_scoperte():
    s = dati_scoperte(fonte)
    st.subheader("Scoperte")
    if s.get("aggiornato"):
        st.caption(f"Aggiornato: {plancia.data_italiana(s['aggiornato'])}")
    if not s["repo"] and not s["skill"]:
        st.info(s.get("messaggio") or "Nessuna scoperta al momento.")
        return

    _n = [0]

    def _griglia(voci_html: list[str]):
        n = _n[0]
        _n[0] += len(voci_html)
        for i, h in enumerate(voci_html):
            with (cols := (st.columns(3) if i % 3 == 0 else cols))[i % 3].container(key=f"scp_{n + i}"):
                st.markdown(h, unsafe_allow_html=True)

    st.markdown(f"<div class='g-sez'>Repo GitHub ({len(s['repo'])})</div>", unsafe_allow_html=True)
    _griglia([theme.card_scoperta(plancia.titolo_scoperta(r)[0], r.get("perche", ""),
                                  " · ".join(x for x in (f"{r['stelle']} stelle" if r.get("stelle") not in (None, "") else "",
                                                         f"licenza {r['licenza']}" if r.get("licenza") else "") if x),
                                  r.get("url", ""), sottotitolo=plancia.titolo_scoperta(r)[1]) for r in s["repo"]])
    st.markdown(f"<div class='g-sez'>Skill consigliate ({len(s['skill'])})</div>", unsafe_allow_html=True)
    _griglia([theme.card_scoperta(plancia.titolo_scoperta(k)[0], k.get("perche", ""),
                                  f"{k['installazioni']} installazioni" if k.get("installazioni") not in (None, "") else "",
                                  comando=k.get("comando", ""), sottotitolo=plancia.titolo_scoperta(k)[1]) for k in s["skill"]])
    if s["skill"]:
        st.caption("Il comando va copiato ed eseguito a mano, dopo aver letto la skill: da qui non si installa nulla.")


# ---------------------------------------------------------------- Team: le tre persone e il registro condiviso
@st.cache_data(ttl=30, show_spinner=False)
def dati_team():
    persone = team.leggi_persone()
    voci = team.leggi_registro()
    return team.riepilogo(persone, voci), voci, team.commit_recenti(), team.passaggi_aperti()


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_automatico(_quarto_d_ora: int):
    return team.aggiorna_da_github()   # al massimo una volta ogni 5 minuti, solo lettura


def sez_team():
    st.subheader("Team · chi fa cosa")
    st.caption("Tre persone, tre agenti. Ogni agente scrive una riga in registro/<id>.jsonl a fine compito e fa push sul suo branch: "
               "qui si leggono tutti i branch di GitHub, anche prima del merge.")
    _fetch_automatico(int(time.time() // 300))
    c1, c2 = st.columns([1.6, 3], vertical_alignment="center")
    if c1.button("Aggiorna da GitHub", icon=":material/sync:", key="team_fetch", use_container_width=True):
        ok, msg = team.aggiorna_da_github()
        dati_team.clear()
        (st.toast if ok else st.warning)(msg)
    persone, voci, commit, passaggi = dati_team()
    c2.caption(f"{len(voci)} voci nel registro · {len(commit)} commit negli ultimi 7 giorni")
    for ps in passaggi:
        st.warning(f"**Passaggio {ps['stato']}** da {ps['da']} per {ps['per']}: {ps['titolo']}  \n"
                   f"File `passaggi/{ps['nome']}` · branch `{ps['branch']}` · {team.quando(ps['creato'])}. "
                   "Chi continua: «leggi il passaggio e continua» al proprio agente.", icon=":material/swap_horiz:")
    if not persone:
        st.info("Manca registro/persone.json nel repository.")
        return
    for col, p in zip(st.columns(len(persone), gap="small"), persone):
        u = p["ultima"]
        sotto = f"{u['azione'][:60]} · {team.quando(u['ts'])}" if u else "nessuna voce ancora"
        stato = f"{p['oggi']} oggi" + (f" · {p['bloccate']} bloccate" if p["bloccate"] else "")
        col.markdown(theme.tessera(f"{p.get('nome', p['id'])} · {p.get('agente', '')}", stato, sotto), unsafe_allow_html=True)
        col.caption(theme.esc(p.get("ruolo", "")) + (f" · branch `{theme.esc(p['branch'])}`" if p.get("branch") else ""))
    nomi = {p["id"]: p.get("nome", p["id"]) for p in persone}
    filtro = st.segmented_control("Filtra", ["tutti", *nomi], format_func=lambda k: "Tutti" if k == "tutti" else nomi[k],
                                  default="tutti", key="team_filtro", label_visibility="collapsed") or "tutti"
    mostra = [v for v in voci if filtro == "tutti" or v["chi"] == filtro][:100]
    if not mostra:
        st.info("Nessuna voce. Il primo compito finito da un agente comparirà qui.")
    for v in mostra:
        file = ", ".join(v["file"][:4]) + (" …" if len(v["file"]) > 4 else "")
        st.markdown(f"<div class='g-fin-riga'><b>{theme.esc(nomi.get(v['chi'], v['chi']))}</b>"
                    f"<span>{theme.esc(v['azione'])}{' · ' + theme.esc(file) if file else ''}</span>"
                    f"<span class='q'>{theme.esc(v.get('esito') or '')} · {theme.esc(v.get('agente') or '')} · "
                    f"{theme.esc(team.quando(v['ts']))}</span></div>", unsafe_allow_html=True)
    with st.expander(f"Commit su tutti i branch (ultimi 7 giorni: {len(commit)})"):
        for c in commit:
            st.markdown(f"<div class='g-fin-riga'><b>{theme.esc(c['autore'])}</b><span>{theme.esc(c['messaggio'])}</span>"
                        f"<span class='q'>{theme.esc(c['hash'])} · {theme.esc(team.quando(c['ts']))}</span></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- Plancia unica
SPAZI = [("agenti", "Agenti", sez_agenti), ("team", "Team", sez_team), ("skill", "Skill", sez_skill), ("squadra", "Squadra", sez_squadra),
         ("store", "Store", sez_store), ("clienti", "Clienti", sez_clienti), ("siti", "Siti demo", sez_siti),
         ("scoperte", "Scoperte", pannello_scoperte), ("consumi", "Consumi", sez_consumi), ("costi", "Costi", sez_costi)]


@st.fragment(run_every=15)
def utilizzo_reale():
    """Limiti reali 5 ore / settimana, dalla barra di stato di Claude Code (hooks/guardian_statusline.py)."""
    try:
        d = plancia.descrivi_usage(fonte.usage())
    except Exception:
        d = None
    if not d or not d["barre"]:
        st.info("Dati non ancora arrivati. Se non succede nulla, attiva la barra di stato di Guardian (vedi README)."
                + (f" Ultimo aggiornamento: {d['eta']}." if d else ""))
    else:
        for b in d["barre"]:
            st.markdown(theme.barra_utilizzo(b["titolo"], b["pct"], b["reset"]), unsafe_allow_html=True)
        aiuto = None
        try:
            k = dati_costi(fonte, 30)
            aiuto = f"Stima a listino API: oggi ${k['oggi']:.2f} · ultime 5 h ${k['ultime_5h']:.2f}"
        except Exception:
            pass
        st.caption(("DEMO · valori finti · " if d["demo"] else "") + d["eta"], help=aiuto)


@st.fragment(run_every=15)
def riepilogo_modelli():
    st.subheader("Modelli · 30 giorni")
    try:
        modelli = dati_costi(fonte, 30).get("modelli", [])
    except (OSError, ValueError, KeyError):
        modelli = []
    if modelli:
        for m in modelli[:4]:
            st.text(f"{m['modello']} · ${m['costo']:.2f}")
        st.caption("Dati demo · Stima a listino API" if fonte.nome.startswith("DEMO") else "Stima a listino API")
    else:
        st.caption("Nessun consumo per modello disponibile.")
    st.button("Dettaglio costi", key="rapido_costi", on_click=st.session_state.update,
              args=({"spazio": "costi"},), use_container_width=True)


# ---------------------------------------------------------------- Barra laterale: catalogo agenti e skill
@st.cache_data(ttl=60, show_spinner=False)
def dati_catalogo_agenti() -> list[dict]:
    out = []
    for nome in chat.agenti_installati():
        s = catalogo.scheda_agente(nome)
        out.append({"nome": nome, "ruolo": plancia.nome_ruolo(nome), "descrizione": s["descrizione"]})
    return out


@st.cache_data(ttl=60, show_spinner=False)
def dati_scheda_agente(nome: str) -> dict:
    return catalogo.scheda_agente(nome)


@st.cache_data(ttl=60, show_spinner=False)
def dati_percorso_skill(cartella: str) -> str:
    p = catalogo.percorso_skill(cartella)
    return str(p) if p else ""


def dialog_voce(tipo: str, nome: str, cartella: str = "", descrizione: str = ""):
    """Apre il pop-up con titolo = nome di ruolo (agente) o nome skill (st.dialog fissa il titolo alla definizione)."""
    titolo = (plancia.nome_ruolo(nome) if tipo == "agente" else nome) or "Dettaglio"
    st.dialog(titolo, width="large")(_corpo_voce)(tipo, nome, cartella, descrizione)


def _corpo_voce(tipo: str, nome: str, cartella: str = "", descrizione: str = ""):
    if tipo == "agente":
        s = dati_scheda_agente(nome)
        st.caption(f"Agente · {nome}")
        st.markdown(theme.esc(s["descrizione"]))
        st.markdown("**Strumenti:** " + (", ".join(f"`{theme.esc(t)}`" for t in s["tools"]) if s["tools"] else "tutti quelli di default"))
        st.markdown("**File:**")
        st.code(s["percorso"], language="text")
        if st.button("Assegna un compito", type="primary", key=f"dv_ag_{nome}", icon=":material/assignment:"):
            st.session_state["_lancia_da_catalogo"] = nome   # la conferma (dialog_lancia_agente) si apre al giro dopo
            st.rerun()
    else:
        st.caption("Skill · " + plancia.categoria_skill(nome, descrizione))
        _it = catalogo.descrizione_it(nome, "", mappa_skill_it())
        st.markdown(theme.esc(_it or descrizione or "(nessuna descrizione)"))
        if _it and descrizione:
            st.caption("Descrizione originale: " + theme.esc(descrizione))
        perc = dati_percorso_skill(cartella)
        st.markdown("**File:**")
        st.code(perc or "(percorso non trovato: skill sincronizzata o remota)", language="text")
        richiesta = st.text_area("Cosa deve fare", placeholder="Descrivi il compito…", key=f"dv_sk_t_{cartella}")
        if st.button("Usa", type="primary", key=f"dv_sk_{cartella}", icon=":material/play_arrow:"):
            if not richiesta.strip():
                st.warning("Scrivi cosa deve fare.")
            else:
                st.session_state["_invio_guardian"] = (skill.prompt_skill(nome, richiesta), f"Skill «{nome}»: {richiesta.strip()}")
                st.rerun()


@st.fragment
def barra_laterale():
    with st.sidebar:
        st.markdown("<div class='g-side-titolo' role='heading' aria-level='2'>Catalogo</div>", unsafe_allow_html=True)
        cerca = st.text_input("Cerca agenti e skill", placeholder="Cerca agenti e skill…", key="cerca_catalogo", label_visibility="collapsed")
        agenti = catalogo.filtra(dati_catalogo_agenti(), cerca)
        skills = catalogo.filtra([dict(s, nome_cat=plancia.categoria_skill(s["nome"], s["descrizione"])) for s in dati_skill(fonte)], cerca)
        aperto = bool(cerca.strip())
        st.markdown(f"<div class='g-side-gruppo' role='heading' aria-level='3'>Agenti <span>{len(agenti)}</span></div>", unsafe_allow_html=True)
        for cat, voci in catalogo.raggruppa(agenti, lambda v: catalogo.categoria_agente(v["nome"])).items():
            with st.expander(f"{cat} ({len(voci)})", expanded=aperto):
                for v in voci:
                    if st.button(v["ruolo"], key=f"sb_ag_{v['nome']}", use_container_width=True, help=v["ruolo"]):
                        dialog_voce("agente", v["nome"])
        st.markdown(f"<div class='g-side-gruppo' role='heading' aria-level='3'>Skill <span>{len(skills)}</span></div>", unsafe_allow_html=True)
        for cat, voci in catalogo.raggruppa(skills, lambda v: v["nome_cat"]).items():
            with st.expander(f"{cat} ({len(voci)})", expanded=aperto):
                for v in voci:
                    ch = plancia.chiave_widget(f"{v.get('origine', 'i')}_{v['cartella']}")
                    if st.button(v["nome"], key=f"sb_sk_{ch}", use_container_width=True, help=v["nome"]):
                        dialog_voce("skill", v["nome"], v["cartella"], v["descrizione"])
        if not agenti and not skills:
            st.caption(f"Nessun risultato per «{cerca.strip()}»" if cerca.strip() else "Nessun risultato.")
        if st.button("Guida", key="sb_guida", icon=":material/help:", use_container_width=True):
            dialog_guida()


OSPITE = accesso.e_ospite(st)   # amici da remoto con il PIN ospiti: solo lettura
if OSPITE:
    SPAZI = [x for x in SPAZI if x[0] in ("team", "agenti")]
    st.caption("Accesso ospite in sola lettura: vedi il Team e gli agenti al lavoro. Chat e lanci sono solo sul PC del titolare.")
else:
    barra_laterale()
if not OSPITE and (_ag := st.session_state.pop("_lancia_da_catalogo", None)):
    dialog_lancia_agente(_ag, chiave="cat")

# Panoramica operativa e passaggi rapidi per il titolare
if not OSPITE:
    scorciatoie = st.columns(4)
    for col, titolo, spazio in zip(scorciatoie, ("Diretta", "Consumi", "Clienti", "Team"),
                                  ("agenti", "consumi", "clienti", "team")):
        col.button(titolo, key=f"rapido_{spazio}", use_container_width=True,
                   on_click=st.session_state.update, args=({"spazio": spazio},))
    posta, centro, consumi = st.columns([1, 2.7, 1.35], gap="medium")
    with posta:
        with st.container(border=True, key="plancia_posta"):
            st.subheader("Posta")
            st.caption("Conteggio non letti non collegato")
            st.link_button("Apri Gmail", "https://mail.google.com/mail/#inbox", use_container_width=True)
    with centro:
        with st.container(key="plancia_guardian"):
            sez_guardian()
    with consumi:
        with st.container(key="plancia_utilizzo"):
            utilizzo_reale()
            riepilogo_modelli()

# BASSO: barra di spazi; lo spazio scelto riempie l'area come una pagina a sé
etichette = {chiave: titolo for chiave, titolo, _ in SPAZI}
scelto = st.segmented_control("Spazi", list(etichette), format_func=etichette.get, default="agenti", key="spazio",
                              label_visibility="collapsed")
scelto = scelto if scelto in etichette else "agenti"
with st.container(key=f"sez_{scelto}"):
    next(fn for chiave, _, fn in SPAZI if chiave == scelto)()
