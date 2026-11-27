# GUARDIAN — decisioni (la più recente in alto; non cancellare le vecchie, segnarle come superate)

- **2026-11-27 · HQ Ondata 1: stanze come dati** (tabella `stanze` + `projects.stanza_id`, migrazione 005), con un responsabile per stanza; gli agenti della stanza sono quelli del responsabile. Un task senza progetto va nella stanza del suo responsabile. Solo l'admin modifica le stanze. Scelta rispetto a `users.ruolo`: una quarta stanza o un cambio di responsabile non richiedono codice.
- **2026-11-27 · HQ: stanza espansa nella vista centrale** (non una pagina): Guardian resta visibile in forma compatta e cliccarlo riporta all'orbita; URL `?s=`. Kanban: il trascinamento cambia lo stato reale, con un'alternativa accessibile da tastiera ("Sposta in…").

- **2026-11-27 · Command Center web: opzione B** (titolare): nuova SPA `guardian-web/` (Vite + React + TypeScript + supabase-js) con lo stesso Supabase e le stesse RLS, nessun backend nuovo, hosting statico gratuito. Streamlit resta come riserva e per planner AI e registrazione dei PC finché non c'è parità. Supera la decisione "Streamlit resta" per l'interfaccia principale.
- **2026-11-27 · Web: logica pura duplicata in TypeScript** (stati, report e prossime azioni, assegnazione, metriche) con test vitest specchio di quelli Python; da spostare in RPC SQL se le due versioni divergono.
- **2026-11-27 · Web: pannelli non modali da 1280 px in su** (il centro resta cliccabile e si sposta), modali su schermi piccoli; la barra di Guardian sta sopra ai pannelli.
- **2026-11-27 · Web: dati di esempio solo con `VITE_DEMO=1`** (DemoSource in memoria, banner visibile), mai di default; senza configurazione l'app mostra un errore esplicito.
- **2026-11-27 · Web: palette dei grafici** = palette di riferimento della skill dataviz (dark), validata con lo script sul fondo `#0f1622` (5/5 PASS); i colori di stato restano riservati.

- **2026-11-27 · M7: smoke test con gli stessi passi testati su SQLite** (`scripts/smoke_supabase.py`): password chiesta a terminale e mai salvata; crea un solo task di prova e lo cancella (stato `cancelled`).

- **2026-11-27 · M6: il piano è solo una proposta** (tabella `plans`, stato bozza): diventa task solo con «Conferma». La conferma controlla prima i titoli già aperti (niente piani creati a metà); i task senza dipendenze nascono `ready`, gli altri `planned`; i task con azioni esterne generano subito una richiesta di approvazione.
- **2026-11-27 · M6: report e prossime azioni senza AI**: calcolati dal database con regole fisse (approvazioni, agenti in errore o in attesa di permesso, utilizzo ≥ 90%, task falliti/bloccati/fermi > 24 h, ready senza agente, planned con dipendenze completate).
- **2026-11-27 · M6: assegnazione deterministica**: capacità in comune, poi carico minore; esclusi agenti non disponibili, in errore o offline. Il modello può suggerire solo agenti esistenti.

- **2026-11-27 · M5: un solo adattatore, OpenAI-compatibile, con la libreria standard** (FreeLLMAPI, OpenRouter, Ollama, OpenAI). Nessun provider Anthropic dedicato finché non c'è una chiave; nessuna nuova dipendenza. Fallback solo su errori ritentabili (429, 5xx, rete, JSON non valido); 401/403 fermano la catena. Le tracce delle chiamate non contengono mai prompt né risposte.

- **2026-11-27 · M4: ogni handoff con task crea una voce di memoria `ripresa`** (fonte `handoff #id`): la memoria del task contiene sempre l'ultimo punto da cui ripartire.
- **2026-11-27 · M4: memoria con fonte obbligatoria**; le voci si "superano" (`superseded_by`), non si cancellano. Ricerca: full-text italiano in Postgres, parole chiave in SQLite.
- **2026-11-27 · M4: evento `handoff` se c'è un destinatario, altrimenti `checkpoint`**; il destinatario riceve una notifica (trigger in Postgres). `bridge_checkpoint` ha una sola firma (quella di 001 viene eliminata in 004) per evitare ambiguità in PostgREST.
- **2026-11-27 · M4: export .md solo tra `<!-- guardian:export -->` e `<!-- /guardian:export -->`**: il testo scritto a mano nei file GUARDIAN_* non viene mai sovrascritto.

- **2026-11-27 · M2: stato agente = ultimo stato riferito dal bridge**, ma `unknown` se il bridge non lo aggiorna da più di 180 s (`models.stato_agente`), e `unknown` se l'hook non produce eventi da 30 min (Claude potrebbe essere chiuso). Codex: solo `idle` dopo un turno (notify non ha un evento di inizio).
- **2026-11-27 · M2: un PC gestisce solo gli agenti del proprio collaboratore** (controllo nelle RPC `bridge_agent_*`); `claim` solo su task `ready` del proprio collaboratore e non assegnati ad altri.
- **2026-11-27 · M2: rimosso `guardian/core/adapters.py`** (solo interfacce non usate), sostituito dai collector reali in `bridge/collectors/`.
- **2026-11-27 · M2: hook Claude nello stesso formato della plancia locale** (`~/.claude/guardian/events.jsonl`): le due cose convivono senza duplicati.

- **2026-11-27 · M1: livello di accesso in `users.accesso` (admin/member)**, non in `ruolo`: `ruolo` contiene già la mansione (registro/persone.json).
- **2026-11-27 · M1: regole nel DB**: titoli unici tra i task aperti dello stesso progetto, al massimo un task `running` per agente, `ready`/`running` solo con dipendenze completate; un'approvazione aperta porta il task in `needs_approval`, l'approvazione lo riporta a `ready` (o `planned`), il rifiuto a `blocked`. In Postgres sono trigger e indici, in SQLite lo stesso comportamento in Python.
- **2026-11-27 · M1: notifiche per utente** (una riga per destinatario, così "letta" è personale), create dai trigger in Postgres.
- **2026-11-27 · M1: stati v1 convertiti** (in attesa→ready, in corso→running, bloccato→blocked, completato→completed); `_valida_task` accetta ancora i nomi v1 come alias.

- **2026-11-27 · Provider AI: nessuno per ora** (titolare). Planner e router vengono preparati e testati con un server finto; nell'UI il planner risulta "non disponibile". `GUARDIAN_ALLOW_PAID=false` di default.
- **2026-11-27 · Log agenti: metadati + prompt troncati a 200 caratteri** (titolare), passati dal filtro segreti, mai output dei tool. Disattivabile per PC (`GUARDIAN_SHARE_PROMPTS=0`).
- **2026-11-27 · Commit + push a ogni milestone** su `claude/gallant-sagan-fwncjr` (titolare). Niente PR né force push.
- **2026-11-27 · Pacchetto `guardian/`** al posto di `guardian_hub/` (rinominato prima di qualsiasi deploy): core (dominio, archivi), ui (una pagina per modulo), poi planner e providers.
- **2026-11-27 · Nessun backend separato**: Supabase (Postgres + Auth + RLS + RPC) fa da backend; la logica LLM gira nel processo Streamlit, separata dalla UI.
- **2026-11-27 · Streamlit resta**; il "realtime" è polling (10–20 s) dichiarato come tale.
- **2026-11-27 · PC ≠ agente**: la presenza del PC viene dagli heartbeat; lo stato dell'agente solo da eventi reali (hook, notify, comandi). Senza eventi: `unknown`.
- **2026-11-27 · Hub nuovo partendo da main** (titolare): `dashboard/` e la PR #2 non si toccano; gli hook Claude esistenti si riusano dal bridge.
- **2026-11-27 · Bridge**: solo HTTPS in uscita, token per PC salvato come hash, RPC `SECURITY DEFINER`; nessuna esecuzione di comandi remoti.
- **2026-11-27 · Voce locale senza token**: il servizio `voce` ascolta solo su 127.0.0.1 e accetta solo le origini dell'HQ (`GUARDIAN_HQ_ORIGINI`); nessun token da copiare nel browser. Solo trascrizione: non esegue comandi né salva l'audio. Se manca, l'HQ usa il riconoscimento del browser.
- **2026-11-27 · Realtime senza `devices`** (migrazione 007): i messaggi Realtime portano la riga intera, quindi `devices.token_hash` arriverebbe ai browser. I PC si aggiornano con il ricaricamento completo. La presenza nell'HQ usa Supabase Presence (in memoria, nulla nel DB).
- **2026-11-27 · Aggiornamenti ottimistici**: il kanban sposta subito la scheda; se il database rifiuta (vincoli), torna com'era e lo dice. I vincoli restano nel DB, non nel browser.
- **2026-11-27 · Vendite e amministrazione nel DB condiviso** (migrazione 008): solo azienda o codice del lead, mai persone, telefoni o email (il DB li rifiuta); ogni scadenza e ogni costo vuole una fonte. La fonte unica dei clienti resta il CSV dei lead. Guardian non contatta nessuno.
