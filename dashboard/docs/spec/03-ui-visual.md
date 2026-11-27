# 03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)

Obiettivo: la dashboard più bella **e** più utile possibile. Bella perché il titolare la guarda ore; utile perché ogni pixel risponde a una domanda. Se una decorazione non serve a leggere un dato, toglila.

## 1. Linguaggio visivo
- **Atmosfera**: nero-blu profondo (`#080A12`), pannelli `#0D1020`, linee `#1C2340`, testo `#E8F1FF` e secondario `#8B97B3` (contrasto verificato).
- **Colori dei dati** (validati con `validate_palette.js`, daltonismo incluso): serie 1 ciano `#00AED1`, serie 2 arancio `#FF5F45`. Se servono più serie, **valida il nuovo set** con lo script prima di usarlo (la skill `dataviz` lo spiega) e non superare 4–5 colori. I colori di decorazione (ciano acceso `#00F0FF`, magenta `#FF2BD6`, **giallo acido `#FCEE0A` riservato agli allarmi**) non codificano mai un dato.
- **Forme**: angoli tagliati (`clip-path`), parentesi HUD ai bordi dei pannelli, linee sottili a 1 px, griglia di fondo a bassa opacità, scanline appena percettibili, glow limitato (box-shadow sobrio). Niente ombre grigie generiche e niente gradienti decorativi senza funzione.
- **Tipografia**: monospace di sistema (nessun font esterno: zero richieste di rete). Scala: 12 / 14 / 16 / 20 / 28 / 44 px. Numeri con `font-variant-numeric: tabular-nums` così non ballano mentre cambiano.
- **Movimento**: un solo **momento orchestrato** al caricamento (il logo con un breve glitch, ~0,9 s). Tutto il resto è **movimento che informa**: il numero che sale fino al nuovo valore (150–250 ms), la barra che si allunga, il punto che entra nel grafico e fa scorrere la serie, il flash di 300 ms quando una soglia viene superata. Vietati: rimbalzi, entrate "slide-up" su ogni sezione, hover animato su tutte le card.
- **Rispetta `prefers-reduced-motion`**: spegne glitch, count-up, scorrimento morbido (i grafici si aggiornano ma senza interpolazione).
- **Stati**: vuoto ("Nessun agente in esecuzione. Avvia il manager."), caricamento (scheletro con la stessa forma del contenuto, mai uno spinner a pagina intera), errore (cosa è successo + cosa fare), **dato vecchio** (badge "ferma da 14 s" e pannello attenuato).
- **Microcopy** in italiano, frasi attive e corte, nomi stabili: se un'azione si chiama "Approva", il messaggio dopo dice "Approvato".

## 2. Struttura (wireframe)
```
┌ GUARDIAN ▌ claude code // control room ───── ● live 1,0 s ── [10m|1h|5h|24h|7d] ── ⏸ ┐
│ ┌─ CONSUMI ─────────────────────────────────────────────────────────┐ ┌─ MANAGER ──┐ │
│ │  SETTIMANA  ▁▂▃▃▄▅▅▆▆▇▇  37%  reset gio 09:00  proiez. 71%       │ │ Guardian   │ │
│ │  ════════════════════════●··········· (linea centrale, spessa)   │ │ ● coordina │ │
│ │  5 ORE      ▂▄▅▃▆▇▅▃▄▆   62%  reset 14:20 (1h12)  burn 0,6 $/h  │ │ 4 agenti   │ │
│ │  ───────────────●······· (linea sotto, sincronizzata)            │ │ [parla]    │ │
│ └──────────────────────────────────────────────────────────────────┘ └────────────┘ │
│ ┌ token/s ┐ ┌ azioni/min ┐ ┌ agenti attivi ┐ ┌ cache hit ┐ ┌ CPU Claude ┐ ┌ spesa oggi ┐ │
│ ┌─ AGENTI (corsie nel tempo) ───────────────┐ ┌─ FEED EVENTI ──────────────────────┐ │
│ │ guardian    ▓▓▓░░▓▓▓▓▓▓░░░░               │ │ 14:02:11 cacciatore → WebSearch     │ │
│ │ cacciatore  ░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓             │ │ 14:02:09 analista-presenza → Read   │ │
│ │ analista…   ░░░░░░▓▓▓▓▓░░░░               │ │ 14:02:03 ⏳ serve approvazione: …   │ │
│ └───────────────────────────────────────────┘ └─────────────────────────────────────┘ │
│ CLIENTI ▸ 42 lead · 11 da visitare · 3 interessati    COSTI ▸ oggi $1,9 · mese $38    │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
Tab: **Live** (la schermata sopra, è la prima), Agenti (dettaglio), Clienti, Costi, Guardian (chat col manager), Skill, Store, Sistema. Su schermi stretti (≤ 700 px) i pannelli si impilano e le due linee dei consumi restano una sopra l'altra.

## 3. Il pannello Consumi (il cuore)
- **Linea centrale = utilizzo settimanale**: spessa (3 px), area sotto al 10 %, asse 0–100 % (se calibrato) o UC. Marker verticale del reset e tratteggio della **proiezione** fino al reset.
- **Subito sotto = utilizzo della finestra di 5 ore**: stessa larghezza, asse tempo sincronizzato con il livello di zoom scelto, linea 2 px, proiezione a fine blocco, fascia per le soglie.
- Entrambe le linee mostrano in alto a destra: valore attuale, **ora di reset**, tempo rimasto, etichetta di provenienza (`misurato` / `calibrato` / `stimato`) e l'età del dato.
- **Crosshair sincronizzato**: passando il mouse su una linea compare la guida verticale su entrambe e un tooltip con ora, UC, token, modello più usato in quell'intervallo e agente attivo.
- **Intervalli**: 10 min (1 s per punto), 1 h (10 s), 5 h (10 s), 24 h (1 min), 7 d (1 min→1 h). Pulsante pausa che congela il grafico (i dati continuano ad arrivare in memoria).
- **Eventi sulla linea**: puntini per "inizio blocco", "soglia superata", "agente avviato", "approvazione richiesta": cliccandoli si apre il dettaglio.
- **Legenda sempre presente** quando ci sono ≥ 2 serie, e valori in testo (non solo colore).

## 4. Pannello Agenti
- **Corsie nel tempo (swimlane)**: una riga per agente, segmenti pieni quando lavora (colore per tipo di stato), vuoti quando è fermo; asse tempo condiviso con i grafici. Click su un segmento = dettaglio.
- **Card agente**: nome, ruolo, stato (`lavora` / `fermo` / `bloccato` / `aspetta approvazione` / `finito`), compito corrente (in una riga), strumento attuale, da quanto tempo, chi l'ha avviato (con link all'agente padre), UC e token dell'agente, file prodotti (`leads/…`, `audit/…`), ultimo messaggio.
- **Albero di avvio**: manager → agenti → sotto-agenti, con tempo di vita.
- **Drawer di dettaglio**: cronologia strumenti con orari, durate, errori ripetuti; "perché è bloccato".
- Dettagli del modello dati e del manager: vedi `04`.

## 5. Pannello Clienti e Costi
- Clienti: imbuto (trovati → verificati → visitati → interessati → appuntamenti), tabella con filtri, scheda con foto (solo con consenso), nota e prossimo passo. Dettagli in `05`.
- Costi: spesa giornaliera, per progetto/modello, burn rate, heatmap, margine. Esistono già: rifiniscili e uniscili alla serie live.

## 5b. Pannello Guardian (chat col manager)
Finestra di conversazione con l'agente manager; ogni risposta mostra gli agenti che ha avviato (con link alle card), le richieste di approvazione aperte (con pulsanti Approva / Rifiuta) e i costi della richiesta. Tasto microfono: usa la dettatura di Claude Code o, in futuro, il riconoscimento vocale locale. Dettagli in `04`.

## 6. Tecnologia: decidi con una misura, non a sensazione
Il titolare vuole **tempo reale vero** ("salgono e scendono"). Streamlit ricarica porzioni di pagina; a 1–2 Hz può sfarfallare o costare CPU. Procedi così:
1. **Spike A (Streamlit)**: due indicatori e il grafico dei consumi in un `st.fragment(run_every=1)` con Altair/SVG; misura latenza (dal campione alla pixel visibile), sfarfallio (cambi di layout), CPU del server e del browser su 5 minuti.
2. **Spike B (front-end leggero)**: pagina statica con **uPlot** (o Apache ECharts) che riceve punti da **SSE/WebSocket** servito da un piccolo server (FastAPI o simile) sopra la stessa interfaccia `Fonte`; incorporabile in Streamlit con un componente HTML oppure come pagina separata a cui Streamlit linka.
3. **Criteri** (da misurare, in `docs/decisioni.md`): latenza p95 ≤ 1,5 s; nessun salto di layout; CPU totale (server + browser) < 8 % di un core a 1 Hz; avvio con `avvia.bat` invariato; test verdi; nessuna dipendenza non verificata.
4. **Decisione**: se A rispetta i criteri, resta A. Altrimenti passa a B **solo per i pannelli live** (Consumi, Agenti, Feed), lasciando il resto in Streamlit. Nessuna riscrittura totale.
5. Librerie da valutare (verificane licenza e peso prima): uPlot, Apache ECharts, Chart.js con plugin streaming, lightweight-charts, Tremor, componenti Streamlit già esistenti. Privilegia ciò che si può **includere nel repo** senza CDN (no richieste di rete a runtime).

## 5c. Prestazioni, accessibilità, mobile
- Budget: primo paint < 1 s a freddo; aggiornamento di un pannello < 50 ms lato browser; nessun ricalcolo di tutta la pagina a ogni tick.
- Contrasto minimo 4,5:1 per il testo, 3:1 per i grafici; focus da tastiera visibile; tasti rapidi (`1–5` intervalli, `p` pausa, `g` apre Guardian).
- Funziona a 390 px senza scroll orizzontale; tabelle larghe con scroll interno.
- Nessun contenuto solo-colore. Ogni grafico ha una tabella equivalente apribile ("vedi i dati").
- Nessuna richiesta di rete a runtime (font, CDN): tutto locale.

## 6b. Procedura di verifica visiva
1. Playwright a 1400 px e 390 px; 1× ritagliato per le iterazioni, 2× solo a fine.
2. Con `tests/gen_jsonl.py` genera 24 ore di dati finti con un'impennata e una pausa, e controlla: linee sincronizzate, proiezione corretta, soglie, stato "dato vecchio" fermando il campionatore.
3. Controlla `prefers-reduced-motion` (emulazione) e il contrasto con lo script dei colori.
4. Registra i numeri misurati (latenza, CPU, FPS) nel report: senza numeri, il lavoro non è "fatto".
