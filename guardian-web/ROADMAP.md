# Guardian HQ — roadmap a ondate

Memoria del ciclo continuo descritto in `prompts/GUARDIAN_HQ_MASTER_V3.md`. Ogni sessione aggiorna questo file.

| Ondata | Contenuto | Stato | Note / decisioni del titolare |
|---|---|---|---|
| 0 | Allineamento: inventario dei branch, passaggio di amico1, PR #2 | 🟡 in parte | Inventario fatto (27/11 sera). **Da decidere (titolare):** (a) cosa fare della PR #2 di Niko, cioè busto WebGL + plancia team: unirla o tenerla sul PC; (b) dare a Francesco (`salisfrancesco19-stack`) l'accesso al repo su GitHub, come chiede il passaggio `passaggi/20261127T1641-amico1.md` |
| 1 | **Tre stanze**: migrazione 005 `stanze` + `projects.stanza_id`, vista orbita, stanza espansa con nucleo compatto, kanban vero (trascina o "Sposta in…"), comandi "apri vendite"/"torna al centro", contesto della stanza in chat, palette, colori Accesa/Soft | ✅ fatto | Colori: **Accesa** (dal DB, predefinita) o **Soft** in Impostazioni; nomi dal DB (l'admin li cambia). E2E verdi, 4 larghezze |
| 2 | Conversazione vocale livello B (browser): modalità conversazione, VAD, frase per frase, barge-in, sottotitoli, comandi vocali, diagnostica | ✅ fatto | Voce: preferisce in automatico una voce italiana **locale** (es. «Microsoft Elsa»); serve Chrome o Edge |
| 3 | Voce livello A: servizio vocale locale del bridge (sherpa-onnx + Parakeet già sul PC) | ✅ fatto | Si attiva con `guardian_bridge.py voce` (serve il modello sul PC); l'HQ lo sceglie da solo, altrimenti usa il browser |
| 4 | Cervello sul PC (`guardian_richieste` / `guardian_risposte`, `claude -p` in sola risposta) | ✅ fatto | Si attiva con `guardian_bridge.py cervello` sul PC del titolare (usa il suo abbonamento) |
| 5 | Stanza Vendite completa (pipeline senza dati personali, bozze con approvazione) | 🟡 in parte | Pipeline fatta (migrazione 008, inserimento a mano). Manca l'import dal CSV dei lead: arriva quando il branch `codex/vendite` di Niko esiste |
| 6 | Smistamento del lavoro alle IA dalla conversazione | da fare | Modello di minaccia |
| 7 | Stanza Amministrazione (scadenze, documenti, costi manuali, calendario) | 🟡 in parte | Scadenze e costi con fonte fatti (migrazione 008). Mancano documenti e calendario (serve l'ok al connettore) |
| 8 | Mappa operativa, Realtime incrementale, aggiornamenti ottimistici, presence | ✅ fatto | Migrazione 007: i PC escono dal canale in diretta (non deve arrivare `token_hash` ai browser) |
| 9 | 3D e suoni (nucleo 3D o busto di Niko), modalità parete | da fare | Scelta del look 3D |
| 10 | PWA, notifiche push, briefing vocale del mattino | da fare | Ok alle notifiche |

## Idee (massimo 3 per sessione, concrete)
- Stanza: filtro "solo miei" e ordinamento per priorità dentro le colonne.
- Nucleo compatto: piccolo indicatore di quanti agenti sono al lavoro **in quella stanza**, oltre al totale.

## Registro delle ondate
- **27/11 · Ondate 5 e 7**: migrazione 008 (`vendite_pipeline`, `scadenze`, `costi`; fonte obbligatoria; il DB rifiuta email e
  telefoni con `senza_dati_personali()`; firma automatica; cancella solo l'admin), pannelli nelle stanze (`ui/StanzeLavoro.tsx`:
  pipeline a 6 fasi con cambio di fase, scadenze a 30 giorni con «Fatta», costi del mese per categoria), prossime azioni con le
  scadenze vicine o passate, domande «scadenze», «quanto spendiamo», «come va la pipeline». Test: vitest 21, E2E verdi (13 nuovi), CHECK 008 OK.
- **27/11 · Ondata 8**: `logic/live.ts` (i messaggi Realtime si applicano subito ai dati, poi riallineamento dopo 2,5 s),
  `ottimistico()` nello stato (kanban: la scheda si sposta subito e torna indietro se il DB rifiuta, con «modifica annullata»),
  Presence Supabase (chi è nell'HQ e in quale stanza, avatar nell'header; nulla salvato nel DB), pannello «Mappa operativa»
  (`logic/mappa.ts`: persone → agenti → task aperti → stanze, solo collegamenti reali, impulso sull'attività degli ultimi 2 min,
  elenco al posto del disegno sotto i 720 px). Migrazione 007: `devices` fuori dalla pubblicazione Realtime.
  Test: vitest 17, E2E verdi (7 controlli nuovi), CHECK 007 OK.
- **27/11 · Ondata 3**: `bridge/voce_locale.py` + comando `voce` (solo 127.0.0.1, solo le origini dell'HQ in `GUARDIAN_HQ_ORIGINI`,
  preflight Private-Network, `GET /stato`, `POST /trascrivi` WAV 16 kHz → sherpa-onnx Parakeet), web: `voce/wav.ts`,
  `LocaleTrascrittore` (VAD + pre-roll + WAV) scelto in automatico se il servizio è pronto, pill «Ascolto locale · privato».
  Test: pytest voce 5, vitest 14, E2E `e2e/voce-locale.mjs` (microfono finto di Chromium da file WAV → servizio reale con riconoscitore di prova) verde.
- **27/11 · Ondata 4**: migrazione 006 (richieste, risposte, battito; solo il PC dell'admin risponde; ognuno vede le sue domande),
  `bridge/cervello.py` + comando `cervello` (claude -p in plan, strumenti di scrittura vietati, risposta a frasi, segreti rimossi),
  SqliteStore allineato, web: stato «Cervello online/offline», domande aperte → cervello con contesto minimo, risposta a voce mentre arriva.
  Test: pytest 65 (con un finto claude), CHECK 006 OK, E2E verdi (cervello finto solo in demo).
- **27/11 · Ondata 2**: `guardian-web/src/voce/` (vad.ts testato, adattatori.ts, motore.ts), `ui/Conversazione.tsx`, `ui/useRispondi.ts`
  (chat e voce rispondono allo stesso modo), stati del nucleo «in ascolto» (livello reale del microfono) e «sta parlando»,
  diagnostica delle latenze. Comandi: «basta», «silenzio», «apri …», «approva …» (apre il pannello, non approva).
  Test: vitest 13, E2E tutti verdi (14 nuovi controlli con il microfono simulato solo nel test); bundle 84 KB gzip.
- **27/11 · Ondata 1**:
  - file: `supabase/migrations/005_stanze.sql`, `tests/pg/check_005.sql`, `guardian-web/src/logic/stanze.ts`,
    `guardian-web/src/ui/Stanze.tsx`, più modifiche a state, CommandCenter, Shell, intents, impostazioni e CSS;
  - test: vitest 7, E2E tutti verdi (16 nuovi controlli sulle stanze), `tests/pg/run.sh` CHECK 002–005 OK;
  - bundle: 79 KB gzip.
