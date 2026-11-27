# Guardian Web — piano, catalogo delle metriche, contratto dei controlli

Fonte: `prompts/GUARDIAN_COMMAND_CENTER_MASTER.md`. Decisione del titolare (27/11): **opzione B, web app React**, tutte le fasi.

## Skill lette e regola presa
- **dataviz**: prima la forma (spesso un numero, non un grafico); un solo asse Y; colore per entità in ordine fisso;
  palette validata con lo script (`validate_palette.js --mode dark --surface #0f1622`: 5/5 PASS con gli 8 colori in `tokens.css`);
  tooltip e vista tabellare per ogni grafico; testi nei colori del testo.
- **artifact-design / ui-ux-pro-max**: non disponibili in questa sessione (la seconda è sul PC del titolare). Applicati token, stati e AA a mano.
- **graphify**: non installato in questa sessione; l'analisi del repo viene dalle milestone M0–M7.

## Architettura
`src/types.ts` (schema del DB) · `src/logic/` (pura, testata con vitest: stati, report, assegnazione, metriche, intenti) ·
`src/data/` (`SupabaseSource` in produzione, `DemoSource` solo con `VITE_DEMO=1`) · `src/state.tsx` (dati, diretta/polling,
pannelli con URL `?p=&id=&f=`, conversazione) · `src/ui/` (Shell, CommandCenter, pannelli, grafici, voce).

## Catalogo delle metriche (ogni numero mostrato)
| Metrica | Definizione | Fonte | Aggiornamento | Se manca |
|---|---|---|---|---|
| Agenti al lavoro | `statoAgente ∈ {working, waiting, needs_approval}` | `agents` + `last_heartbeat` < 180 s | Realtime o polling 20 s | 0 / "nessun agente registrato" |
| Agenti con segnale | stato ≠ unknown/offline | `agents` | idem | 0 |
| PC online | `last_seen` < 120 s | `devices` | idem | 0 / "nessun PC" |
| Task in esecuzione / aperti / per stato | conteggi per stato | `tasks` | idem | 0 |
| Approvazioni in attesa | `status = richiesta` | `approvals` | idem | 0 |
| Completati oggi | eventi `task_completed` da mezzanotte locale | `activity_events` | idem | 0 |
| Errori 24 h | eventi con gravità `error`/`critical` nelle ultime 24 h | `activity_events` | idem | 0 |
| Tasso di completamento | completed / (completed+failed+cancelled), task chiusi negli ultimi 7 giorni | `tasks` | idem | "n.d." |
| Durata media | media ore tra `task_started` e `task_completed` dello stesso task | `activity_events` | idem | "n.d." |
| Attività per giorno (14 g) | eventi e completati per giorno | `activity_events` (ultimi 400) | idem | giorni a zero |
| Task aperti per agente | task non chiusi con `assigned_agent_id` | `tasks` | idem | "nessun agente" |
| Utilizzo 5 h / 7 g | `% used` letto dalla statusline di Claude Code | `agents.usage` (bridge) | dal bridge | non mostrato |
| Cervello online | battito del PC del titolare < 60 s | `guardian_cervello` | Realtime/polling | «Cervello offline · risposte dai dati» |
| Latenza DB | tempo di `select id from users limit 1` | ping ogni 30 s | 30 s | "non raggiungibile" |
| Riepilogo di una stanza (attivi, in corso, fermi, da approvare, completati) | conteggi sui task della stanza (progetto con `stanza_id`, oppure task senza progetto del responsabile della stanza) | `stanze`, `projects`, `tasks`, `approvals` | Realtime o polling | 0 / "stanze non configurate (migrazione 005)" |
| Agenti di una stanza | agenti il cui `user_id` è il responsabile della stanza | `agents`, `stanze.responsabile` | idem | "nessun agente collegato" |
| Ricavi, spese, clienti, workflow | **nessuna fonte reale** | — | — | **non mostrati** |

## Contratto dei controlli
| Controllo | Dove | Azione | Pannello / effetto | Dato (metodo `DataSource`) | Ok | Errore |
|---|---|---|---|---|---|---|
| Voci della rail (11) + Centro | rail | apre pannello / chiude | drawer `?p=` | lettura snapshot | pannello aperto | — |
| KPI (4) | centro | apre agenti, task attivi, approvazioni, statistiche | drawer | — | — | — |
| Prossima azione | centro | apre task/agente/approvazione collegati | drawer | — | — | — |
| Card agente | centro, Agenti | apre agente | drawer | `logAgente` | — | vuoto onesto |
| Riga task / approvazione / azienda | ovunque | apre dettaglio | drawer | — | — | "non trovato" |
| Salute (pillola) | header | apre Salute | drawer | `ping` | — | rosso + motivo |
| Cerca / Ctrl+K | header | palette comandi | modale | snapshot | apre voce | "nessun risultato" |
| Campanella | header | Notifiche | drawer | — | — | — |
| Esci | header | logout | login | `esci` | — | — |
| Indietro / Chiudi / Esc | drawer | traccia / chiude | — | — | focus restituito | — |
| Nuovo task (form) | Task | crea | toast | `creaTask` | "Task creato" | messaggio di vincolo |
| Filtri task / azienda | Task | filtra | — | — | — | vuoto |
| Salva (task) | Task | stato/priorità/agente/prossimo passo | toast + eventi | `modificaTask` | "Task aggiornato" | vincolo DB leggibile |
| Richiedi approvazione | Task, Approvazioni | form | toast, task → needs_approval | `richiediApprovazione` | "Richiesta registrata" | filtro segreti |
| Approva / Rifiuta | Approvazione | decisione | toast, notifica | `decidiApprovazione` | "Approvata"/"Rifiutata" | "già decisa" |
| Segna lette / riga notifica | Notifiche | read_at + apre ref | drawer | `segnaLetta` | — | — |
| Prendi in carico / Chiudi handoff | Handoff | stato handoff | toast | `prendiHandoff` / `chiudiHandoff` | — | "già preso" |
| Cerca / Salva memoria | Memoria | ricerca / inserimento | — | `memoria` / `aggiungiMemoria` | "Salvato" | fonte obbligatoria |
| Nuova azienda | Aziende | crea progetto | toast | `creaProgetto` | "Azienda creata" | nome duplicato |
| Disponibile / non disponibile | Agente | `agents.disponibile` | toast | `disponibilitaAgente` | — | permessi |
| Assegna task libero | Agente | `assigned_agent_id` | toast | `modificaTask` | "Task assegnato" | vincolo DB |
| Vista tabella / grafico | Statistiche | alterna | — | — | — | — |
| Invia (chat) / Invio | dock | router di intenti, può aprire un pannello | conversazione | snapshot | risposta con fonte | "non ho una risposta dai dati" |
| Conversazione / Nascondi | dock | mostra/nasconde la cronologia | — | — | — | — |
| Impostazioni voce/annunci | Impostazioni | localStorage | toast | — | "Preferenze salvate" | storage non disponibile: ignorato |
| Porta di una stanza (3) | orbita | apre la stanza (URL `?s=`), nucleo compatto | stanza espansa | snapshot | — | "stanza non trovata" |
| Indietro / nucleo compatto / Esc | stanza | torna all'orbita (Esc chiude prima un pannello aperto) | orbita | — | — | — |
| Trascina scheda / "Sposta in…" | kanban della stanza | stato reale del task (Da fare→ready, In corso→running, Fermi→blocked, Chiusi→completed) | toast | `modificaTask` | "Task #n → stato" | vincolo DB leggibile, la scheda resta |
| Titolo scheda | kanban | apre il task | drawer sopra la stanza | — | — | — |
| Chiedi a Guardian (stanza) | testata stanza | domanda con il contesto della stanza | conversazione | snapshot | risposta con fonte | — |
| Nuovo task (stanza) | testata stanza | apre il form | drawer Task | `creaTask` | "Task creato" | vincolo DB |
| Comandi "apri vendite / sviluppo / amministrazione", "torna al centro" | barra di Guardian | apre/chiude la stanza | stanza/orbita | — | "Apro la stanza …" | non riconosciuto → risposta normale |
| Colori stanze Accesa/Soft | Impostazioni | preferenza locale | colori | localStorage | toast | — |
| Conversazione (hero e dock) | centro, dock | avvia/termina la modalità conversazione (microfono, VAD, risposta a voce frase per frase) | barra dei sottotitoli | `useRispondi` | fase "Ti ascolto" | permesso negato / microfono assente: messaggio |
| Silenzio / Termina | barra conversazione | zittisce Guardian / chiude | — | motore | — | — |
| Voce: «basta», «silenzio», «apri …», «approva …», domande | conversazione | come la chat; «approva» apre solo il pannello | pannello/stanza | `useRispondi` | risposta parlata | "non ho una risposta dai dati" |
| Domanda aperta (chat o voce) con cervello online | dock / conversazione | va al cervello sul PC; risposta a frasi | conversazione | `chiediCervello` | risposta con fonte «cervello sul PC» | timeout 60 s: «forse il PC è spento» |
| Parlare sopra Guardian (barge-in) | conversazione | interrompe la voce e ascolta | — | livello reale del microfono | — | — |
| Ascolto locale e privato | barra conversazione | se il servizio `guardian_bridge.py voce` risponde su 127.0.0.1:8765 lo usa al posto del browser | pill «Ascolto locale · privato» | `LocaleTrascrittore` → `POST /trascrivi` | testo capito | servizio spento/non pronto: si usa il browser |

### Controlli disabilitati (con motivo)
| Controllo | Quando | Perché / cosa serve | Tooltip |
|---|---|---|---|
| Conversazione | browser senza riconoscimento o sintesi vocale | API non supportate (usare Chrome o Edge) | tooltip esplicativo |
| Microfono | browser senza `SpeechRecognition` | API non supportata | "Voce non disponibile: questo browser non supporta il riconoscimento vocale" |
| Voce (checkbox) | browser senza `speechSynthesis` | API non supportata | nota nel pannello |
| Invia | input vuoto | niente da inviare | — |
| Segna tutte come lette | nessuna non letta | — | — |
| Planner AI | sempre nel web | le chiavi provider non stanno nel browser | rimando al Guardian classico |
| Registra / revoca PC | nel web | il token va mostrato una sola volta in un contesto controllato | rimando al Guardian classico |
| Workflow | sempre | non esiste un motore di workflow | stato vuoto onesto |
| Chiedi modifiche / scadenza approvazioni | sempre | non esistono nel DB (serve una migrazione approvata) | nota nel pannello |

## Fasi
1–2 audit e decisione ✅ · 3 design system ✅ · 4 Command Center ✅ · 5 pannelli ✅ · 6 dati reali + realtime/polling ✅ ·
7 chat + intenti + Ctrl+K + voce ✅ · 8 statistiche ✅ · 9 test E2E e rifinitura ✅ (e2e/run.mjs: tutti i controlli, 390/768/1280/1920 px, axe senza violazioni serie, console pulita) · 10 guida di deploy ✅ (docs/guardian-web.md); messa online: azione del titolare.
Ciclo continuo (prompt v3): vedi `ROADMAP.md`. Ondata 1 (tre stanze) ✅.
