# Prompt autonomo di Claude: Guardian HQ diventa la dashboard più bella mai vista

Si attiva da solo il 28/11 alle 04:52, dopo il reset delle 5 ore, con `/loop`. Il titolare dorme o lavora: **decidi tu**, non aspettare il suo ok per le scelte tecniche e di design. Fermati solo davanti a ✋ (soldi, account, segreti, invii esterni, dipendenze pesanti).
Il titolare ha detto: "non c'è problema se raggiungi il limite settimanale". Quindi lavora finché c'è utilizzo. Prima che finisca, salva sempre lo stato (passo F).

## 0. Dove e cosa
- **Cartella**: `C:\Users\casal\hq-worktree`, branch locale `hq-locale`, che punta a `origin/claude/gallant-sagan-fwncjr`.
  **Push**: `git push origin hq-locale:claude/gallant-sagan-fwncjr`. Il push ripubblica https://guardian-nexo.pages.dev (Cloudflare Pages, 1-2 minuti).
- **App**: `guardian-web/` (React 18, Vite, TS, Supabase). Bridge: `bridge/`. Migrazioni: `supabase/migrations/` (se ne aggiungi una, deve contenere i `grant ... to authenticated` e mai permessi alle tabelle per `anon`).
- **Da leggere a ogni avvio**, con grep per cercare invece di aprire file interi:
  - `prompts/GUARDIAN_HQ_ATLAS_3D.md` (il cervello 3D);
  - `prompts/GUARDIAN_HQ_CONTINUA.md` (stato e backlog delle funzioni);
  - `prompts/GUARDIAN_HQ_MASTER_V3.md` (visione);
  - `guardian-web/ROADMAP.md`;
  - `guardian-web/VOLTO-STILE.md`.
- **Riferimento visivo**: `C:\Users\casal\OneDrive\Desktop\atlas-view-3.jpg`. Aprilo con Read e guardalo davvero all'inizio di ogni fase visiva. Non va mai copiato nel repo.

## 1. La richiesta del titolare (le sue parole, da rispettare tutte)
"Il sito più bello che abbia mai visto. Utilizza quell'esempio. Deve essere **reattivo, vivo, bello da vedere, facile da leggere, da comprendere**, ma ogni cosa deve avere **la sua funzionalità**. Devo poter **leggere statistiche**. **Le tendine all'inizio nascoste.** Rendilo tipo **3D**."

Tradotto in criteri verificabili:
| Criterio | Come si verifica |
|---|---|
| Bello e vivo | Il cervello 3D ruota, gli impulsi scorrono, gli eventi live si accendono; atmosfera del riferimento. Screenshot affiancato al riferimento: deve reggere il confronto |
| Reattivo | Interazioni sotto i 100 ms, 30 fps sulla Intel Iris del titolare, nessun salto di layout (CLS), caricamento iniziale sotto i 2,5 s |
| Facile da leggere | Un solo messaggio principale per schermata, gerarchia chiara, testi brevi in italiano semplice, contrasto AA, font leggibili (minimo 14 px) |
| Ogni cosa funziona | Nessun bottone finto. Ogni elemento fa qualcosa o va tolto. Gli stati vuoti spiegano cosa fare ("Collega un PC") |
| Statistiche | Pagina e riquadri con dati veri dal database (vedi §4) |
| Tendine nascoste | Pannelli laterali, menu e dettagli chiusi all'avvio; si aprono con un clic e ricordano lo stato |
| 3D | Il cervello di `GUARDIAN_HQ_ATLAS_3D.md`, come sfondo vivo del Centro |

## 2. Skill e strumenti (usali davvero)
- **Design**: `ui-ux-pro-max`, con la ricerca nei suoi dati di stili, palette, tipografia e grafici, poi `frontend-design` e `design-system`. Per i grafici `dataviz`, che va caricato PRIMA di scrivere codice per un grafico.
- **Qualità**: `core-web-vitals`, `accessibility`, `web-design-guidelines`. Per i test a schermo `playwright-cli` e Claude in Chrome.
- **Processo**: `superpowers:writing-plans` per il piano iniziale, `superpowers:test-driven-development` per la logica, `superpowers:systematic-debugging` sui bug, `superpowers:verification-before-completion` prima di dire "fatto".
- **Skill mancanti**: se a una fase manca una competenza (per esempio animazioni 3D in canvas o grafici), usa `find-skills`.
  - Puoi installare solo skill con licenza chiara, più di 1.000 stelle e mantenute, dopo un controllo con l'agente `curatore-skill`.
  - Controlla che il nome non sia già usato in `~/.claude/skills`.
  - Annota tutto in `docs/skill-migliori.md`.
- **Ricerca nel codice**: usa sempre Grep e Glob invece di leggere file interi (token-efficiency).
- **Agenti**: usa `web-designer` per il codice della web app. Puoi lanciarne fino a 2 in parallelo **solo su file diversi** e dichiarati nel brief. Ogni brief deve contenere: file consentiti, criteri di §1, verifica richiesta, "commit, fetch, rebase, push" e risposta in massimo 6 righe. Dopo ogni agente **verifichi tu a schermo**.

## 3. Prima azione: il piano (al posto della Plan mode, perché il titolare non può approvare)
1. Controlla con `git status` se ci sono modifiche a metà dell'ondata 3 interrotta (`atlas.ts`, `atlas.test.ts`, ecc.). Se sono incomplete scartale con `git checkout -- <file>`, se sono utili tienile.
2. Fai un inventario veloce con grep e glob: pannelli in `src/ui/panels/`, componenti in `src/ui/`, stato in `src/state.tsx`, dati in `src/data/`.
3. Scrivi `guardian-web/PIANO-NOTTE.md` con le fasi di §5. Per ogni fase indica file, criterio di "fatto" e rischi. Fai il commit. Questo è il piano: poi eseguilo senza aspettare.

## 4. Statistiche da mostrare (solo dati veri; se un dato non c'è, uno stato vuoto che lo spiega)
- **Agenti**: attivi e fermi per stanza, ore di lavoro per agente al giorno e alla settimana, errori.
- **Task**: aperti, in corso, completati per giorno (grafico a barre su 14 giorni), tempo medio di completamento, bloccati.
- **Approvazioni**: in attesa, approvate e rifiutate, tempo medio di risposta.
- **Vendite**: pipeline per fase (funnel), valore aperto, tasso di vittoria; dalla migrazione 008.
- **Amministrazione**: scadenze dei prossimi 30 giorni, costi del mese per categoria.
- **Utilizzo di Claude**: 5 ore e settimana, da `usage.json` tramite bridge se esiste, altrimenti "non collegato".
- **Formato**: riquadri numerici grandi in alto, grafici sotto (con la skill `dataviz`), confronto con la settimana prima ("+12%"), dettagli in un pannello che si apre.

## 5. Fasi (in ordine; ognuna chiusa da verifica, commit e push)
**A. Cervello 3D**: le ondate 1-3 di `GUARDIAN_HQ_ATLAS_3D.md`. Motore 3D in Canvas 2D (proiezione, rotazione, profondità, sprite di glow precalcolati, polvere neurale, nucleo ad anelli), poi dati veri, poi impulsi e stati. È lo sfondo del Centro.

**B. Struttura e leggibilità ("tendine nascoste")**:
- All'avvio si vedono solo il cervello 3D, una riga di stato in alto (Guardian, PC collegati, approvazioni) e la barra della chat/voce in basso.
- La barra laterale è compatta con icone e tooltip, e si allarga al passaggio del mouse o con un clic.
- Pannelli e dettagli sono **chiusi** e si aprono come cassetti morbidi da destra; Esc li chiude; lo stato aperto/chiuso è salvato in `guardian.pref`.
- I riquadri delle stanze sono compatti e si espandono con un clic.
- Riduci il testo, togli i doppioni, unifica i bottoni.

**C. Statistiche**: pagina "Statistiche" e riquadri come in §4, con grafici leggeri in SVG fatti a mano, senza dipendenze, oppure una libreria piccola solo dopo una valutazione ✋.

**D. Vita e reattività**:
- Animazioni di ingresso brevi (150-250 ms) solo su transform e opacity.
- Feedback immediato a ogni clic, skeleton nei caricamenti, notifiche live discrete, aggiornamenti ottimistici.
- Il cervello reagisce alla voce: si accende quando Guardian parla, l'iride si apre quando ascolta.

**E. Interazione 3D, telefono e parete**: trascinamento, zoom, volo verso le stanze, tooltip, filtri. Su telefono la versione leggera con il tocco. Modalità parete a tutto schermo.

**F. Rifinitura finale**: confronto con il riferimento, controllo `accessibility` e `core-web-vitals`, pulizia del codice inutilizzato, aggiornamento di `ROADMAP.md`.

## 6. Verifica (obbligatoria a ogni fase)
1. `npm run build`, poi `npx vitest run`. Se mancano, aggiungi test per la logica pura.
2. Push, poi aspetta la build di Cloudflare (controlla il nome del file `assets/index-*.js` che cambia), poi apri https://guardian-nexo.pages.dev in Chrome. Il titolare è loggato nel suo Chrome, nella scheda del gruppo Claude.
3. Screenshot a 1440 px e a 390 px (iframe largo 390 o finestra ridotta). Console senza errori. Misura gli fps con requestAnimationFrame per 3 secondi.
4. Confronta lo screenshot con il riferimento e con i criteri di §1. Se una cosa è brutta o illeggibile, correggila prima di passare oltre.
5. Riga di registro: `python registro/scrivi.py --chi menotti --agente claude-code "<fase>: ..." --file ... --esito fatto`, poi commit e push.

## 7. Regole fisse
- Nessun segreto nel repo o nel browser. La anon key va solo nelle variabili di Cloudflare, già impostate. Mai usare la service_role.
- Non toccare la configurazione di Supabase, Cloudflare o GitHub senza ✋, a parte le migrazioni con i GRANT corretti.
- Nessun dato inventato presentato come vero: la polvere decorativa va dichiarata come tale nel riepilogo accessibile.
- Non scaricare né installare pacchetti npm pesanti senza ✋ (soglia: più di 50 KB gzip).
- `git reset --hard` e altri comandi distruttivi sono bloccati: scarta i file uno per uno con `git checkout -- <file>`.

## 8. Fine sessione o utilizzo quasi finito
- Se la settimana è oltre il 98%, o le 5 ore oltre il 97%: chiudi il lavoro in corso (commit e push anche se incompleto, con "WIP" nel messaggio) e aggiorna `guardian-web/ROADMAP.md` e `PIANO-NOTTE.md` con "dove sono arrivato e cosa resta".
- Poi scrivi al titolare un riepilogo in 8 righe con 2 screenshot, inviati con SendUserFile.
- Se un PC amico è online e la settimana è oltre il 60%, apri un passaggio per il suo Codex (vedi `GUARDIAN_HQ_CONTINUA.md` §4).
