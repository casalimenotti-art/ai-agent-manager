# 07 — Esempi online e riferimenti (con provenienza)

Il titolare vuole che si trovino **tutti gli esempi online** di interfacce simili e che la dashboard sia "il più figa possibile". Qui c'è ciò che è già stato trovato (con quanto è **verificato**) e il lavoro di ricerca da fare, con regole per non sprecare token.

## 1. Già trovato (ricerca precedente)
Letti direttamente dalle pagine:
- **ccusage** — github.com/ryoppippi/ccusage. Report per giorno/mese/sessione/progetto, ripartizione per modello, esportazione JSON, cache write e cache read in colonne separate, comando `blocks` per le **finestre da 5 ore**, status line in beta, layout compatto su terminali stretti. *Da prendere*: definizione dei blocchi, colonne separate della cache.
- **Claude-Code-Usage-Monitor** — github.com/Maciek-roboblog/Claude-Code-Usage-Monitor. Monitor live con burn rate, previsione di esaurimento, barre di avanzamento; ogni numero con etichetta di provenienza (`official`, `local_estimate`, `experimental`, `unknown`); temi light/dark. Per il limite "custom" usa il 90° percentile degli ultimi 192 h. *Da prendere*: etichette di provenienza, previsione di esaurimento, percentile come limite di riserva.
- **opcode / claudia** — github.com/winfunc/opcode. Costi in tempo reale per modello, progetto e periodo; sessioni con timeline e checkpoint. *Da prendere*: timeline di sessione.
- **claude-top** — github.com/a2d2-dev/claude-top. TUI con 4 schede (Overview, Sessions, Daily, Monthly), aggiornamento ogni 10 s, grafico a contributi su 52 settimane, costo per messaggio. *Da prendere*: grafico a contributi, costo per messaggio.
- **claude-token-dashboard** — pypi.org/project/claude-token-dashboard. Dashboard browser con utilizzo a 5 ore e settimanale, burndown e feed live delle chiamate. *Da prendere*: burndown e feed.

Visti solo nei risultati di ricerca (**non verificati**, da aprire prima di usarli): `claude-view` (card live per sessione con costo, token e uso del contesto), `ClawView` (sessioni aggiornate via WebSocket), `Claudestat` (si aggancia agli hook per catturare ogni chiamata), `Cybercore CSS` (framework CSS cyberpunk con icone), il `theme.py` Streamlit di un Space su Hugging Face (CSS futuristico).

## 2. Da cercare (almeno altri 12, con URL letto davvero)
Cerca con `WebSearch`/`WebFetch` e scrivi `docs/design-research.md` (una riga per esempio: URL letto · cosa funziona · cosa prendi · licenza/marchio · cosa **non** copi):
1. **HUD e UI di Cyberpunk 2077**: articoli di analisi UI/UX, case study di design, interviste ai designer. Obiettivo: capire *principi* (gerarchia, angoli, linee, densità, colore d'allarme), non copiare risorse.
2. **Sci-fi / FUI** (interfacce fantascientifiche) e raccolte di HUD.
3. **Dashboard di osservabilità**: Grafana, Datadog, Linear, Vercel Analytics, Posthog (come presentano serie temporali live, soglie, annotazioni).
4. **Monitor di sistema** a terminale e web: btop, htop, glances, netdata (densità, sparkline, aggiornamento).
5. **Librerie per grafici in tempo reale**: uPlot, Apache ECharts, Chart.js (streaming), lightweight-charts, Tremor, Observable Plot — con licenza, peso, supporto al push.
6. **Componenti Streamlit** utili (grafici live, componenti HTML bidirezionali) e come altri hanno ottenuto aggiornamenti a 1 Hz.
7. **Dashboard di agenti AI**: Langfuse, Helicone, AgentOps, LangSmith (tracce, alberi di chiamata, timeline) — specialmente la visualizzazione dell'albero padre/figlio e delle corsie nel tempo.
8. **Palette e tipografia**: riferimenti di accessibilità (contrasto, daltonismo), da validare con lo script.
Regole di ricerca: **solo pagine realmente aperte**; se un sito non si apre, scrivi "non verificato" e non usarlo. Licenze: segna MIT/Apache/GPL/non commerciale; non incorporare nulla senza licenza chiara. Marchi: non copiare logo, font o grafiche di terzi.

## 3. Come usare la ricerca senza sprecare token
- Delega la ricerca a subagent su **Sonnet**, con un brief preciso ("trova 6 esempi di timeline di agenti; per ciascuno URL aperto, 3 righe, licenza") e risposta **max 400 parole**. Non caricare nel contesto principale le pagine intere.
- Una volta scritto `docs/design-research.md`, **non rifare la ricerca**: aggiorna solo se serve un tema nuovo.
- Dai risultati estrai al massimo 10 decisioni di design e scrivile in `docs/decisioni.md`.

## 4. Prezzi e consumo (riferimento verificato)
Tabella dei prezzi ufficiali usata da `config.PRICES` (verificata il 2026-11-26 sulla pagina prezzi di Claude): Sonnet 5.5 $2/$10 (lettura cache 0,05×), Opus 5.5 $4/$20 (0,05×), Haiku 4.5 $1/$5, Fable 5.2 $8/$40 (0,025×), Haiku 5.5 con tariffa lunga oltre 100.000 token di prompt. La scrittura in cache vale 1,25× l'input (5 minuti). Se la tabella cambia, aggiorna `config.py` e i test dei prezzi. Con un abbonamento a tariffa fissa le UC non sono ciò che si paga: servono come misura relativa e per la calibrazione.
