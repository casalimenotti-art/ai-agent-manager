# 05 — Clienti, pipeline e visite di persona

## Obiettivo
Il titolare deve **vedere i clienti trovati**, capire in 10 secondi perché ognuno è adatto, e andarci a parlare di persona con una scheda pronta. Ogni lead ha una prova verificabile; ciò che non è verificato si vede come tale.

## Pipeline (stati e passaggi)
`trovato` → `verificato` (prova riaperta da `verificatore-fonti`) → `scheda pronta` → `da visitare` → `visitato` → `interessato` / `richiamare` / `no` → `preventivo` → `cliente`.
Oggi la dashboard gestisce lo stato della visita (`clienti.py`: da visitare, visitato, interessato, richiamare, no). Estendi la sequenza **senza rompere** i dati esistenti (migrazione che mappa i vecchi valori).

## Archiviazione
Oggi: CSV in `leads/` (scritti dagli agenti) + `visite.json` + foto in `~/.claude/guardian/foto/<slug>/`. Con più agenti che scrivono insieme il JSON rischia conflitti. **Proposta da valutare** (annotare in `docs/decisioni.md`): un database **SQLite locale** `guardian.db` (modalità WAL) con tabelle `lead`, `visita`, `foto`, `evento_pipeline`; i CSV restano il **formato di importazione** degli agenti (importazione idempotente per `slug`) e di esportazione. Vantaggi: transazioni, query veloci, storico degli stati. Passa a SQLite solo se i test di migrazione e concorrenza passano.

## Campi di un lead
`azienda`, `categoria`, `zona`, `contatto_pubblico`, `prova` (una frase), `fonte_url`, `adattamento` (1–5), `motivo`, `da_verificare`, `opportunita_principale`, `stato`, `note`, `consenso_foto`, `aggiornato`, più (nuovi) `problemi[]` con prova e URL, `offerta_proposta`, `prossimo_passo`, `data_prossimo_passo`.
Punteggio di adattamento: spiegabile. Mostra **perché** (nessun sito +2, non adatto al telefono +1, solo telefono per prenotare +1, recensioni senza risposta +1, giorni deboli rilevati +1; sottrai se "non verificato"). I pesi stanno in `config` e si possono cambiare.

## Pannello Clienti
- **KPI**: lead, da visitare, interessati, appuntamenti, tasso di conversione per categoria.
- **Imbuto** con conteggi e percentuali tra una fase e l'altra.
- **Tabella** con filtri (categoria, fit minimo, stato, zona, "solo verificati"), ordinamento, ricerca testuale; colonne: fit, attività, categoria, zona, stato, opportunità/prova, fonte.
- **Scheda cliente**: prova con link (solo http/https), problemi con prova, offerta proposta, contatto pubblico, **scheda di visita** dell'agente (testo trattato come dato, mai HTML), cronologia degli stati, note, foto.
- **Percorso di visita** (facoltativo): ordina i lead "da visitare" per zona e orario di apertura pubblicato, e propone un giro; senza mappe esterne (nessuna richiesta di rete). Se il titolare vuole una mappa, valuta un servizio e chiedi prima: invia posizioni all'esterno.
- **Foto**: caricamento solo con la casella "il titolare mi ha dato il permesso" spuntata; formati JPG/PNG/WEBP verificati dal contenuto, max 10 MB, max 40 per cliente; nessuna persona riconoscibile senza consenso. I render 3D sono una fase successiva: per ora solo archiviazione.

## Agenti coinvolti (catena)
`cacciatore-clienti` (per categoria, in parallelo) → `analista-presenza-online` (audit con prove) → `scopritore-problemi` (opportunità) → `verificatore-fonti` (a campione, declassa i lead deboli) → `compilatore-schede-visita` (solo fit ≥ 4) → il titolare visita → `analista-risultati` (con `esiti.csv`) → `ottimizzatore-prompt` migliora i criteri.
Il manager Guardian lancia la catena e mostra in dashboard lo stato di ogni passo per ogni categoria.

## Cosa cercare (problemi risolvibili da noi)
Nessun sito o sito inutilizzabile da telefono; nessuna prenotazione online; solo telefono; orari incoerenti tra scheda e sito; recensioni senza risposta; giorni o fasce deboli; nessun modo di raccogliere contatti con consenso; menu non aggiornato; nessun WhatsApp. Esempio di prodotto: **chatbot per ristoranti** (prenotazioni, domande frequenti, **offerte nei giorni deboli proposte al titolare e da lui approvate**). Il richiamo di clienti passati si fa solo con consenso (opt-in). Specifica in `prodotti/chatbot-ristoranti.md` (da scrivere): cosa vende, cosa fa, cosa serve per partire, rischi, domande per un consulente privacy. Prezzo "da definire" finché il titolare non decide.

## Limiti e onestà
- La ricerca web funziona solo dove il web è libero (il PC del titolare): le sessioni cloud non riescono ad aprire molti siti. Un lead non verificato resta con punteggio ≤ 2.
- Nessuna promessa di guadagno: la dashboard mostra ciò che è dimostrato (lead verificati, appuntamenti, preventivi, incassi inseriti a mano).
- Privacy: dati di attività, non di persone private; niente dati sensibili; il contatto è solo quello pubblicato dall'attività; ogni outreach è una bozza approvata dal titolare.

## Test
Importazione CSV con `;` e `,`, BOM, colonne mancanti, duplicati (vince il fit migliore), adattamento sporco; migrazione stati; concorrenza (due scrittori); foto (consenso, magic bytes, dimensione, path traversal); HTML dei campi agente escapato; link `javascript:`/`data:` neutralizzati; filtri; imbuto con conteggi corretti. (Parte già coperta da `tests/test_clienti.py`.)
