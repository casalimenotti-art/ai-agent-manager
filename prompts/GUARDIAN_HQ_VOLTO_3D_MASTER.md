# GUARDIAN HQ — VOLTO 3D REALISTICO, VETRO E VOCE IN TEMPO REALE
### Prompt master per Claude Code (italiano) · repo `casalimenotti-art/ai-agent-manager` · cartella `guardian-web/`

> Da incollare in una sessione di Claude Code sul repository. Lavora **a fasi**: alla fine di ogni fase fai test, commit, push,
> la riga del registro e aggiorna `guardian-web/ROADMAP.md`. Dove trovi ✋ fermati, mostra gli screenshot al titolare
> (Menotti) e aspetta la sua scelta. Spiega sempre in italiano semplice: il titolare non è un tecnico.

---

## 0. Cosa vuole il titolare (leggilo due volte)

Oggi l'HQ di Guardian è **piatto**: un nucleo SVG, pannelli scuri, nessuna profondità. Il titolare vuole:

1. **Un volto di robot in 3D, realistico al 100%, come sfondo vivo dell'intera interfaccia.**
   - È la testa di un robot da combattimento pesante (un "titano" o mech), con piastre di metallo **vero**, consumato:
     graffi, ammaccature, vernice scrostata sui bordi, ruggine nelle fessure, sporco nelle giunture, bulloni.
   - Al centro c'è **un solo grande occhio-nucleo blu** a più anelli, che è il "cuore" di Guardian.
   - Sulla fronte c'è la scritta **«NEXO SRL»** come stencil militare **vecchio e consumato** (lettere mangiate, vernice
     sbiadita e scheggiata). Sulla guancia, piccola, la matricola **«NX-7472»**.
   - Deve sembrare un oggetto fotografato, non un cartone: luce cinematografica, riflessi veri sul metallo, profondità di campo.
2. **Il volto si muove e reagisce quando si parla.** Quando Guardian risponde, l'occhio blu si accende e pulsa con la voce.
   Quando ascolta, l'iride si apre e segue il livello reale del microfono. Quando pensa, gli anelli ruotano.
3. **Interfaccia in vetro (glassmorphism) e HUD stile "assistente da film"** sopra il volto: pannelli traslucidi e sfocati,
   bordi luminosi sottili, anelli e tacche attorno all'occhio, etichette mono, tutto allineato al volto 3D.
4. **Conversazione davvero in tempo reale.** Guardian risponde **appena il titolare smette di parlare**. Se il titolare
   riprende a parlare mentre Guardian parla, Guardian **si zittisce subito, ascolta e poi continua** la conversazione
   (senza perdere ciò che il titolare ha detto interrompendolo).

Decisioni già prese dal titolare (non chiederle di nuovo):
- **Il modello 3D lo crei tu in Blender** (gratis, via script Python headless). Niente acquisti.
- **Voce gratis**: ascolto nel browser o sul PC (servizio `voce` del bridge, privato), risposte dai dati o dal "cervello"
  (Claude Code sul PC del titolare), sintesi vocale locale o del browser. Nessun servizio vocale a pagamento.

### 0.1 Vincoli che non si discutono
- **Originalità.** Il robot è un **design originale di NEXO** (nome di lavoro «NEXO Sentinel»). È *dello stesso genere*
  dei mech dei film e dei videogiochi, ma **non deve copiare nessun personaggio esistente** (in particolare BT-7274 di
  Titanfall). Non usare nomi, loghi, sagome, proporzioni o dettagli riconoscibili di personaggi protetti. Non usare il nome
  né il logo "JARVIS": lo stile HUD è un genere, il nome no.
- **Licenze.** Ogni asset esterno (HDRI, font, texture) deve essere CC0 o con licenza compatibile. Annotalo in
  `guardian-web/public/modelli/LICENZE.md` (nome, autore, link, licenza). Niente asset scaricati da siti senza licenza chiara.
- **Onestà.** Il volto mostra solo stati **reali**: la fase del motore vocale (`src/voce/motore.ts`), lo stato del nucleo
  (`statoNucleo()` in `src/logic/guardian.ts`) e il livello reale del microfono. Non simulare attività che non c'è.
- **Regole del repo** (`AGENTS.md`): lavori su un branch `claude/*`; alla fine di ogni fase
  `python registro/scrivi.py --chi menotti --agente claude-code "…" --file … --esito fatto`, poi commit e push.
  Mai segreti, mai dati personali dei clienti, mai force push, mai `git reset --hard`.
- **Niente regressioni.** Tutto ciò che funziona oggi deve continuare a funzionare: `npm test`, `npm run e2e`,
  `npm run e2e:voce`, `python -m pytest -q tests`, `bash tests/pg/run.sh`.
- **Fallback obbligatorio.** Senza WebGL2, con hardware debole o con `prefers-reduced-motion`, l'HQ deve restare usabile:
  si torna al nucleo SVG di oggi (`src/ui/GuardianCore.tsx`) o a un'immagine ferma del volto.

---

## 1. Audit (prima di scrivere codice)

Leggi davvero questi file e scrivi in `guardian-web/VOLTO3D.md` (breve) cosa hai capito e cosa riusi:

| File | Perché |
|---|---|
| `src/ui/GuardianCore.tsx` | nucleo SVG attuale: diventa il fallback |
| `src/logic/guardian.ts` | `StatoNucleo` (`offline · error · listening · speaking · thinking · approval · working · idle`), `statoNucleo()`, `testoStato()` |
| `src/voce/motore.ts` | macchina a stati `Fase` = `spento · avvio · ascolto · elaborazione · parla`; `misure` (`fineToTesto`, `testoToVoce`, `bargeInToSilenzio`); barge-in; la variabile CSS `--livello` |
| `src/voce/vad.ts` | `Vad` (soglia 0.02, fine frase 1000 ms, minimo 400 ms, massimo 25 s), `BargeIn` (0.06 per 250 ms), `dividiFrasi`, `perLaVoce` |
| `src/voce/adattatori.ts` | `WebSpeechTrascrittore`, `LocaleTrascrittore` (servizio del bridge su 127.0.0.1:8765), `ParlatoreWeb`, `Microfono`, adattatori finti per i test |
| `src/ui/Conversazione.tsx`, `src/ui/useRispondi.ts` | come parte la conversazione e da dove arrivano le risposte (comandi → dati → cervello) |
| `src/ui/CommandCenter.tsx`, `src/ui/Shell.tsx`, `src/ui/Parete.tsx`, `src/ui/Stanze.tsx` | dove vive il nucleo oggi; layout da trasformare |
| `src/styles/tokens.css`, `src/styles/app.css` | token di colore e spazio; il vetro va costruito sopra questi |
| `bridge/voce_locale.py` | servizio vocale locale (`GET /stato`, `POST /trascrivi`): qui aggiungerai la sintesi vocale |
| `e2e/run.mjs`, `e2e/voce-locale.mjs`, `e2e/video-demo.mjs` | test e video da estendere |
| branch `codex/dashboard`, `dashboard/componenti/avatar/` (di Niko) | solo come riferimento tecnico (WebGL, licenze annotate bene). **Non** riusare la mesh umana: il nostro è un robot |

Criterio di accettazione: `VOLTO3D.md` elenca i punti di aggancio (dove si monta il canvas, da dove si leggono fase e livello,
come si passa al fallback) e i rischi (peso, GPU dei telefoni, contrasto del testo sopra lo sfondo).

---

## 2. Concept del volto ✋

Prima di modellare tutto, fai **due proposte** e falle scegliere al titolare.

1. Scrivi una **scheda di design** in `tools/volto3d/CONCEPT.md`:
   - **Silhouette**: testa larga e bassa, mento squadrato, "fronte" con visiera, guance a piastre sovrapposte, collo con pistoni
     e cavi. Deve leggersi bene anche come sagoma scura su fondo scuro.
   - **Occhio-nucleo**: 3 anelli concentrici dentro una ghiera di metallo spesso; iride a **lamelle** (come un diaframma
     fotografico) che si apre e si chiude; vetro frontale leggermente graffiato; luce blu `#3FB8FF` → ciano `#22D3EE`
     nei picchi (coerente con l'accento di Guardian in `tokens.css`).
   - **Piastre**: 8–14 piastre principali con linee di pannello, bulloni a testa esagonale, prese d'aria a feritoie sui lati,
     una "griglia bocca" sotto l'occhio (si illumina debolmente quando parla).
   - **Materiali**: acciaio canna di fucile sotto, vernice grigio-oliva o grigio-antracite sopra; vernice scheggiata sugli spigoli;
     ruggine e sporco solo nelle cavità; segni di saldatura; un'ammaccatura evidente su una guancia.
   - **Scritte**: «NEXO SRL» a stencil sulla fronte (vernice bianco sporco, consumata al 40–60%), «NX-7472» piccolo sulla guancia,
     un paio di marcature tecniche inventate (es. "CAL. 07", frecce di sollevamento). Niente loghi di terzi.
2. Fai due **render fermi** in Blender (Cycles, 1600×1000) di due varianti (es. A = più massiccio e scuro, B = più slanciato e
   chiaro) in `tools/volto3d/concept/` e mostrali al titolare. ✋ Si procede solo con la variante scelta.

Criterio di accettazione: due immagini realistiche, chiaramente originali, con la scritta consumata leggibile.

---

## 3. Modello in Blender, interamente da script

Tutto deve essere **riproducibile**: chiunque può rigenerare il modello con un comando.

### 3.1 Strumenti
- **Punto di partenza già pronto**: `tools/volto3d/costruisci.py` costruisce e renderizza il volto (varianti A/B); i concept
  sono in `tools/volto3d/concept/`. Parti da lì, non ricominciare da zero.
- Blender si installa come modulo Python da PyPI, senza scaricarlo da blender.org (che dal container può essere bloccato):
  `python3.13 -m venv .venv-blender && .venv-blender/bin/pip install bpy pillow` (Blender 5.3).
  Annota la versione usata in `tools/volto3d/README.md`.
- Strumenti open source valutati (dettagli e licenze in `tools/volto3d/README.md`):
  - **blender-mcp**: per ritocchi dal vivo sul PC del titolare;
  - **TRELLIS.2**: dall'immagine al modello 3D, ma solo con una GPU NVIDIA e attenzione alle licenze NVIDIA non commerciali;
  - **Hunyuan3D**: **vietato**, la licenza esclude l'Unione Europea;
  - **Open-Higgsfield**: non fa 3D e usa API a pagamento.
- Script in `tools/volto3d/`:
  - `costruisci.py`: geometria;
  - `materiali.py`: materiali procedurali;
  - `bake.py`: cottura delle texture;
  - `rig.py`: ossa e shape key;
  - `esporta.py`: GLB;
  - `render.py`: render fermi per concept, fallback e telefono.
- Comando unico: `blender -b -P tools/volto3d/tutto.py -- --variante A --uscita guardian-web/public/modelli/`.

### 3.2 Geometria (hard-surface)
- Modella le piastre come mesh separate con **bevel** reali (2–3 segmenti) sugli spigoli: è ciò che cattura la luce e fa "vero".
- Linee di pannello incise, bulloni istanziati, feritoie, ghiera dell'occhio spessa, lamelle dell'iride (8–12) come oggetti separati.
- Topologia pulita per il bake: un modello **alto** (dettagli) e un modello **basso** (per il web).
- Budget del modello web: **≤ 60.000 triangoli** in tutto.

### 3.3 Materiali e texture (il realismo si gioca qui)
- Costruisci i materiali con nodi procedurali:
  - rumore e Voronoi per sporco e ruggine;
  - **Pointiness/AO** per l'usura sugli spigoli e lo sporco nelle cavità;
  - graffi direzionali (rumore stirato);
  - impronte e opacità variabile nella roughness.
- Scritta «NEXO SRL»: testo convertito in maschera, poi **maschera di consumo** (rumore + usura sui bordi delle lettere +
  graffi che la attraversano). Deve sembrare vecchia di anni, non stampata ieri.
- **Bake** su texture 2048×2048 (atlas unico o 2 atlas):
  - Base Color;
  - ORM (Occlusion, Roughness, Metallic nei canali R/G/B);
  - Normal (dai dettagli del modello alto, più graffi e ammaccature);
  - Emissive (solo occhio, griglia bocca e piccoli LED).
- Comprimi le texture per il web: **KTX2 (Basis)** se gli strumenti sono disponibili, altrimenti **WebP**.
  Prevedi una variante 1024 per i telefoni.

### 3.4 Rig e animazioni (contratto dei nomi)
Usa **esattamente** questi nomi, così un modello fatto da un artista in futuro si sostituisce senza toccare il codice
(documentali in `tools/volto3d/CONTRATTO.md`):

| Nome nel GLB | Tipo | Uso |
|---|---|---|
| `Testa` | osso radice | rotazione yaw/pitch (segue lo sguardo, "respiro") |
| `Occhio` | nodo | posizione dell'occhio (serve all'HUD per agganciarsi) |
| `Iride_Apertura` | shape key 0→1 | lamelle chiuse → aperte |
| `Anello_1`, `Anello_2`, `Anello_3` | nodi | rotazione degli anelli quando pensa |
| `Otturatore` | shape key 0→1 | "battito di palpebra" meccanico (barge-in, avvio) |
| `Bocca_Griglia` | materiale emissivo separato | intensità durante il parlato |
| `Mat_Occhio` | materiale emissivo | colore e intensità del nucleo |

### 3.5 Esportazione
- GLB con compressione **meshopt** o **Draco**. Peso totale **≤ 6 MB** (desktop) e **≤ 2,5 MB** (variante telefono).
- File in `guardian-web/public/modelli/`:
  - `volto.glb`;
  - `volto-mobile.glb`;
  - `volto-fermo.webp`: render fermo per il fallback e il telefono, 1920 px e 960 px;
  - `LICENZE.md`.
- Controllo automatico in `tools/volto3d/verifica.py`: numero di triangoli, peso, presenza di tutti i nomi del contratto.

Criterio di accettazione: il comando unico rigenera tutto da zero; `verifica.py` passa; il render fermo sembra una foto.

---

## 4. La scena 3D nel browser

### 4.1 Librerie (versioni fissate, nessun `^`)
- `three` (r16x stabile), `@react-three/fiber` 8.x (compatibile con React 18), `@react-three/drei` 9.x,
  `@react-three/postprocessing` 2.x + `postprocessing`.
- Tutto il 3D vive in `src/volto3d/` ed è caricato con `React.lazy` in un **chunk separato**. Il bundle iniziale non deve
  crescere di più di 5 KB gzip (verifica con la build).

### 4.2 Composizione
- Un `<canvas>` **fisso a tutto schermo, dietro l'interfaccia** (z-index sotto `.shell`), con `pointer-events: none`.
- Inquadratura:
  - desktop: volto leggermente decentrato a destra, l'occhio a circa 60% della larghezza e 40% dell'altezza;
  - modalità parete (`?parete=1`): volto centrato e più grande;
  - telefono: render fermo `volto-fermo.webp` con glow CSS sull'occhio (niente WebGL).
- Camera con focale da ritratto (circa 50–85 mm equivalenti), **profondità di campo** leggera (fuoco sull'occhio).

### 4.3 Luce e resa fotografica
- Ambiente: **HDRI CC0** da Poly Haven (interno industriale o hangar, 1K–2K), solo per i riflessi; sfondo quasi nero.
- Una luce chiave fredda dall'alto a sinistra, una controluce calda e sottile da dietro a destra, il blu dell'occhio che
  illumina davvero le piastre vicine (luce puntiforme blu nell'occhio, intensità legata allo stato).
- Tone mapping **AgX** (o ACES), colori sRGB corretti, ombre morbide.
- Post-processing: **bloom solo sugli emissivi** (soglia alta), vignettatura leggera, grana fine, aberrazione cromatica
  quasi nulla. Facoltativo: polvere in sospensione nel fascio di luce (poche centinaia di particelle).
- Parallasse lieve: il volto ruota di pochi gradi seguendo il mouse (smorzato). Niente movimenti bruschi.

Criterio di accettazione: a 1920×1080 lo sfondo sembra una foto di un oggetto reale. Il titolare lo guarda e dice «sì, così».
È un punto ✋: fai 2 screenshot, luce più fredda o più calda.

---

## 5. Stati → animazione (cuore del "vivo")

Crea `src/volto3d/stati.ts` con una funzione **pura e testata**:

```
statoVolto({ fase, nucleo, livello, ampiezzaVoce, tempo }) → { iride, anelliVel, intensitaOcchio, coloreOcchio, otturatore, bocca, testaYaw, testaPitch }
```

| Situazione reale | Fonte | Cosa fa il volto |
|---|---|---|
| Inattivo | `fase = spento`, nucleo `idle` | occhio fioco (circa 15%), "respiro" lento della testa (ampiezza 0,5°, periodo 6 s), iride semichiusa |
| Avvio conversazione | `fase = avvio` | battito dell'otturatore, l'occhio si accende in 400 ms |
| Ascolto | `fase = ascolto` | iride aperta; l'anello esterno pulsa con il **livello reale del microfono** (stesso valore di `--livello`) |
| Sta pensando | `fase = elaborazione` o nucleo `thinking` | anelli che ruotano in versi opposti, scansione luminosa che scorre |
| Sta parlando | `fase = parla` | occhio acceso (picchi ciano) e griglia bocca accesa **in sincrono con l'ampiezza reale della voce** |
| Interrotto (barge-in) | `motore.interrompi(true)` | otturatore che "sbatte" in 120 ms, l'occhio scende di colpo e torna in ascolto |
| Approvazione in attesa | nucleo `approval` | un anello diventa ambra `#FBBF24` e pulsa lento |
| Errore / offline | nucleo `error` / `offline` | sfarfallio rosso `#F87171` breve, poi occhio fioco e fisso |

Regole:
- Tutte le transizioni sono smorzate (molle o lerp), mai a scatti, tranne l'otturatore.
- L'ampiezza della voce deve essere **vera**:
  - con la sintesi vocale locale (fase 7), un `AnalyserNode` sul flusso audio della voce;
  - con la voce del browser (Web Speech), che non dà l'audio, usa gli eventi `boundary` (parola per parola) per un inviluppo
    plausibile e dichiaralo in Diagnostica voce («ampiezza stimata»).
- Test vitest per ogni riga della tabella.

---

## 6. Interfaccia in vetro e HUD ✋

### 6.1 Vetro
- Nuovi token in `tokens.css`: `--vetro-bg` (es. `rgba(12,18,28,0.42)`), `--vetro-blur` (16–24 px), `--vetro-bordo`
  (gradiente speculare da `rgba(255,255,255,0.18)` a trasparente), `--vetro-ombra`, `--vetro-rumore` (texture di rumore 2%).
- Classe `.vetro`: `backdrop-filter: blur(var(--vetro-blur)) saturate(140%)`, bordo di 1 px con gradiente, ombra morbida,
  rumore sottile, riflesso diagonale debolissimo in alto.
- Applica il vetro a header, rail, dock, card del centro, drawer, palette, barra della conversazione e stanze.
- **Budget**: al massimo 6 superfici sfocate visibili insieme; gli elementi dentro una card di vetro sono opachi o semplici.
- **Fallback**: con `prefers-reduced-transparency`, senza supporto a `backdrop-filter` o con FPS bassi, le superfici diventano
  opache (colori di oggi). Interruttore in Impostazioni: «Vetro: forte / leggero / spento».
- **Contrasto AA garantito**: dietro ogni blocco di testo c'è uno scrim (velo scuro) sufficiente. Verifica con axe e con
  screenshot sopra le zone più chiare del volto.

### 6.2 HUD stile "assistente da film"
- Uno strato SVG/CSS sopra il canvas con:
  - anelli sottili concentrici attorno all'occhio, tacche graduate;
  - 2–3 archi che ruotano piano;
  - etichette mono maiuscole con tracking («NX-7472 · ONLINE», «ASCOLTO LOCALE · PRIVATO», latenza misurata);
  - piccoli marcatori che collegano l'occhio ai pannelli principali.
- L'HUD si **aggancia alla posizione dell'occhio 3D**: proietta il nodo `Occhio` in coordinate schermo a ogni frame (o quando
  cambia la finestra) e passa `--occhio-x`, `--occhio-y` al CSS.
- Glow solo su linee ed elementi attivi, **mai sul testo dei dati**.
- Il testo di stato di Guardian (`testoStato()`) e i sottotitoli della conversazione compaiono vicino all'occhio, in vetro.

### 6.3 Layout
- Il centro diventa "cabina di comando":
  - il volto riempie lo sfondo;
  - a sinistra una colonna di vetro con numeri e prossime azioni;
  - in basso la barra della conversazione;
  - le tre stanze come schede di vetro che "orbitano" attorno all'occhio.
- Drawer, palette, stanze e parete continuano a funzionare come oggi (stessi URL, stesse scorciatoie).
- ✋ Due varianti (vetro forte / vetro leggero) con screenshot a 1440 e 1920 px; il titolare sceglie.

---

## 7. Voce in tempo reale (gratis)

Obiettivo misurabile, letto da Diagnostica voce (`misure` del motore):
- dalla fine della frase del titolare alla **prima parola di Guardian**: **< 1,2 s** per le risposte dai dati e **< 2,5 s**
  quando risponde il cervello;
- da quando il titolare riprende a parlare al **silenzio di Guardian**: **< 200 ms**.

### 7.1 Fine frase più rapida e naturale
- Fine frase **adattiva**: 600–700 ms di silenzio di base. Fino a 1000 ms se la frase finisce con parole di continuazione
  ("e", "ma", "quindi", "cioè", "tipo") o con un tono sospeso.
- Mantieni il minimo di 400 ms e il massimo di 25 s.
- Test vitest sul nuovo VAD.

### 7.2 Ascolto in streaming sul PC
- Nel servizio `bridge/voce_locale.py` aggiungi un riconoscitore **in streaming**:
  - sherpa-onnx online, modello italiano o multilingue CC0/Apache;
  - endpoint WebSocket o HTTP a blocchi su 127.0.0.1;
  - testo **parziale** mentre si parla (sottotitoli dal vivo) e finale alla fine della frase.
- Stesse regole di oggi: solo 127.0.0.1, solo le origini dell'HQ in `GUARDIAN_HQ_ORIGINI`, nessun audio salvato.
- Senza modello si resta all'attuale `POST /trascrivi` o a Web Speech.

### 7.3 Sintesi vocale locale con ampiezza vera
- Nuova rotta `POST /parla` nel servizio vocale:
  - testo → audio PCM in streaming, motore Piper o sherpa-onnx TTS con una voce italiana a licenza libera;
  - prima frase restituita subito, le altre mentre suona la prima.
- Nel browser:
  - `LocaleParlatore` riproduce con WebAudio;
  - un `AnalyserNode` sul suono fornisce l'**ampiezza vera** al volto (fase 5);
  - fallback `ParlatoreWeb` (Web Speech).
- Voce "da robot" credibile: leggero filtro metallico facoltativo (WebAudio), disattivabile.

### 7.4 Interruzioni perfette (barge-in)
- `getUserMedia` con `echoCancellation`, `noiseSuppression`, `autoGainControl` attivi, così la voce di Guardian non fa scattare
  il barge-in da sola.
- Soglia di barge-in **adattiva**: misura il rumore di fondo mentre Guardian parla e scatta solo sopra quel livello più un margine.
- Quando scatta:
  1. ferma subito l'audio (WebAudio `stop()` o `speechSynthesis.cancel()`);
  2. otturatore sul volto;
  3. fase `ascolto`.
- **Non perdere le prime parole** del titolare: tieni un buffer audio continuo di circa 500 ms (pre-roll) e mandalo al
  riconoscitore insieme al resto della frase.
- Poi Guardian risponde **tenendo conto** di ciò che stava dicendo (passa a `useRispondi` la frase interrotta come contesto).

### 7.5 Cervello più rapido
- Il cervello (`bridge/cervello.py`, Claude Code in sola risposta) restituisce già frasi in streaming: assicurati che la
  **prima frase** venga detta appena arriva.
- Mentre aspetta: un breve suono o un «Un attimo…» detto subito, **solo** se l'attesa supera 900 ms.

Criterio di accettazione: E2E con microfono finto (vedi `e2e/voce-locale.mjs`) che misura le latenze. Test del barge-in che
verifica che la frase interrotta arrivi intera al riconoscitore.

---

## 8. Prestazioni, fallback, accessibilità

- **WebGL2** obbligatorio per il 3D; altrimenti nucleo SVG (`GuardianCore`).
- **Auto-degrado**: misura gli FPS nei primi 3 secondi e poi ogni 10. Sotto 45 fps:
  1. riduci il DPR (fino a 1);
  2. togli la profondità di campo;
  3. togli il bloom;
  4. passa all'immagine ferma.
- **Pausa** del rendering con `document.hidden` e quando un drawer largo copre il volto. Rendering a richiesta quando
  è tutto fermo (inattivo = 20 fps).
- **Telefono**: immagine ferma + glow CSS sull'occhio guidato dalla stessa `statoVolto()`; nessun download del GLB.
- `prefers-reduced-motion`: niente parallasse, niente rotazioni, solo variazioni di luce dell'occhio.
- CPU a riposo < 5% su un portatile medio; memoria GPU < 300 MB.
- Accessibilità: il canvas è `aria-hidden`; lo stato di Guardian resta leggibile come testo (`aria-live` come oggi);
  axe senza violazioni serie; contrasto AA su tutti i testi sopra il vetro.

---

## 9. Test e prove

- **vitest**: `statoVolto()` (tutte le righe della tabella §5), VAD adattivo, soglia di barge-in, selettore del livello di vetro.
- **E2E** (`e2e/run.mjs` + nuovo `e2e/volto3d.mjs`):
  - canvas presente e animato a 1440 e 1920 px (Chromium headless con GL software: verifica che il frame cambi tra stati);
  - con WebGL disattivato compare il nucleo SVG;
  - a 390 px compare l'immagine ferma e il GLB **non** viene scaricato;
  - con la voce finta (`?voce=finta`), la fase `parla` alza l'intensità dell'occhio e il barge-in la abbassa entro 200 ms;
  - console pulita, axe senza violazioni serie, nessuno scroll orizzontale alle 4 larghezze;
  - budget del bundle: iniziale invariato (±5 KB), chunk 3D separato.
- Tutte le suite esistenti restano verdi.
- **Video**: aggiorna `e2e/video-demo.mjs` per mostrare il volto (inattivo → ascolto → pensa → parla → interruzione) e
  rigenera il video. Mandalo al titolare.

---

## 10. Ordine di lavoro e consegne

| Fase | Contenuto | ✋ |
|---|---|---|
| 1 | Audit → `guardian-web/VOLTO3D.md` | — |
| 2 | Concept + 2 render | ✋ scelta della variante |
| 3 | Modello Blender da script, texture consumate, rig, GLB, verifica | — |
| 4 | Scena 3D lazy dietro l'interfaccia, luce fotografica | ✋ luce fredda o calda |
| 5 | Stati → animazione (`statoVolto`) | — |
| 6 | Vetro + HUD agganciato all'occhio, nuovo layout | ✋ vetro forte o leggero |
| 7 | Voce in tempo reale: fine frase adattiva, streaming, TTS locale, barge-in con pre-roll | — |
| 8 | Prestazioni, fallback, accessibilità | — |
| 9 | Test, screenshot, video | — |
| 10 | Docs (`docs/guardian-web.md`: come rigenerare il modello; `docs/guardian-setup.md`: voce locale con TTS), ROADMAP, GUARDIAN_STATUS/DECISIONS/HANDOFF, registro, notifica al titolare | — |

A ogni fase:
1. Test verdi.
2. `python registro/scrivi.py --chi menotti --agente claude-code "Volto 3D fase N: …" --file … --esito fatto`.
3. Commit + push sul branch `claude/*`.
4. Breve messaggio al titolare in italiano semplice: cosa vede di nuovo, cosa deve scegliere.

Se una cosa non si può fare in questo ambiente (es. Blender non installabile, GPU assente per un render), **dillo
chiaramente**, fai la parte possibile e lascia le istruzioni precise per farla sul PC del titolare. Non dichiarare finito ciò
che non hai verificato.
