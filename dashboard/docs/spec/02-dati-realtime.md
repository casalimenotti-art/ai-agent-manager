# 02 — Livello dati in tempo reale (consumi, finestre, agenti)

Questa specifica definisce **da dove arrivano i numeri**, **come si calcolano** e **ogni quanto si aggiornano**. È la parte più importante: se i dati sono sbagliati, nessuna grafica li salva.

## 1. Fonti dei dati
| Fonte | Cosa dà | Latenza | Affidabilità |
|---|---|---|---|
| JSONL di Claude Code in `~/.claude/projects/**` (e `**/subagents/*.jsonl`) | messaggi, strumenti usati, `usage` (token in/out, cache read/write) per risposta, modello, `cwd`, `isSidechain`, timestamp | secondi (scritti a ogni risposta) | alta per i token, ma i messaggi vengono ripetuti: contare una volta per `message.id` (già fatto in `agenti._Stato`) |
| Hook di Guardian → `~/.claude/guardian/events.jsonl` | `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop` con `ts`, `session_id`, `cwd`, `tool` | sub-secondo | alta; è la fonte "immediata" dello stato lavoro/fermo |
| Eventi di subagent (da verificare nella documentazione degli hook: nomi come `SubagentStart` / `SubagentStop`) | nascita e fine di ogni agente, chi l'ha avviato | sub-secondo | **verifica i nomi esatti dei campi prima di usarli** |
| `psutil` | CPU/RAM per processo Claude e macchina | 1 s | alta |
| Uso del piano (% finestra 5 h e % settimanale) | quanto del limite è consumato | — | **vedi §4: non assumere che esista un'API** |
| Inserimento manuale / calibrazione | percentuale letta da `/usage` in un istante | manuale | usata per calibrare le stime |

Regola: se una fonte non è verificata nella documentazione ufficiale, **non basarci niente**; implementa la stima locale e segnala "stimato".

## 2. Architettura del campionatore
Oggi `Campionatore` (in `monitor.py`) calcola al volo a ogni richiesta della UI. Per il tempo reale serve un **campionatore in background**, uno solo per processo (singleton in `FonteLocale`, creato con `st.cache_resource`):
- Un thread demone `Sampler` gira ogni **1 secondo** e fa solo lavoro leggero: legge i byte nuovi dei file (offset per file, come `_Stato.aggiorna`), aggiorna i contatori, legge `psutil.cpu_percent`, calcola le velocità.
- Scrive in **buffer ad anello** (deque con `maxlen`) a più risoluzioni:
  - `t1s`: ultimi 10 minuti, 600 punti;
  - `t10s`: ultime 6 ore, 2.160 punti;
  - `t1m`: ultimi 7 giorni, 10.080 punti;
  - `t1h`: ultimi 90 giorni, 2.160 punti.
  I livelli superiori si ottengono **aggregando** quelli inferiori, mai rileggendo i file.
- Un punto è una tupla compatta: `(ts, unità_consumo, token_out, token_in, cache, tool_calls, cpu_claude, cpu_macchina, agenti_attivi)`. Niente dict per punto (memoria).
- Persistenza: ogni minuto scrive su disco uno snapshot (`~/.claude/guardian/serie.json`, o SQLite) così al riavvio il grafico non riparte vuoto. Alla ripartenza, ricostruisci dai JSONL le ultime 7 giorni **una volta** (con indice per file) e poi segui in incrementale.
- Memoria: tetto di 50 MB per i buffer; ruotare i file letti più vecchi di 8 giorni (come `AGENT_MAX_AGE_H` ma per i costi).
- Il thread non deve mai bloccare la UI né sollevare eccezioni: ogni errore va in un contatore `errori_sampler` mostrato nella tab Sistema.

Interfaccia `Fonte` (aggiungere, rimanendo compatibile con `FonteRemota`):
- `live(cursore: int | None) -> dict`: restituisce **solo i punti nuovi** dopo `cursore` per i livelli richiesti, più lo "snapshot" corrente. Con un cursore il payload è di pochi byte anche a 1 Hz, ed è già pronto per un agent HTTP remoto (long polling o SSE).
- `finestre() -> dict`: stato delle finestre 5 h e settimanale (vedi §3).
- `agenti_live(cursore) -> dict`: eventi e stato per agente (vedi `04`).

## 3. Definizioni esatte delle metriche
- **Unità di consumo (UC)** = costo di listino stimato in USD di una risposta (`agenti.costo`: input, output, cache read × moltiplicatore del modello, cache write × 1,25). È l'unica misura omogenea tra modelli diversi. Con un abbonamento non è ciò che si paga: serve per misurare consumo **relativo**.
- **Token/s** (output): token output nell'ultimo intervallo / secondi. Mostra anche input e cache separati (la cache read è quasi gratis ma conta nel contesto).
- **Burn rate** = UC nella finestra mobile degli ultimi 10 minuti, espresso in UC/ora. Mostra anche la media delle ultime 5 ore.
- **Cache hit ratio** = cache read / (cache read + input + cache write).
- **Azioni/min** = chiamate di strumenti per minuto (da hook o JSONL).
- **Agenti attivi** = agenti con evento negli ultimi `IDLE_THRESHOLD_S` e non terminati.
- **Finestra di 5 ore (blocco).** Algoritmo come i monitor che usano blocchi: il blocco inizia al primo evento dopo che il blocco precedente è finito (o dopo una pausa ≥ 5 h) e dura 5 ore. UC del blocco = somma delle UC degli eventi nel blocco. Mostra: UC consumata, tempo trascorso, tempo rimasto, **ora di reset prevista**, proiezione lineare a fine blocco (UC attuale + burn rate × tempo rimasto).
- **Settimana.** Finestra mobile di 7 giorni, **oppure** ancorata a un giorno/ora di reset inseriti dal titolare (da `/usage`). Stesse grandezze: UC, resto, proiezione al reset. Se il reset non è noto, finestra mobile e scritta "stima".
- **Percentuale di utilizzo** = `k × UC_finestra`, dove `k` è il **fattore di calibrazione** (§4). Senza calibrazione mostra solo UC e dillo ("calibra con /usage").
- **Soglie**: 60 % normale, 60–85 % attenzione, > 85 % critico. Il colore **non** è l'unico segnale: icona e testo ("Attenzione: 78 %, reset tra 1 h 12 min").

## 4. Uso del piano: cosa si può e non si può fare
Il titolare vuole vedere "l'utilizzo settimanale e, subito sotto, l'utilizzo delle 5 ore". Procedi così, in ordine:
1. **Verifica nella documentazione ufficiale** (usa l'agente `claude-code-guide` o le pagine su code.claude.com) se Claude Code espone la percentuale di utilizzo del piano in modo documentato: per esempio nei dati passati alla **status line**, o in un comando che restituisce testo/JSON. Annota in `docs/decisioni.md` cosa hai trovato con l'URL della pagina.
2. **Se esiste una fonte documentata**: scrivi un piccolo ponte (script di status line o hook) che salva la lettura in `~/.claude/guardian/uso-piano.json` con timestamp; implementa `UsoPianoUfficiale` che lo legge. Etichetta `misurato`.
3. **In ogni caso** implementa `UsoPianoStimato` dai JSONL (§3) con **calibrazione**: il titolare inserisce nella dashboard "ora `/usage` dice 37 % (5 h) e 21 % (settimana)"; si calcola `k = percentuale / UC_finestra_in_quel_momento`; si salva la serie di calibrazioni; il fattore usato è la mediana delle ultime 5 letture; si mostra l'incertezza (± in base alla dispersione). Etichetta `calibrato` e data dell'ultima calibrazione; oltre 24 h di età → "ricalibra".
4. **Vietato**: usare endpoint non documentati, leggere o riusare i token di accesso di Claude, fare scraping del sito. Se non c'è una fonte ufficiale, resta la stima calibrata.
5. `UsoPiano` è un'interfaccia con priorità `ufficiale > calibrato > solo UC`. La UI non sa quale dei tre sta usando, ma lo mostra nell'etichetta.

## 5. Cadenze di aggiornamento (livelli di tick)
| Elemento | Cadenza | Come |
|---|---|---|
| Contatori live (token/s, azioni/min, CPU, agenti attivi), linea consumi 5 h e settimana | **1–2 s** | `st.fragment(run_every=2)` o canale a push (vedi `03`) |
| Stato dettagliato degli agenti, feed eventi | **2 s** | idem, con cursore |
| Costi, per progetto/modello, heatmap | 10–30 s | fragment più lento |
| Clienti, pipeline | 30 s o al salvataggio | fragment lento |
| Ricostruzione completa dai file | solo all'avvio | una volta |
Budget: il campionatore + la UI aperta devono stare **sotto il 3 % di un core** su un PC normale con 20 sessioni recenti; misurarlo (§AC in `06`). Se `run_every=1` sfarfalla o costa troppo, 2 s è accettabile per tutto tranne i due indicatori "vivi", che passano al canale a push.

## 6. Schema degli eventi (hook)
`events.jsonl`, una riga per evento: `{"ts": float, "event": "PreToolUse|PostToolUse|UserPromptSubmit|Stop|SubagentStart|SubagentStop", "session_id": str, "agent": str|null, "parent": str|null, "cwd": str, "tool": str, "prompt": str(<=200)}`.
- Non registrare mai il contenuto degli strumenti (comandi, file): solo il nome (`guardian_hook.py` già lo fa).
- Aggiungere `agent`/`parent` **solo se** i campi esistono nei dati degli hook (verifica); altrimenti ricavali dai JSONL dei subagent (`.../subagents/agent-<id>.jsonl` e `parent_session`).
- Lettura: tail con offset, righe parziali ignorate, righe corrotte saltate (come oggi). Tetto di 400 KB riletti all'avvio.

## 7. Test del livello dati (obbligatori)
- **Generatore sintetico**: script `tests/gen_jsonl.py` che produce sessioni finte con timestamp controllati (per blocchi da 5 ore, pause, più modelli, subagent, messaggi duplicati). Orologio finto (`now` iniettabile) per non dipendere dal tempo reale.
- Casi: blocco che inizia dopo una pausa ≥ 5 h; due blocchi nella stessa giornata; evento esattamente a 5 h; settimana a cavallo di mezzanotte e del cambio ora legale; duplicati; file ruotato/ridotto; riga parziale; modello sconosciuto; cache a zero; dati futuri (orologio sbagliato).
- **Proprietà**: la somma delle UC dei punti a 1 s = UC calcolata da zero rileggendo i file (nessuna perdita, nessun doppio conteggio); la proiezione è monotona; la percentuale con `k` noto è esatta.
- **Carico**: 10.000 eventi in un secondo non fanno superare 50 ms per tick.
- **Non regressione**: i 88+ test esistenti restano verdi.
