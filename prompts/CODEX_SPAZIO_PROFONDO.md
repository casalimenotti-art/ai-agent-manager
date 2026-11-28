# Prompt per Codex: Guardian HQ diventa "spazio profondo"

Lingua di lavoro e dei testi: italiano semplice. Lavora da solo fino alla fine; fermati solo nei casi della sezione 7.

## 1. Obiettivo (le parole del titolare)
"Come entro nella dashboard devo vedere **esclusivamente sfondo nero opaco, profondo, come uno spazio profondo**. Tutto quello che vedo, il cervello e i dati, devono sembrare **delle stelle nello spazio**, visibili a prima vista. Anche i tasti dove cliccare devono avere **quel colore bianchino delle stelle, luminoso, ma che non dà fastidio all'occhio**. Libera ancora spazio."

Risultato atteso: al primo caricamento del Centro si vedono SOLO
1. il nero profondo;
2. il cervello 3D (Atlas) fatto di stelle;
3. i dati principali come piccole stelle con etichetta (non come card);
4. una riga di stato sottilissima in alto e la barra della chat in basso, entrambe quasi trasparenti.
Tutto il resto (card delle stanze, prossime azioni, flotta, task, pannelli) è nascosto in tendine/cassetti che si aprono con un clic e si chiudono con Esc.

## 2. Contesto (già deciso, non rimetterlo in discussione)
- Cartella di lavoro: la radice di questo repository (worktree `hq-codex`, branch locale `codex-spazio`). App in `guardian-web/` (React 18 + Vite + TypeScript, Supabase). `node_modules` è già presente.
- Il cervello 3D è in `guardian-web/src/ui/Atlas.tsx` (disegno su Canvas 2D: `disegna`, `disegnaVita`, `sprite`, `punto`, `geometria`) e `guardian-web/src/logic/atlas.ts` (funzioni pure: `conProfondita`, `proietta`, `polvere`, `COLORI_ATLAS`, `filtraGrafo`, `vistaStanza`). Ruota da solo (90 s/giro), si trascina, zoom con la rotellina, 30 fps max, qualità adattiva. NON riscrivere il motore: cambia colori, alpha, dimensioni e composizione.
- Centro: `guardian-web/src/ui/CommandCenter.tsx` (sezione `.hero` con il pannello "Guardian", i KPI in una tendina `numeriAperti` già chiusa all'avvio, poi `OrbitaStanze` e le sezioni). Guscio: `guardian-web/src/ui/Shell.tsx` (header, rail laterale, dock della chat). Stili: `guardian-web/src/styles/app.css` e `guardian-web/src/styles/volto.css` (classe `.con-volto`). Preferenze utente in `localStorage['guardian.pref']` tramite `leggiPreferenze`/`salvaPreferenze` in `guardian-web/src/state.tsx`.
- L'Atlas evita il pannello del Centro leggendo il rettangolo di `.hero > div:last-child` (`leggiPannello`) e usa `zonaLibera`. Se togli o sposti quel pannello, aggiorna `leggiPannello` e la lista `OCCUPATO` di conseguenza, così il cervello si centra nello schermo.
- Se nelle tue skill ci sono `ui-ux-pro-max`, `frontend-design`, `accessibility`, `web-design-guidelines`, `core-web-vitals`: usale per le scelte visive e per il controllo finale.

## 3. Direzione visiva (specifiche misurabili)
**Fondo**
- Colore unico `#000000` (accettato fino a `#02030a`). Togli griglie, vignette, gradienti radiali blu e il bagliore di fondo in `disegna` (oggi `createRadialGradient` con `rgba(60,90,170,…)`). Al massimo una nebbia lontanissima con alpha ≤ 0.03.
- Aggiungi un campo di stelle lontane fisse (200-400 puntini da 0.5-1 px, alpha 0.15-0.5) che ruota 5 volte più lento del cervello: dà profondità. Deve stare nello stesso canvas e nello stesso ciclo di disegno (niente secondo requestAnimationFrame).

**Stelle (cervello e dati)**
- Palette "luce di stella": bianco `#F2F6FF` per nucleo e testi; per le stanze solo una tinta leggera, quasi bianca: Sviluppo `#CDEFFF`, Vendite `#FFE7C2`, Amministrazione `#E4DCFF`. Aggiorna `COLORI_ATLAS` di conseguenza; gli stati restano riconoscibili ma desaturati (bloccato `#FFB4A8`, serve OK `#FFC8E6`).
- Ogni nodo è una stella: punto centrale piccolo e nitido + alone morbido dello sprite. Aggiungi un **luccichio** lento (scintillio dell'alpha ±15%, periodo 2-5 s, fase diversa per stella da `hash01(id)`); fermo con `prefers-reduced-motion`.
- Le linee ("nervi") diventano filamenti quasi invisibili: alpha 0.04-0.12, bianco-azzurro. La polvere neurale resta, più fine (puntini 0.5-1.4 px).
- Il nucleo Guardian è la stella più luminosa, con gli anelli di puntini più tenui (alpha massimo 0.35).

**Dati come stelle**
- I 4 numeri del Centro (agenti al lavoro, task in esecuzione, approvazioni in attesa, completati oggi) non sono più card: diventano 4 "stelle-dato" vicino al nucleo, numero grande in bianco stella (font 28-34 px, peso 300-400) con etichetta piccola sotto (12-13 px, maiuscolo spaziato, alpha 0.6). Sono pulsanti veri (DOM sopra il canvas, non disegnati nel canvas) e aprono lo stesso pannello di oggi (`apri({ p: 'agenti' })`, ecc.).
- Il testo di stato di Guardian ("Coordino 1 agente…") resta, una riga sola, piccolo, sotto il nucleo o nella riga di stato.
- Il pulsante "Conversazione" resta, ma con lo stile dei tasti stella (sotto).

**Tasti e testi**
- Tasti "stella": sfondo trasparente o `rgba(242,246,255,0.04)`, bordo 1 px `rgba(242,246,255,0.22)`, testo `#F2F6FF` alpha 0.9, raggio 999 px, alone `box-shadow: 0 0 14px rgba(220,232,255,0.14)`. Hover: alone 0.28 e bordo 0.4, transizione 150 ms solo su opacity/box-shadow. Focus visibile: outline 2 px `#F2F6FF`. Il tasto principale (Conversazione, Invia) può avere sfondo `rgba(242,246,255,0.92)` con testo `#05070d`.
- Niente ciano saturo, niente gradienti colorati sui bottoni, niente vetro opaco grigio: i pannelli aperti sono `rgba(4,6,12,0.82)` con bordo `rgba(242,246,255,0.10)`.
- Contrasto minimo AA (4.5:1 per testi < 18 px). Testo minimo 12 px, corpo 14 px.

## 4. Liberare spazio (struttura)
1. Pannello `.hero` grande: eliminato. Al suo posto le stelle-dato e una riga di stato.
2. Header: altezza ridotta (≤ 48 px), sfondo trasparente, solo logo "GUARDIAN" sottile, campanella, avatar. Indicatori tecnici (Database ms, Live/Dati locali, Cerca Ctrl K) dentro un menu o come puntini con tooltip.
3. Rail laterale: icone sole a alpha 0.55 senza etichette (tooltip al passaggio), si allarga con hover o clic. Sul telefono resta la barra in basso, stessi colori.
4. Filtri dell'Atlas (Tutti/stanze/Solo attivi): un solo tasto stella "Filtri" che apre il gruppo.
5. Tutto quello che oggi sta sotto il primo schermo (OrbitaStanze, Prossime azioni, Flotta agenti, Task attivi, ecc.): in un cassetto "Dettagli" che si apre dal basso o da destra, chiuso all'avvio, stato salvato in `guardian.pref` (nuova chiave `dettagliAperti`, default false). Nessuna funzione va persa: si cambia solo dove sta.
6. Barra della chat in basso: più sottile (≤ 52 px), sfondo `rgba(4,6,12,0.6)`, bordo stella.

## 5. Vincoli
- NESSUNA nuova dipendenza npm. NESSUNA modifica a `supabase/`, `bridge/`, file `.env*`, configurazione Cloudflare o GitHub.
- Non toccare la logica dei dati (`src/data/`), né il significato dei test esistenti: puoi aggiornare test che controllano colori o testi cambiati, e aggiungere test per le funzioni pure nuove (luccichio, stelle lontane).
- Prestazioni: restano 30 fps, un solo ciclo di disegno, niente `filter`/`shadowBlur` nel canvas a ogni fotogramma, sprite precalcolati.
- Accessibilità: ogni elemento cliccabile ha nome accessibile; il riepilogo `sr-only` dell'Atlas resta e dice che stelle lontane e polvere sono decorative; Esc chiude cassetti e tendine.
- Nessun dato inventato presentato come vero.
- Modifiche mirate: niente riscritture di file interi quando basta cambiare blocchi.

## 6. Verifica (obbligatoria prima di dire fatto)
Dalla cartella `guardian-web/`:
1. `npx vitest run` → 0 fallimenti.
2. `npm run build` → nessun errore TypeScript.
3. Se puoi aprire un browser: `VITE_DEMO=1` in `guardian-web/.env.local` (già presente, ignorato da git), `npx vite --port 5180`, accesso con «menotti», controlla 1440 px e 390 px: primo schermo = nero + cervello di stelle + stelle-dato + riga di stato + chat, nessuna card visibile, nessuno scroll orizzontale, console senza errori, attributo `data-atlas-fps` dell'elemento `.atlas-sfondo` ≥ 25.
4. Commit sul branch locale `codex-spazio` con messaggi chiari (uno per blocco: colori/stelle, dati come stelle, spazio liberato). **Non fare push**: il lavoro lo controlla Claude prima della pubblicazione.
5. Scrivi `guardian-web/RAPPORTO-CODEX.md` (massimo 15 righe): cosa hai cambiato, file toccati, esito dei comandi, fps misurati se li hai, cosa non sei riuscito a fare e perché. Includilo nell'ultimo commit.

## 7. Fermati e scrivi nel rapporto, senza procedere, se
- serve una dipendenza nuova o un cambio a database/configurazione;
- i test falliscono per motivi che non riguardano il tuo lavoro;
- una richiesta di questo prompt rompe una funzione esistente e non vedi un modo sicuro per mantenerla.
