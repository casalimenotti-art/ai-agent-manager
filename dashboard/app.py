"""Guardian - centrale di controllo per Claude Code.   Avvio: streamlit run dashboard/app.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # import dei moduli accanto ad app.py

import streamlit as st

import chat
import clienti
import config
import fonte as fonte_mod
import hashlib
import lavori
import monitor
import siti_demo
import skill
import theme
import voce
import mic
import voce_out
from frame import html_frame

st.set_page_config(page_title="Guardian", page_icon="🛡️", layout="wide")

# Tema scuro: .streamlit/config.toml vale solo se si avvia da dashboard/, quindi forzo anche da qui.
try:
    for chiave, valore in (("base", "dark"), ("primaryColor", "#00F0FF"), ("backgroundColor", "#080A12"),
                           ("secondaryBackgroundColor", "#0D1020"), ("textColor", "#E8F1FF")):
        st._config.set_option(f"theme.{chiave}", valore)
except Exception:
    pass
st.markdown(theme.CSS + theme.CSS_EXTRA, unsafe_allow_html=True)


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


def parla_ora(frasi: list[str], slot) -> None:
    """Accoda le frasi nella sintesi vocale del browser (la coda vive nella finestra principale)."""
    if frasi:
        with slot:
            html_frame(voce_out.js_parla(frasi), height=0)


def esegui_e_mostra(prompt: str, cwd: str, resume: str | None, agente: str | None = None, parla: bool = False) -> chat.Risposta:
    """Esegue sulla fonte e aggiorna in streaming l'interfaccia; con `parla` Guardian dice le frasi man mano che arrivano."""
    r = chat.Risposta()
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
st.markdown(theme.intestazione(fonte.nome, config.CHAT_PERMISSION_MODE, config.REFRESH_S), unsafe_allow_html=True)
SEZIONI = [("centro", "Centro"), ("consumi", "Consumi"), ("costi", "Costi"), ("agenti", "Agenti"), ("clienti", "Clienti"),
           ("siti", "Siti demo"), ("guardian", "Guardian"), ("skill", "Skill"), ("store", "Store")]


def vai(k: str):
    st.session_state["sezione"] = k


sezione = st.segmented_control("Sezione", [k for k, _ in SEZIONI], format_func=dict(SEZIONI).get, key="sezione",
                               default="centro", label_visibility="collapsed") or "centro"


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


def sez_consumi():
    vista_statistiche()


# ---------------------------------------------------------------- 1b. Costi & output
@st.fragment(run_every=max(10, config.REFRESH_S * 5))
def vista_costi():
    k = fonte.costi(30)
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
    st.altair_chart(theme.heatmap_giorni(fonte.costi(84)["giorni"]), width="content", theme=None)
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
             "dice": ["dice"], "lettura": ["lettura"]}


@st.fragment(run_every=2)
def vista_palcoscenico():
    """Cosa fanno gli agenti adesso: chi delega a chi, cosa cercano sul web, quali pagine aprono, cosa ne ricavano."""
    righe = fonte.sessioni()
    al_lavoro = sum(r["stato"] == "al lavoro" for r in righe)
    scelte = st.pills("Mostra", list(TIPI_FEED), selection_mode="multi", default=["delega", "web", "file", "comando", "dice"],
                      key="f_att", label_visibility="collapsed") or list(TIPI_FEED)
    tipi = {x for k in scelte for x in TIPI_FEED[k]}
    ev = fonte.attivita(80, tipi)
    ora = time.time()
    recenti = [e for e in ev if ora - e["ts"] < 600]
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(theme.tessera("Al lavoro", str(al_lavoro), f"{len(righe) - al_lavoro} fermi"), unsafe_allow_html=True)
    k2.markdown(theme.tessera("Eventi · 10 min", str(len(recenti)), "deleghe, ricerche, file"), unsafe_allow_html=True)
    k3.markdown(theme.tessera("Pagine aperte", str(sum(e["tipo"] in ("web-apri", "browser") for e in recenti)), "negli ultimi 10 min"), unsafe_allow_html=True)
    k4.markdown(theme.tessera("Deleghe", str(sum(e["tipo"] == "delega" for e in recenti)), "ordini del manager"), unsafe_allow_html=True)
    sx, dx = st.columns([3, 2])
    with sx:
        st.subheader("Cosa sta succedendo")
        visto = st.session_state.get("_att_visto", 0.0)
        st.markdown(theme.feed_attivita(ev, fa, ora, visto), unsafe_allow_html=True)
        if ev:
            st.session_state["_att_visto"] = max(e["ts"] for e in ev)
        st.caption("Le pagine si aprono nel browser dell'agente: qui vedi dove va e cosa ne ricava. Per vederle scorrere dal vivo, "
                   "usa Claude in Chrome (le schede appaiono nel tuo Chrome).")
    with dx:
        st.subheader("Chi lavora")
        if righe:
            st.markdown(theme.tabella_agenti(righe, fa), unsafe_allow_html=True)
        else:
            st.info("Nessuna sessione recente in ~/.claude/projects")
        st.caption(f"Soglia {config.IDLE_THRESHOLD_S:.0f}s · dati: JSONL" + (" + hook" if any(r["fonte"] == "hook" for r in righe) else " (hook non attivi)"))


def sez_agenti():
    vista_palcoscenico()
    st.subheader("Squadra di agenti")
    st.caption("Agenti Claude Code specializzati. Fanno solo ricerca e bozze: nessuno invia messaggi o contatta clienti da solo.")
    membri = fonte.squadra()
    cs = st.columns(3)
    for i, m in enumerate(membri):
        with cs[i % 3]:
            st.markdown(theme.card_skill(m["nome"], m["descrizione"], "installata" if m["installata"] else "da installare"), unsafe_allow_html=True)
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
def sez_clienti():
    leads = fonte.clienti()
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
            scelto = st.selectbox("Attività", [x["azienda"] for x in vis], key="cl_sel")
            c = next(x for x in vis if x["azienda"] == scelto)
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
                        (st.success if r["ok"] else st.error)(r["messaggio"])
                        for fl in foto_up or []:
                            rf = fonte.salva_foto(c["slug"], fl.getvalue(), cons)
                            (st.success if rf["ok"] else st.error)(rf["messaggio"])
                ft = fonte.foto(c["slug"])
                if ft:
                    st.image([f["dati"] for f in ft], caption=[f["nome"] for f in ft], width=120)


# ---------------------------------------------------------------- 3. Agente centrale
def scegli_cartella(chiave: str) -> str:
    opzioni = fonte.progetti()
    ALTRA = "➕ Altra cartella…"
    scelta = st.selectbox("Cartella progetto", opzioni + [ALTRA], key=f"sel_{chiave}")
    if scelta == ALTRA or not opzioni:
        return st.text_input("Percorso cartella", key=f"txt_{chiave}", placeholder="/percorso/del/progetto").strip()
    return scelta


@st.cache_resource
def get_lavori():
    """Le chat vivono nel server, non nella pagina: i lavori continuano anche se chiudi o ricarichi il browser."""
    demo = fonte.nome.startswith("DEMO")
    return lavori.Lavori(fonte, None if demo else config.VISITE_DIR / "chat.json", iniziali=3, cwd_default=(fonte.progetti() or [""])[0])


ALTRA = "➕ Altra cartella…"
SENZA_AGENTE = "Claude Code (normale)"


@st.fragment(run_every=1.2)
def pannello_chat(cid: str):
    L = get_lavori()
    s = L.istantanea(cid)
    if not s:
        return
    st.markdown(theme.chat_testata(s["nome"], "lavora" if s["in_corso"] else "pronta", s["durata"]), unsafe_allow_html=True)
    with st.expander("Cartella, agente e voce"):
        opz = fonte.progetti()
        if s["cwd"] and s["cwd"] not in opz:
            opz = [s["cwd"]] + opz
        sel = st.selectbox("Cartella progetto", opz + [ALTRA], index=opz.index(s["cwd"]) if s["cwd"] in opz else 0, key=f"cwd_{cid}")
        nuova_cwd = st.text_input("Percorso", key=f"cwdt_{cid}").strip() if sel == ALTRA or not opz else sel
        installati = [m["nome"] for m in fonte.squadra() if m["installata"]]
        scelte = [SENZA_AGENTE] + installati
        attuale = s["agente"] if s["agente"] in installati else SENZA_AGENTE
        ag = st.selectbox("Agente", scelte, index=scelte.index(attuale), key=f"ag_{cid}", disabled=s["in_corso"],
                          help="Chi risponde in questa chat. Il manager `guardian-manager` coordina gli altri agenti.")
        pl = st.toggle("Parla a voce", value=s["parla"], key=f"pl_{cid}")
        if (nuova_cwd and nuova_cwd != s["cwd"]) or (ag if ag != SENZA_AGENTE else None) != s["agente"] or pl != s["parla"]:
            if not s["in_corso"]:
                L.imposta(cid, cwd=nuova_cwd or s["cwd"], agente=None if ag == SENZA_AGENTE else ag, parla=pl)
        c1, c2 = st.columns(2)
        if c1.button("Azzera", key=f"az_{cid}", disabled=s["in_corso"], use_container_width=True):
            L.reset(cid)
        if c2.button("Chiudi chat", key=f"ch_{cid}", disabled=s["in_corso"] or len(L.ids()) <= 1, use_container_width=True):
            L.chiudi(cid)
            st.rerun()
    with st.container(height=400, border=True):
        if not s["msgs"] and not s["in_corso"]:
            st.caption("Scrivi un compito qui sotto. Questa chat lavora in parallelo alle altre.")
        for m in s["msgs"]:
            with st.chat_message(m["ruolo"]):
                st.markdown(m["testo"])
                if m.get("nota"):
                    st.caption(m["nota"])
        if s["in_corso"]:
            with st.chat_message("assistant"):
                st.markdown(s["testo"] or "⏳ _al lavoro…_")
                if s["strumenti"]:
                    st.caption("🔧 " + " → ".join(s["strumenti"][-5:]))
    if s["parla"] and s["da_leggere"]:                       # voce: solo frasi complete, man mano che arrivano
        c = L.get(cid)
        frasi, c.parlato = voce_out.prossimo_pezzo(voce_out.pulisci_per_voce(s["testo"]), s["parlato"], finale=s["fatto"] and not s["in_corso"])
        parla_ora(frasi, st.empty())
        if s["fatto"] and not s["in_corso"] and not s["errore"]:
            L.segna_letto(cid)
    with st.form(f"f_{cid}", clear_on_submit=True, border=False):
        testo = st.text_area("Messaggio", key=f"t_{cid}", height=80, label_visibility="collapsed", placeholder="Scrivi il compito…")
        inv = st.form_submit_button("Invia", type="primary", disabled=s["in_corso"], use_container_width=True)
    if inv:
        res = L.invia(cid, testo)
        if res["ok"]:
            st.rerun(scope="fragment")
        else:
            st.warning(res["messaggio"])
    if s["in_corso"] and st.button("Stop", key=f"stop_{cid}", use_container_width=True):
        L.ferma(cid)


@st.fragment(run_every=1.5)
def barra_chat():
    """Quante chat lavorano; avvisa che il consumo cresce; segnala al microfono a mani libere quando tacere."""
    L = get_lavori()
    n = L.in_corso()
    st.caption(f"{n} su {len(L.ids())} chat al lavoro" + (f" · attenzione: {n} lavori in parallelo consumano il limite {n} volte più in fretta" if n >= 2 else ""))
    voce_attiva = any(L.istantanea(i)["in_corso"] and L.get(i).parla for i in L.ids())
    if st.session_state.get("_flag_lavora") != voce_attiva:
        st.session_state["_flag_lavora"] = voce_attiva
        html_frame(voce_out.js_lavora(voce_attiva), height=0)


def sez_guardian():
    L = get_lavori()
    if chat.agente_installato(config.MANAGER_AGENT):
        st.caption(f"Fino a {lavori.MAX_CHAT} chat nello stesso momento, ognuna con la sua cartella e il suo agente. "
                   f"La prima è **Guardian**, il manager (`{config.MANAGER_AGENT}`): coordina gli altri agenti.")
    else:
        st.warning(f"L'agente `{config.MANAGER_AGENT}` non è installato: installa la squadra dalla sezione Agenti. Intanto le chat rispondono come Claude Code normale.")
    b1, b2 = st.columns([4, 1])
    with b1:
        barra_chat()
    if b2.button("＋ Nuova chat", disabled=len(L.ids()) >= lavori.MAX_CHAT, use_container_width=True, help=f"Massimo {lavori.MAX_CHAT}"):
        L.nuova(cwd=(fonte.progetti() or [""])[0])
        st.rerun()
    ids = L.ids()
    for k in range(0, len(ids), 3):
        righe = ids[k:k + 3]
        for col, cid in zip(st.columns(len(righe)), righe):
            with col:
                pannello_chat(cid)
    with st.expander("Voce e microfono (parlano con la prima chat, Guardian)"):
        cv1, cv2 = st.columns([1, 1])
        with cv1:
            st.caption("Uso le voci del tuo sistema: su Windows una voce italiana **locale** (il testo non esce dal PC). Le voci «online» "
                       "mandano il testo al servizio del browser: il pannello le segnala. Ogni chat ha il suo interruttore «Parla a voce».")
        with cv2:
            html_frame(voce_out.html_impostazioni(), height=230)
        st.markdown("#### Conversazione a voce")
        st.caption("Un clic su «Avvia conversazione», poi parli e fai una pausa: capisco in locale e mando il testo a Guardian. "
                   "Tace mentre Guardian lavora o parla.")
        prima = L.ids()[0]
        voce_in = mic.mic_continuo("mic_cont")
        if voce_in and voce_in["id"] != st.session_state.get("_mic_id"):
            st.session_state["_mic_id"] = voce_in["id"]
            dati_wav = mic.decodifica(voce_in)
            if not voce.disponibile():
                st.warning("Per capire la voce serve il riconoscimento locale: installalo qui sotto (una volta).")
            else:
                with st.spinner("Ascolto…"):
                    rv = voce.trascrivi(dati_wav)
                if rv["ok"]:
                    res = L.invia(prima, rv["testo"])
                    st.caption(f"Ho capito: «{rv['testo']}»" + ("" if res["ok"] else f" — non inviato: {res['messaggio']}"))
                else:
                    st.caption(f"Non ho capito: {rv['messaggio']}")
        with st.expander("Un messaggio alla volta (con conferma)"):
            audio = st.audio_input("Premi per registrare, premi di nuovo per fermare", key="mic")
            if audio is not None:
                dati = audio.getvalue()
                h = hashlib.sha1(dati).hexdigest()
                if st.session_state.get("_voce_h") != h:
                    r0 = voce.trascrivi(dati) if voce.disponibile() else {"ok": False, "testo": "", "messaggio": "Riconoscimento vocale non installato (vedi sotto)."}
                    st.session_state.update(_voce_h=h, _voce_r=r0)
                r = st.session_state["_voce_r"]
                if r["ok"]:
                    testo_voce = st.text_area("Ho capito (puoi correggere):", value=r["testo"], key=f"voce_t_{h}")
                    if st.button("Invia a Guardian", type="primary", key=f"voce_i_{h}"):
                        res = L.invia(prima, testo_voce)
                        st.caption("Inviato." if res["ok"] else res["messaggio"])
                else:
                    st.warning(r["messaggio"])
        if not voce.disponibile():
            st.caption(f"Serve il pacchetto {voce.PACCHETTO} {voce.VERSIONE} (versione fissata, solo wheel). Il primo riconoscimento scarica "
                       "il modello (~140 MB) da Hugging Face; l'audio non viene mai inviato.")
            if st.button("Installa il riconoscimento vocale locale", key="inst_voce", disabled=fonte.nome.startswith("DEMO")):
                with st.spinner("Installazione in corso (alcuni minuti)…"):
                    res = voce.installa()
                (st.success if res["ok"] else st.error)(res["messaggio"])


# ---------------------------------------------------------------- 4/5. Skill
def sez_skill():
    st.subheader("Skill installate")
    skills = fonte.skill_elenco()
    if not skills:
        st.info("Nessuna skill trovata. Installane una dallo Store o da un URL GitHub qui sotto.")
    f1, f2 = st.columns([3, 1])
    cerca = f1.text_input("Cerca", placeholder="nome o parola della descrizione…", label_visibility="collapsed", key="cerca_skill")
    origini = sorted({s.get("origine", "installata") for s in skills})
    scelta = f2.selectbox("Origine", ["tutte"] + origini, label_visibility="collapsed", key="orig_skill")
    skills = [s for s in skills if (scelta == "tutte" or s.get("origine", "installata") == scelta)
              and (not cerca.strip() or cerca.strip().lower() in (s["nome"] + " " + s["descrizione"]).lower())]
    st.caption(f"{len(skills)} skill")
    cols = st.columns(3)
    for i, s in enumerate(skills):
        with cols[i % 3]:
            st.markdown(theme.card_skill(s["nome"], s["descrizione"], s.get("origine", "installata")), unsafe_allow_html=True)
            if st.button("Usa", key=f"usa_{s.get('origine', 'i')}_{s['cartella']}", use_container_width=True):
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
    colonne = st.columns(3)
    for i, v in enumerate(voci):
        with colonne[i % 3]:
            st.markdown(theme.card_store(v), unsafe_allow_html=True)
            if not v["installata"] and st.button("Installa", key=f"inst_{v['id']}", use_container_width=True):
                with st.spinner(f"Installo {v['titolo']}…"):
                    res = fonte.installa_catalogo(v["id"])
                (st.success if res["ok"] else st.error)(res["messaggio"])
                if res["ok"]:
                    st.rerun()


# ---------------------------------------------------------------- Centro (porta d'ingresso)
def sez_centro():
    righe = fonte.sessioni()
    lav = sum(r["stato"] == "al lavoro" for r in righe)
    p = fonte.processi()
    leads = fonte.clienti()
    skills = fonte.skill_elenco()
    k = fonte.costi(30)
    tessere = [
        ("agenti", "Agenti", f"{lav} al lavoro", "chi fa cosa, quali pagine apre, cosa ne ricava"),
        ("guardian", "Guardian", "manager", "parlagli a testo o a voce: coordina gli altri agenti"),
        ("consumi", "Consumi e sistema", f"{p['n']} processi", f"CPU Claude {p['cpu']:.1f}% · RAM {p['ram_mb']:.0f} MB"),
        ("costi", "Costi e output", f"${k['oggi']:.2f} oggi", f"mese ${k['mese']:.2f} · proiezione ${k['proiezione_mese']:.2f}"),
        ("clienti", "Clienti", str(len(leads)), f"{sum(1 for x in leads if x['stato'] == 'da visitare')} da visitare"),
        ("siti", "Siti demo", str(len(leads)), "un sito dimostrativo per ogni cliente"),
        ("skill", "Skill", str(len(skills)), "cosa puoi usare e quando"),
        ("store", "Store", "catalogo", "skill verificate da installare"),
    ]
    st.caption("Scegli uno spazio. Ogni sezione si apre con una transizione e si aggiorna da sola.")
    cols = st.columns(4)
    for i, (chiave, titolo, valore, sub) in enumerate(tessere):
        with cols[i % 4]:
            st.markdown(theme.tessera(titolo, valore, sub), unsafe_allow_html=True)
            st.button("Apri", key=f"apri_{chiave}", on_click=vai, args=(chiave,), use_container_width=True)


# ---------------------------------------------------------------- Siti demo
def sez_siti():
    st.subheader("Siti demo dei clienti")
    st.caption("Per ogni cliente trovato genero un sito dimostrativo da mostrare di persona. Non invento nulla sull'attività: "
               "orari, contatti e prezzi restano «da inserire». Nessuna richiesta di rete, nessuno script.")
    leads = fonte.clienti()
    if not leads:
        st.info("Nessun cliente ancora: quando gli agenti trovano i lead (cartella leads/) compaiono qui.")
        return
    c1, c2 = st.columns([3, 1])
    nome = c1.selectbox("Cliente", [x["azienda"] for x in leads], key="siti_sel")
    tema = c2.selectbox("Stile", list(siti_demo.TEMI), key="siti_tema")
    c = next(x for x in leads if x["azienda"] == nome)
    pagina = siti_demo.genera_sito(c["azienda"], c.get("categoria", ""), c.get("zona", ""), tema, c.get("opportunita", ""))
    html_frame(pagina, height=720, scrolling=True)
    b1, b2 = st.columns(2)
    b1.download_button("Scarica questo sito (HTML)", data=pagina, file_name=f"{siti_demo.slug_file(nome)}.html", mime="text/html",
                       use_container_width=True)
    if b2.button("Salva tutti in siti-demo/", use_container_width=True, disabled=fonte.nome.startswith("DEMO")):
        cartella = config.LEADS_DIR.parent / "siti-demo"
        cartella.mkdir(parents=True, exist_ok=True)
        for x in leads:
            (cartella / f"{siti_demo.slug_file(x['azienda'])}.html").write_text(
                siti_demo.genera_sito(x["azienda"], x.get("categoria", ""), x.get("zona", ""), tema, x.get("opportunita", "")), encoding="utf-8")
        st.success(f"{len(leads)} siti salvati in {cartella}")


SEZ = {"centro": sez_centro, "consumi": sez_consumi, "costi": sez_costi, "agenti": sez_agenti, "clienti": sez_clienti,
       "siti": sez_siti, "guardian": sez_guardian, "skill": sez_skill, "store": sez_store}
with st.container(key=f"sez_{sezione}"):
    SEZ[sezione]()
