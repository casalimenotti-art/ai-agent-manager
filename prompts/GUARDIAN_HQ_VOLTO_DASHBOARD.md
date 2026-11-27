# GUARDIAN HQ — IL VOLTO DI NEXO SENTINEL DENTRO LA DASHBOARD
### Prompt di implementazione per Claude Code · repo `casalimenotti-art/ai-agent-manager` · `guardian-web/` + `tools/volto3d/`

> Incolla questo prompt in Claude Code sul repository. Lavora **a fasi**. Alla fine di ognuna:
> 1. test verdi;
> 2. riga del registro;
> 3. commit e push;
> 4. aggiornamento di `guardian-web/ROADMAP.md`;
> 5. un messaggio breve in italiano semplice al titolare (Menotti, non tecnico).
>
> Dove trovi ✋ mostra gli screenshot al titolare e aspetta la sua scelta.

---

## 0. Obiettivo, decisioni già prese, regole

### 0.1 Cosa vuole il titolare
- Il volto del robot **NEXO Sentinel** è lo **sfondo vivo** dell'HQ:
  - parte dalla variante **A** (scura) di `tools/volto3d/concept/sentinel-A.png`;
  - deve essere **ancora più rovinato e realistico**;
  - la scena è **molto scura**;
  - dietro il volto c'è la parete di lamiere chiodate e arrugginite, quasi nera.
- Il volto è **dinamico**. **Non segue il cursore.** Si anima a ogni cosa reale che succede:
  - arriva una **richiesta** (chat, voce, palette): si "sveglia", l'occhio si accende, la testa si alza appena;
  - Guardian **pensa**: gli anelli dell'occhio ruotano, una scansione luminosa scorre;
  - Guardian **parla**: l'occhio e la griglia della bocca pulsano con la voce, piccoli cenni della testa;
  - Guardian **ascolta**: l'iride si apre e l'anello esterno segue il livello reale del microfono;
  - arriva un **evento** (task, approvazione, agente): un breve lampo dell'occhio;
  - il titolare lo **interrompe** parlando: l'occhio si abbassa in meno di 200 ms e torna in ascolto;
  - c'è un'**approvazione in attesa**: l'anello diventa ambra; **errore o offline**: sfarfallio rosso, poi occhio fioco;
  - **inattivo**: occhio al 15% circa, "respiro" lentissimo.
- Lo stile di tutta la dashboard si adatta: scuro, il volto protagonista, pannelli in vetro scuro sopra.

### 0.2 Decisione tecnica: "2.5D fotografico" (non 3D in tempo reale)
Il realismo dei render viene da Cycles (path tracing: minuti per immagine), impossibile in tempo reale su un PC normale o su un
telefono. Quindi:
1. In Blender si renderizzano **strati separati** del volto (occhio spento, luce dell'occhio, anelli, iride, bocca,
   profondità).
2. Nel browser un **piccolo shader WebGL2** li compone dal vivo:
   - accende e spegne la luce;
   - ruota gli anelli;
   - apre l'iride;
   - fa muovere leggermente la testa con la **parallasse da mappa di profondità**.

Risultato: qualità da render, pochi MB, gira ovunque. È l'approccio da usare, non three.js con texture cotte.

### 0.3 Regole che non si discutono
- **Originalità.** NEXO Sentinel è un design originale di NEXO. Non deve somigliare a BT-7274 né ad altri personaggi:
  niente nomi, sagome o dettagli riconoscibili. Non usare il nome "JARVIS".
- **Onestà.** Il volto mostra solo stati **reali**:
  - la `Fase` del motore vocale (`src/voce/motore.ts`);
  - `statoNucleo()` di `src/logic/guardian.ts`;
  - il flag `pensa` dello stato (`src/state.tsx`);
  - il livello reale del microfono (`--livello`, o `motore.stato.livello`);
  - gli eventi Realtime (`source.ascolta` → `applicaCambio` in `src/logic/live.ts`).

  Niente animazioni che fingono attività.
- **Repo** (`AGENTS.md`):
  - lavora su un branch `claude/*`;
  - a fine fase `python registro/scrivi.py --chi menotti --agente claude-code "…" --file … --esito fatto`, poi commit e push;
  - mai segreti, mai dati dei clienti, mai force push.
- **Niente regressioni.** Devono restare verdi `npm test`, `npm run e2e`, `npm run e2e:voce`, `python -m pytest -q tests`,
  `bash tests/pg/run.sh`.
- **Fallback.** Senza WebGL2, con `prefers-reduced-motion`, sul telefono o con il volto spento nelle Impostazioni: immagine
  ferma + bagliore CSS dell'occhio guidato dagli stessi stati.

### 0.4 Skill da usare (leggile davvero prima di scrivere codice)
| Skill | Per cosa |
|---|---|
| `superpowers:writing-plans` → `superpowers:executing-plans` | piano a passi e sua esecuzione |
| `superpowers:test-driven-development` | test prima di `stati.ts` e della mappatura |
| `superpowers:verification-before-completion` | non dichiarare finito nulla senza prova (test, screenshot) |
| `/mnt/skills/public/frontend-design/SKILL.md` (leggi il file) | direzione visiva, palette, tipografia, token, autocritica con screenshot; evita gli stili "generati" che elenca |
| `dataviz` | validatore della palette e del contrasto dei colori di stato sopra lo sfondo scuro |
| `tweenkit:animation-html` (facoltativa) | prototipo dei tempi delle animazioni del volto prima di scriverle nello shader |
| `run` | avviare l'app e guardarla davvero |
| `simplify`, poi `code-review` | pulizia e revisione a fine lavoro |

---

## 1. Volto ancora più rovinato (Blender, `tools/volto3d/costruisci.py`)

Blender c'è come modulo Python:
```
python3.13 -m venv .venv-blender && .venv-blender/bin/pip install bpy pillow numpy
```
Lo script costruisce già testa, materiali consumati, parete chiodata, luci e camera 16:9. **Partine, non ricominciare.**

Aggiungi alla variante A, con parametri ripetibili (seme fisso `7472`):
1. **Ammaccature vere nella geometria**:
   - modificatore Displace con texture di rumore a bassa frequenza sulle piastre (ampiezza 3–8 mm, suddivisione quanto basta);
   - 2–3 **crateri d'impatto** (deformazione sferica locale + vernice saltata attorno + graffi radiali).
2. **Usura più forte**:
   - scheggiature più grandi sugli spigoli;
   - graffi profondi che attraversano le piastre;
   - vernice sbiadita a chiazze;
   - **bruciature** scure e **colature d'olio** sotto le feritoie e la griglia;
   - **cordoni di saldatura** lungo 2 giunture.
3. **Dettagli del tempo**:
   - un **bullone mancante** con il foro arrugginito;
   - **vetro dell'occhio incrinato** (crepe come maschera di rugosità e normale, non opache);
   - stencil «NEXO SRL» ancora più consumato ma leggibile.
4. **Scena più scura**:
   - parete quasi nera;
   - luci più basse e radenti, così i rivetti fanno ombre lunghe;
   - vignettatura;
   - il blu dell'occhio diventa la luce principale sulla faccia.
5. Velocità: non usare `bmesh.ops` in ciclo su una mesh che cresce (era il collo di bottiglia: vedi come sono fatti i rivetti in
   `parete()`). Per le superfici grandi usa i materiali con `ao=False`.

✋ Render di controllo a 1600 px: il titolare conferma "più rovinato, sì".

---

## 2. Render a strati (`tools/volto3d/strati.py`)

Script nuovo che importa `costruisci.py`, costruisce la scena (variante A) e renderizza **dalla stessa camera**:

| File (`guardian-web/public/volto/`) | Come si ottiene | Uso nello shader |
|---|---|---|
| `base.webp` | occhio, anelli, nucleo e bocca spenti (emissione 0, luce dell'occhio 0) | immagine di fondo |
| `luce.webp` | (render con occhio acceso al 100%) − `base`, in lineare, poi codificato | **additivo**: bagliore e riflessi blu sulle piastre |
| `anelli.webp` | solo gli anelli emissivi su nero (gli altri oggetti come holdout) | ruotati nello spazio dell'ellisse dell'occhio |
| `iride.webp` | atlante di 8 ritagli dell'occhio (iride da chiusa ad aperta, shape key o rotazione delle lamelle) | flipbook con dissolvenza |
| `bocca.webp` | solo la griglia emissiva su nero | intensità con la voce |
| `profondita.webp` | passata Z normalizzata (vicino = chiaro), sfocata leggermente | parallasse |
| `meta.json` | centro dell'occhio in px, assi dell'ellisse dell'occhio proiettato, rettangolo del ritaglio dell'iride, dimensioni | allineamento degli strati |

- Due misure: **1920×1080** (desktop) e **960×540** (telefono e fallback).
- Budget: **≤ 2,5 MB** in tutto per il desktop e **≤ 0,8 MB** per il telefono.
- Formato WebP con qualità 82–88; `luce` può essere in mezza risoluzione.
- `tools/volto3d/verifica_strati.py` controlla:
  - presenza dei file;
  - dimensioni coerenti;
  - pesi nel budget;
  - `meta.json` valido;
  - che `base + luce` ricomponga il render acceso con errore medio < 3%.
- Annota la provenienza in `guardian-web/public/volto/LICENZE.md`: tutto generato da script, nessun asset esterno.

---

## 3. Componente `src/volto/`

- `VoltoSfondo.tsx`:
  - un `<canvas>` **fisso a tutto schermo dietro `.shell`** (z-index sotto l'interfaccia), `aria-hidden`, `pointer-events: none`;
  - caricato con `React.lazy` in un chunk separato;
  - carica gli strati con `createImageBitmap`;
  - mostra subito `base.webp` come `<img>` e passa al canvas quando è pronto.
- `shader.ts`, WebGL2, un solo fragment shader a schermo intero:
  - copertura tipo `object-fit: cover`, con l'occhio sempre visibile;
  - a desktop l'occhio sta a circa 58% della larghezza e 42% dell'altezza (lascia spazio ai pannelli a sinistra);
  - **parallasse**: `uv + (profondita − 0.5) × offset` per i micro-movimenti della testa, massimo circa 6 px;
  - colore finale = `base × esposizione + luce × intensitàOcchio × coloreOcchio + anelli(ruotati) × intensitàAnelli
    + iride(flipbook) + bocca × intensitàBocca`;
  - sfarfallio leggero dell'emissione (rumore lento, ampiezza 2–3%);
  - grana di pellicola fine;
  - vignettatura;
  - gradazione **molto scura** (esposizione circa 0,6–0,75; neri profondi ma non schiacciati).
- `uniform` aggiornati a ogni frame da `stati.ts`. Quando tutto è fermo (inattivo da più di 3 s), il rendering scende a circa
  15 fps; torna a 60 fps a ogni cambio di stato.
- Attributi di test sul contenitore: `data-volto-fase`, `data-volto-intensita` (arrotondato a 0,05),
  `data-volto-modalita="webgl|immagine"`.

---

## 4. Stati e animazione (`src/volto/stati.ts`, puro e testato)

Scrivi i test **prima**, con `superpowers:test-driven-development`.

```
type Ingressi = { fase: Fase; nucleo: StatoNucleo; pensa: boolean; livelloMic: number; ampiezzaVoce: number;
                  ultimaRichiesta: number | null; ultimoEvento: number | null; adesso: number }
type Uscite   = { intensitaOcchio; coloreOcchio: [r,g,b]; intensitaAnelli; velocitaAnelli; aperturaIride; intensitaBocca;
                  parallasse: [x,y]; flash }
statoVolto(ingressi, precedente, dt) → Uscite   // con smorzamento (molle) tranne il flash e lo spegnimento da barge-in
```

| Situazione | Ingressi reali | Uscite |
|---|---|---|
| Inattivo | `fase=spento`, nucleo `idle`/`working` | occhio 0,15; anelli 0,05 lenti; iride 0,3; parallasse = respiro di 7 s di ±1 px in verticale |
| Richiesta ricevuta | `ultimaRichiesta` cambiata (invio chat, frase finita, comando dalla palette) | flash 120 ms; occhio sale a 0,7 in 300 ms; la testa "si alza" (parallasse y −4 px, poi ritorno in 1,2 s) |
| Pensa | `pensa` oppure `fase=elaborazione` | anelli 0,8 con velocità alta in versi opposti; scansione luminosa; occhio 0,6 |
| Parla | `fase=parla` | occhio 0,55 + 0,45 × ampiezza; bocca = ampiezza; piccoli cenni (parallasse y ±1,5 px a ritmo delle frasi) |
| Ascolta | `fase=ascolto` | iride 1 (aperta); anello esterno = livello del microfono; occhio 0,45 |
| Evento nuovo | `ultimoEvento` cambiato (Realtime) | flash breve 80 ms, intensità 0,3 sopra lo stato attuale |
| Barge-in | passaggio `parla → ascolto` per interruzione | occhio e bocca a zero in < 200 ms, poi stato "ascolta" |
| Approvazione | nucleo `approval` | colore dell'anello ambra `#FBBF24`, pulsazione lenta |
| Errore / offline | nucleo `error` / `offline` | sfarfallio rosso `#F87171` per 600 ms, poi occhio 0,08 fisso |

Collegamenti da aggiungere (minimi, senza cambiare la logica esistente):
- `ultimaRichiesta`: in `useRispondi` (`src/ui/useRispondi.ts`) a ogni domanda, e in `motore` quando arriva il testo finale.
  Esponilo con un piccolo store o con un evento `window` già usato nel progetto (es. `guardian:chiedi`).
- `ultimoEvento`: in `src/state.tsx`, quando `applicaCambio` applica un cambio di `activity_events`.
- `ampiezzaVoce`: con `ParlatoreWeb` (Web Speech) usa gli eventi `boundary` per un inviluppo e dichiara in Diagnostica voce
  "ampiezza stimata". Quando esisterà la sintesi locale, un `AnalyserNode` sull'audio.
- **Niente inseguimento del cursore**: non registrare listener di `mousemove`.

---

## 5. Stile della dashboard (usa `frontend-design`)

Prima un **piano di stile** breve in `guardian-web/VOLTO-STILE.md`: 4–6 colori nominati con esadecimale, i caratteri e il loro
ruolo, il layout con un wireframe ASCII, i principi. Rivedilo contro la skill (niente tratti "generati") e poi applicalo.
- **Sfondo molto scuro**: il volto è l'unico elemento luminoso; il blu dell'occhio è l'accento di Guardian (allinea
  `--accent` in `src/styles/tokens.css`).
- **Pannelli in vetro scuro**:
  - `backdrop-filter: blur(14–20px) saturate(130%)`, fondo `rgba` molto scuro, bordo di 1 px appena più chiaro, nessun glow sul testo;
  - al massimo 5 superfici sfocate visibili insieme;
  - fallback opaco con `prefers-reduced-transparency` o senza supporto.
- **Layout del centro** (`src/ui/CommandCenter.tsx`):
  - il nucleo SVG grande sparisce quando il volto è attivo (il volto è il nucleo);
  - testo di stato e numeri in una colonna di vetro a sinistra;
  - l'occhio resta libero;
  - le stanze sotto, in vetro.
  - Drawer, palette, stanze e parete funzionano come oggi, con gli stessi URL.
- **Contrasto AA**: scrim scuro dietro ogni blocco di testo. Verifica con axe e con il validatore di `dataviz` sopra le zone
  più chiare del volto.
- **Impostazioni**: "Volto 3D: acceso / solo immagine / spento" e "Vetro: forte / leggero / spento", salvati in localStorage
  con try/catch come le altre preferenze (`leggiPreferenze` / `salvaPreferenze` in `src/state.tsx`).
- **Modalità parete** (`src/ui/Parete.tsx`): il volto al centro, più grande, numeri ai lati.
- ✋ Due screenshot a 1440 e 1920 px (vetro forte e leggero); il titolare sceglie.

---

## 6. Prestazioni e fallback

- Bundle iniziale: massimo +5 KB gzip; il volto vive in un chunk separato.
- Pausa del rendering con `document.hidden` e quando un drawer largo copre l'occhio.
- DPR massimo 1,5; texture del telefono sotto i 900 px di larghezza.
- Telefono e `prefers-reduced-motion`: `base` 960 px + un `div` con `radial-gradient` sull'occhio. L'intensità segue
  `statoVolto()` con transizioni CSS di sola opacità.
- Senza WebGL2 o in caso di errore del contesto (`webglcontextlost`): passa a "immagine" senza errori in console.
- Obiettivo: CPU a riposo < 3% su un portatile medio; nessun calo dei 60 fps quando si aprono i drawer.

---

## 7. Test

- **vitest**:
  - `statoVolto()` per ogni riga della tabella §4 (incluso il barge-in sotto i 200 ms);
  - lo smorzamento;
  - il calcolo della copertura e la posizione dell'occhio da `meta.json`.
- **E2E** (`e2e/run.mjs` + nuovo `e2e/volto.mjs`, build demo `VITE_DEMO=1`, voce finta `?voce=finta`):
  - a 1440 px `data-volto-modalita="webgl"`, oppure "immagine" se Chromium headless non ha WebGL2 (dichiaralo);
  - inviando una domanda in chat, `data-volto-intensita` sale entro 400 ms e poi torna giù;
  - con la conversazione finta, `data-volto-fase` passa per `ascolto → elaborazione → parla → ascolto`;
  - un evento demo (es. spostare un task nel kanban) produce il flash;
  - con WebGL disabilitato compare l'immagine;
  - a 390 px non viene scaricato `luce.webp` 1920;
  - axe senza violazioni serie, console pulita, nessuno scroll orizzontale a 390/768/1280/1920;
  - budget del bundle rispettato.
- Le suite esistenti restano verdi.
- Rigenera il video con `e2e/video-demo.mjs`: aggiungi una scena «Il volto di Guardian» (richiesta → pensa → parla →
  interruzione) e mandalo al titolare.

---

## 8. Ordine di lavoro

| Fase | Contenuto | ✋ |
|---|---|---|
| 1 | Volto più rovinato e scena più scura | ✋ render di controllo |
| 2 | Strati + `meta.json` + verifica | — |
| 3 | `VoltoSfondo` + shader + fallback | — |
| 4 | `stati.ts` (test prima) + collegamenti (richieste, eventi, voce) | — |
| 5 | Stile: piano con frontend-design, vetro, nuovo centro, Impostazioni, parete | ✋ vetro forte o leggero |
| 6 | Prestazioni | — |
| 7 | Test, screenshot, video | — |
| 8 | Docs, ROADMAP, GUARDIAN_STATUS/DECISIONS/HANDOFF, `simplify` + `code-review`, registro, commit/push, notifica | — |

Docs da aggiornare:
- `tools/volto3d/README.md`: come rigenerare volto e strati;
- `docs/guardian-web.md`: il volto, le Impostazioni, i fallback.

Se qualcosa non si può fare in questo ambiente (es. GPU, WebGL in headless), **dillo chiaramente**, fai il resto e lascia le
istruzioni per farlo sul PC del titolare. Non dichiarare finito ciò che non hai verificato.
