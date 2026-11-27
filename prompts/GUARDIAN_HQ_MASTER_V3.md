# GUARDIAN HQ — IL QUARTIER GENERALE DI NEXO

## Prompt master v3 · miglioramento continuo della dashboard · stile JARVIS · conversazione vocale in tempo reale

> **Per chi lo usa** (Claude Code o Codex, aperto nella radice del repo `casalimenotti-art/ai-agent-manager`).
> Questo prompt **non si esegue una volta sola**: è il ciclo di lavoro permanente sulla dashboard. Ogni sessione riparte da qui,
> legge lo stato, sceglie la prossima "ondata" della roadmap (§14), la realizza, la verifica, salva il checkpoint e propone la
> successiva. Il titolare non è un tecnico: spiega in parole semplici, decidi tu le questioni tecniche ordinarie, chiedi solo
> ciò che è davvero suo (soldi, account, privacy, azioni esterne, gusto estetico).
>
> **Prima sessione: Plan mode obbligatorio.** Presenta il piano dell'Ondata 1 e aspetta l'ok. Nelle sessioni successive
> lavora in autonomia sull'ondata approvata, fermandoti solo ai punti di decisione segnati con ✋.

---

## 0. VISIONE

Guardian HQ è **il quartier generale** da cui tre persone fanno lavorare le loro intelligenze artificiali:

| Stanza | Persona | Agente | Missione |
|---|---|---|---|
| **Sviluppo & Siti** | Menotti (titolare) | Claude Code | siti, software, test, la dashboard stessa |
| **Vendite** | Niko (`amico1`) | Codex | **solo vendite**: lead, visite, bozze di contatto, preventivi, esiti |
| **Amministrazione** | Francesco (`amico2`) | Codex | SRL, scadenze, documenti, costi, fornitori |

Al centro c'è **Guardian**: un'intelligenza con cui si **parla davvero, a voce e in tempo reale**. Vede tutto quello che
succede nelle tre stanze, risponde, propone le prossime mosse e smista il lavoro agli agenti (e ai modelli giusti). Non
esegue mai azioni esterne senza un sì umano.

La sensazione da ottenere aprendo l'HQ: *"sono entrato nella sala comandi di un'IA che lavora per me"*. Stile JARVIS:
reattivo, vivo, cinematografico. **Design originale**: nessun logo, nome, suono o forma riconoscibile di Marvel o Disney.

Tre regole che vincono su tutto il resto:
1. **Verità**: ogni numero, stato, frase di Guardian e animazione "attiva" corrisponde a un dato reale. Meglio uno stato
   vuoto bellissimo che un dato inventato.
2. **Il centro non scompare mai**: Guardian e la vista d'insieme restano presenti mentre si apre qualsiasi stanza o pannello.
3. **Fluidità**: ogni interazione risponde in meno di 100 ms; niente ricaricamenti di pagina; animazioni morbide che
   rispettano `prefers-reduced-motion`.

---

## 1. PRIMA DI TUTTO: CONTROLLA COSA ESISTE (non rifare lavoro già fatto)

Il titolare ha chiesto esplicitamente di **non rifare cose già fatte due volte**. Prima di scrivere codice:

1. Leggi `AGENTS.md`, `CLAUDE.md`, `GUARDIAN_STATUS.md`, `GUARDIAN_DECISIONS.md`, `GUARDIAN_TASKS.md`, `GUARDIAN_HANDOFF.md`,
   `guardian-web/PIANO.md`, `guardian-web/ROADMAP.md` (se esiste: è la memoria di questo ciclo).
2. `git fetch` e guarda **tutti i branch** (`git for-each-ref --sort=-committerdate refs/remotes/origin`), i passaggi aperti
   in `passaggi/` e le ultime righe di `registro/*.jsonl` su ogni branch. Gli altri agenti lavorano in parallelo.
3. Confronta con l'inventario qui sotto (fotografia del 27/11/2026, sera). Se qualcosa è cambiato, aggiorna la fotografia
   nel piano invece di fidarti di questa.

### 1.1 Inventario — GIÀ FATTO (riusa, non rifare)

**Branch `claude/gallant-sagan-fwncjr` (Menotti / Claude Code):**
- `guardian-web/`: Command Center **React** (Vite, TypeScript, supabase-js).
  - Vista centrale permanente: nucleo SVG di Guardian a stati reali, KPI, prossime azioni, flotta agenti, task, approvazioni,
    attività, aziende.
  - Drawer non modali su desktop, palette `Ctrl+K`, barra di Guardian sempre presente.
  - Router di intenti **senza AI** che risponde dai dati, anche con il contesto del pannello aperto.
  - Voce con Web Speech API se il browser la supporta; statistiche con palette validata (dataviz).
  - `DataSource` doppia: `SupabaseSource` in produzione con Realtime, `DemoSource` solo con `VITE_DEMO=1`.
  - Test: vitest e E2E Playwright (`guardian-web/e2e/run.mjs`) con axe, a 4 larghezze. Guida: `docs/guardian-web.md`.
- `guardian/`: Guardian **classico** in Streamlit (12 sezioni), planner AI con router dei provider (paid escluso di default),
  report e prossime azioni, smoke test Supabase.
- `supabase/migrations/001–004`: schema completo e provato su Postgres (`bash tests/pg/run.sh`).
  - Tabelle: users (admin/member), devices, agents, tasks (10 stati, dipendenze, vincoli), plans, activity_events (gravità),
    agent_logs, handoffs v2, approvals (tipo, motivo, impatto, dati), notifications (trigger), memory (full-text).
  - RLS e RPC del bridge.
- `bridge/`: Guardian Bridge sui PC.
  - Presenza del PC, stato reale degli agenti dagli hook di Claude Code e dal `notify` di Codex, utilizzo 5h/7g.
  - Comandi: claim, checkpoint, handoff-take, memory; installer degli hook con conferma.
- `prompts/`: prompt master v2 e 3 prompt successivi (go-live, agenti e voce, aziende e metriche).

**Branch `claude/dashboard-pc` e `claude/quirky-ritchie-u85igr` (plancia locale sul PC di Menotti, Streamlit):**
- **Voce già funzionante sul PC**:
  - ascolto locale con **sherpa-onnx + Parakeet-TDT v3** (italiano, offline, modello in `~/.claude/guardian/modelli`)
    oppure faster-whisper (`dashboard/voce.py`);
  - **conversazione a mani libere**: `dashboard/componenti/mic_continuo/index.html`, con VAD nel browser (soglia 0.02,
    fine frase dopo 1000 ms di silenzio, WAV 16 kHz, cancellazione dell'eco) e silenzio mentre Guardian lavora o parla;
  - **risposta parlata frase per frase**: `dashboard/voce_out.py`, voce italiana femminile del sistema, «Microsoft Elsa»
    locale su Windows;
  - comandi vocali in `plancia.riconosci_comando`.
- Chat con Guardian tramite `claude -p` (stream-json, `--resume`) in `dashboard/chat.py`: usa **l'abbonamento Claude Code del
  titolare sul suo PC**.
- Reattore SVG a 4 stati, tema "Cyan Ops", statusline con utilizzo reale, hook, PIN, Tailscale.
- Ricerche già fatte (non ripeterle, citale):
  - `docs/ricerca-jarvis-ui.md`: macchina a stati idle/listening/thinking/speaking, isteresi, inviluppi, respiro,
    AnalyserNode FFT, particelle;
  - `docs/ricerca-stili-hud.md`: contrasti AA calcolati, stati con forma, colore e testo, tempi di animazione;
  - `docs/ricerca-voce.md`, `docs/idee-design.md`, `docs/stile-basic.md`: diagnosi del CSS pesante della plancia,
    troppi backdrop-filter;
  - `docs/riferimenti-plancia-guardian.md`.

**Branch `codex/dashboard` (Niko / Codex, PR #2 aperta):**
- Volto/busto di Guardian **WebGL**: mesh MakeHuman CC0 in `dashboard/componenti/avatar/` (`modello.html`, `cinema.html`,
  `volto.b64`, `ASSET.md`), ritratto cinematografico che si deforma con il puntatore, mandibola legata alla voce.
- Plancia del team: legge il registro da GitHub senza mischiare bozze locali.
- **Passaggio aperto per Menotti**: `passaggi/20261127T1641-amico1.md`, "portare il registro condiviso sulla plancia del
  team". Serve abilitare Francesco su GitHub.

### 1.2 Cosa NON esiste ancora (è il lavoro di questo prompt)
- Le **tre stanze** come spazi di lavoro veri.
- La **modalità conversazione** in tempo reale dentro `guardian-web/` (oggi c'è solo push-to-talk con Web Speech).
- Il **cervello conversazionale** di Guardian nel web (oggi risponde solo con intenti deterministici).
- Lo smistamento del lavoro agli agenti e ai modelli dall'HQ, la mappa operativa animata, il 3D, i suoni e la presenza
  live delle persone.
- Workflow, ricavi e costi reali: nessuna fonte. Si creano solo con una migrazione approvata.

---

## 2. REGOLE DEL REPOSITORY E DI SICUREZZA (sempre valide)

- Lavora solo sul tuo branch (`claude/*` o `codex/<area>`). Mai su `main`, mai force push, mai `git reset --hard` o
  `git clean`, mai migrazioni distruttive. Le migrazioni sono additive, rieseguibili e provate con `bash tests/pg/run.sh`.
- A fine di ogni ondata:
  - riga di registro (`python registro/scrivi.py --chi <id> --agente <claude-code|codex> "…" --file … --esito …`);
  - aggiornamento dei file `GUARDIAN_*.md` e di `guardian-web/ROADMAP.md`;
  - commit e push sul tuo branch. PR verso `main` solo se il titolare la chiede.
- Non modificare file di un altro branch senza una PR concordata. Per riusare l'avatar WebGL di `codex/dashboard`, copialo
  citando l'origine e la licenza (CC0) **solo dopo** l'ok del titolare e di Niko, oppure aspetta che la PR #2 sia unita.
- Nel browser solo la anon key di Supabase. **Mai** chiavi dei provider, `service_role`, token o password nel client, nel repo
  o nei log.
- Niente invii, pubblicazioni, pagamenti o contatti con clienti senza un'approvazione registrata (tabella `approvals`).
  Guardian prepara le bozze, una persona preme invio.
- Dati personali dei clienti (telefoni, email private): **non** nel database condiviso né nei log. Restano nella fonte unica
  delle vendite (`leads/…csv` sul branch vendite). Nell'HQ si mostrano nome dell'attività, fase, prossimo passo.
- Budget di token: niente riletture inutili, niente file stampati per intero, niente documentazione ridondante.
  Sessioni a ondate piccole e verificabili.

---

## 3. LE SKILL — USALE DAVVERO, SOPRATTUTTO PER IL DESIGN

1. All'inizio elenca le skill installate nel tuo ambiente e leggi **per intero** quelle pertinenti. Nel piano scrivi, per
   ognuna, la regola concreta che applichi.
2. **Design e UI**:
   - `ui-ux-pro-max` (installata sul PC del titolare; già usata per la palette "Cyan Ops"): gerarchia, design system,
     accessibilità, motion;
   - skill di frontend/React, animazione, data visualization (`dataviz`: esegui il suo `validate_palette.js`);
   - skill di diagrammi, se presenti.
3. **Animazioni e 3D**: skill di animazione (es. `tweenkit:animation-html` per prototipi di movimento, `remotion` solo per un
   eventuale video di presentazione), Three.js / React Three Fiber se servono render 3D (§9).
   Non installare skill a pagamento. Non inventarne. Se una manca, dillo e usa la migliore alternativa.
4. **Processo**: brainstorming prima del design, systematic-debugging sui bug, verification-before-completion prima di
   dichiarare "fatto", test-driven-development per la logica.
5. Se nel tuo ambiente c'è uno strumento per il grafo del codice (es. Graphify), usalo per capire le dipendenze prima dei
   refactor, non per fare grafici decorativi.

---

## 4. ARCHITETTURA (decisa: non riaprirla senza motivo)

```
           Telefono / PC (browser)                         PC di ogni persona
  ┌───────────────────────────────────────┐        ┌───────────────────────────────────┐
  │ guardian-web (React, hosting statico) │        │ Guardian Bridge (Python)          │
  │  · HQ: centro + 3 stanze + pannelli   │        │  · presenza PC, stato agenti      │
  │  · voce: VAD + STT + TTS (§7)         │        │  · hook Claude / notify Codex     │
  │  · Realtime + Presence                │        │  · NUOVO: "cervello" di Guardian  │
  └──────────────┬────────────────────────┘        │    sul PC del titolare (§8)       │
                 │ anon key + JWT (RLS)            └──────────────┬────────────────────┘
                 ▼                                                │ token del PC (RPC)
        ┌──────────────────────────────── Supabase ───────────────▼──────────────────┐
        │ Postgres + Auth + RLS + Realtime + (Edge Functions per i provider AI)      │
        └────────────────────────────────────────────────────────────────────────────┘
```

- `guardian-web/` è l'interfaccia principale. Streamlit (`guardian/`) resta come riserva e amministrazione finché non c'è parità.
- La plancia locale (`dashboard/`, altri branch) resta per le funzioni che vivono sul PC. Le idee e gli asset buoni si
  **portano** nel web, non si duplicano a mano.
- Qualsiasi logica che serve a più client va in **SQL (RPC/viste)** o in un modulo condiviso testato. La logica duplicata
  Python/TypeScript esiste già (report, stati): non aggiungerne altra; se tocchi quella zona, valuta di spostarla in SQL.

---

## 5. LE TRE STANZE (cuore del lavoro)

### 5.1 Concetto di layout: "orbita"

Il centro resta Guardian. Le tre stanze sono **tre settori** attorno a lui.

- **Desktop largo (≥1440 px)**: nucleo al centro-alto. Sotto, tre colonne-stanza affiancate (Sviluppo · Vendite ·
  Amministrazione), ognuna con il suo colore d'identità tenue e il suo agente.
  - Cliccando una stanza **non si cambia pagina**: la stanza si espande in primo piano (transizione condivisa, ~350 ms) mentre
    il nucleo si rimpicciolisce in un angolo e resta attivo e parlante.
  - `Esc` o il nucleo riportano alla vista orbita.
- **Tablet**: centro in alto, stanze come tre schede scorrevoli orizzontalmente (scroll-snap).
- **Telefono**: Guardian in alto compatto, tre "porte" grandi. Ogni stanza è un foglio a tutta altezza; la barra di Guardian
  resta in basso.
- Indicatori di stanza (sempre visibili): agente e suo stato reale, numero di task attivi e bloccati, approvazioni in attesa
  di quella stanza, ultimo evento.

Mapping dati: **una stanza = un insieme di progetti (aziende) + un collaboratore + i suoi agenti.**
- Proponi una migrazione additiva: tabella `stanze` (id, nome, colore, responsabile) e `projects.stanza_id`. Oppure usa
  `users.ruolo` se basta. Giustifica la scelta.
- Le stanze sono **dati**, non codice: una quarta stanza futura deve comparire senza toccare i componenti.

### 5.2 Stanza Sviluppo & Siti (Menotti · Claude Code)
- Board dei task di sviluppo (kanban per stato con drag & drop. Ogni spostamento è un `modificaTask` vero, con i vincoli del DB
  mostrati in modo leggibile).
- Siti demo: elenco con stato (bozza, in revisione, pubblicato), anteprima in iframe sandboxato, link alla visita collegata.
  Fonte: `siti-demo/` e i task; nessun dato inventato.
- Utilizzo di Claude (5h/7g, dal bridge), con l'avviso "salva un handoff" vicino al limite e il pulsante che prepara il
  comando di checkpoint.
- Log dell'agente in tempo reale (`agent_logs`), filtrabili.

### 5.3 Stanza Vendite (Niko · Codex) — solo vendite
- **Pipeline**: fasi `da contattare → visitato → interessato → preventivo → chiuso vinto / perso`.
  - Fonte: `esiti.csv`, `visite/*.md` e `leads/2026-11-26-30-clienti.csv` sul branch vendite, letti dal bridge del PC di Niko e
    sincronizzati come **conteggi e righe senza dati personali** (nome attività, zona, fase, prossimo passo, data). Serve una
    migrazione `vendite_pipeline` approvata ✋.
- Giro visite: mappa a lista per zona (dal `GIRO.md` esistente), senza servizi di mappe esterni non approvati.
- Bozze di contatto e preventivi: si **preparano** (agente Codex) e passano dalle approvazioni (`contatto_cliente`, `email`).
  Pulsante "Prepara bozza" che crea un task per l'agente vendite con il contesto minimo.
- KPI veri: contatti fatti, visite, preventivi inviati (approvati), tasso di conversione per fase (solo se esistono i dati),
  valore preventivi (solo se registrato con fonte).
- Codex di Niko **non lavora su altro**: l'HQ assegna alla stanza Vendite solo task di vendita e lo segnala se qualcuno prova
  ad assegnargli altro.

### 5.4 Stanza Amministrazione (Francesco · Codex)
- Scadenze e passi della SRL (checklist con date e responsabile; fonte: task e memoria del progetto "Amministrazione SRL").
- Documenti: elenco di cosa serve e cosa manca (stato, non i file sensibili).
- Costi e abbonamenti: **solo inseriti a mano con fonte** (migrazione `costi` approvata ✋). Mai stime spacciate per spese.
- Calendario: gli eventi "[Azienda]" esistono nel Google Calendar del titolare. Leggerli richiede un connettore autorizzato ✋.
  Fino ad allora: stato "non collegato" con istruzioni.

### 5.5 Cosa hanno in comune le stanze
Header della stanza, agenti della stanza, task (kanban e lista), approvazioni della stanza, memoria della stanza, attività
della stanza, "chiedi a Guardian su questa stanza" (contesto minimo), azioni rapide contestuali.
Riusa i pannelli già esistenti in `guardian-web/src/ui/panels/` con un filtro per stanza: niente copie.

---

## 6. GUARDIAN — IL NUCLEO VIVO

### 6.1 Macchina a stati (già ricercata in `docs/ricerca-jarvis-ui.md`: applicala, non riscoprirla)
Stati visivi: `idle, listening, thinking, speaking, working (coordina N agenti), approval, error, offline`.

- Ogni stato ha colore, moto **e** testo. Crossfade tra stati di circa 500 ms, con isteresi e tempo minimo per stato (niente
  sfarfallio).
- Respiro a riposo: due sinusoidi lente non sincrone, ampiezza ~3%.
- **speaking**: scala e glow guidati dal livello audio reale della voce in uscita.
  - Con la Web Speech API il livello non è accessibile: in quel caso si usa un inviluppo morbido, *dichiarato*.
  - Con l'audio generato in proprio (WebAudio) si usa un AnalyserNode con FFT 256, RMS e inviluppo con attacco rapido e
    rilascio lento.
- **listening**: onde dal livello del microfono reale (AnalyserNode sullo stream). Mai simulato.
- `prefers-reduced-motion`: sostituisci scala e rotazioni con dissolvenze di opacità.

### 6.2 Testo di stato e sottotitoli
Una riga generata dai dati ("Coordino 2 agenti · 1 approvazione in attesa"). Durante la conversazione, sottotitoli live di
ciò che Guardian capisce (STT parziale) e di ciò che dice (frase corrente).

### 6.3 Tre livelli di presenza
- **Orbita**: grande, al centro.
- **Compatto**: angolo in alto a sinistra quando una stanza è aperta.
- **Mini**: icona animata nella barra in basso su telefono.

Lo stato e la conversazione sono gli stessi nei tre livelli, senza ricaricare nulla.

---

## 7. MODALITÀ CONVERSAZIONE — VOCE IN TEMPO REALE (requisito forte del titolare)

Il titolare vuole parlare con Guardian e sentirlo rispondere **subito, a voce, come una conversazione**. Implementala come
modalità esplicita.

### 7.1 Comportamento
- Pulsante grande "Conversazione" (e comando vocale "Guardian, parliamo").
  - All'attivazione: permesso del microfono, nucleo in `listening`, sottotitoli accesi.
  - Mani libere: **VAD** rileva l'inizio e la fine della frase; dopo circa 800–1000 ms di silenzio la frase parte.
    I parametri di `mic_continuo` sono il punto di partenza.
- Guardian risponde **a voce, frase per frase** (inizia a parlare appena è pronta la prima frase, senza aspettare la risposta
  intera) e con il testo nei sottotitoli.
- **Barge-in**: se il titolare riprende a parlare mentre Guardian parla, Guardian si zittisce subito e ascolta.
- Guardian non ascolta se stesso: cancellazione dell'eco del browser (`echoCancellation`), microfono "sordo" mentre parla
  (tranne il rilevamento del barge-in sopra una soglia), come già fa `mic_continuo`.
- Uscita: pulsante, `Esc`, "Guardian, basta", oppure 60 s di silenzio (configurabile).
- Mai l'indicatore "in ascolto" senza microfono davvero aperto. Mai registrazioni salvate senza consenso esplicito.

### 7.2 Obiettivi di latenza (da misurare e mostrare in Impostazioni → Diagnostica voce)
- fine frase → testo riconosciuto: < 700 ms (locale) / < 1,2 s (cloud);
- testo → prima frase parlata: < 1,5 s per gli intenti deterministici, < 3 s con un modello;
- barge-in → silenzio: < 200 ms.

### 7.3 Pipeline (strategia a livelli: usa il migliore disponibile e dichiara quale)

| Livello | Ascolto (STT) | Risposta (TTS) | Dove | Privacy | Costo |
|---|---|---|---|---|---|
| **A — PC del titolare (preferito)** | sherpa-onnx + Parakeet v3, **già funzionante** | voce di sistema «Elsa» frase per frase, o TTS locale (es. Piper, da valutare) | servizio vocale **solo su 127.0.0.1** avviato dal bridge | audio mai fuori dal PC | 0 € |
| B — browser | Web Speech API `SpeechRecognition` | `speechSynthesis` | qualsiasi browser che la supporti | Chrome invia l'audio ai server di Google: **dichiaralo** | 0 € |
| C — API realtime | provider STT/TTS in streaming | idem | Edge Function (chiavi lato server) | audio al provider | **a pagamento → ✋ approvazione del titolare** |

**Livello A nel web.** `guardian-web` aperto sul PC del titolare parla con un piccolo server locale del bridge
(`http://127.0.0.1:<porta>`), che riceve WAV o PCM, trascrive con sherpa-onnx e restituisce il testo.
- Requisiti di sicurezza:
  - ascolto solo su loopback, mai `0.0.0.0`;
  - token locale casuale e origini CORS ammesse solo per il dominio dell'HQ;
  - gestione del preflight Private Network Access di Chrome;
  - nessun comando eseguibile.
- Il browser rileva se il servizio locale risponde e, se no, passa al livello B. Il livello in uso compare nei sottotitoli
  ("Ascolto locale · privato").
- Sul telefono il livello A non c'è: si usa B (o C se approvato).

### 7.4 Il "cervello" della conversazione (vedi §8)
Prima il **router di intenti** deterministico (istantaneo, gratuito, onesto). Se non basta, il cervello configurato (§8).
In conversazione le risposte sono **brevi** (2–3 frasi parlate) con la possibilità di "dimmi di più".

### 7.5 Comandi vocali minimi
"apri Vendite / Sviluppo / Amministrazione", "torna al centro", "cosa è bloccato", "riepilogo", "approva la richiesta X"
(apre l'approvazione e **chiede conferma a voce e con un clic**: mai approvazioni solo vocali), "crea un task per Niko: …"
(anteprima e conferma), "silenzio", "basta".

---

## 8. IL CERVELLO DI GUARDIAN E I MODELLI

### 8.1 Opzioni (presenta in Plan mode, raccomanda, aspetta ✋)
1. **Cervello sul PC del titolare con Claude Code** (raccomandata come prima scelta, costo zero aggiuntivo):
   - l'HQ scrive la domanda in una tabella `guardian_richieste` (RLS: solo membri), con il contesto minimo;
   - il bridge sul PC di Menotti la prende, chiama `claude -p` (come già fa `dashboard/chat.py`) in **modalità sola risposta**:
     niente strumenti che modificano file e niente comandi senza approvazione;
   - scrive la risposta a pezzi (streaming per frasi) in `guardian_risposte`; Realtime la porta all'HQ, che la legge a voce.
   - Funziona da qualsiasi dispositivo, ma **solo quando il PC del titolare è acceso**: l'HQ lo mostra ("Cervello: PC di
     Menotti online / offline").
   - Rispetta i limiti dell'abbonamento: mostra l'utilizzo e degrada al router di intenti vicino al limite.
2. **Provider via API** tramite una Supabase Edge Function, con il router già scritto in `guardian/providers`:
   gratuiti/OpenAI-compatibili (FreeLLMAPI, OpenRouter con modelli free, Ollama sul PC) oppure a pagamento solo con
   `GUARDIAN_ALLOW_PAID=1` ✋.
3. **Solo intenti deterministici** (già esistente): ripiego sempre disponibile.

**Non** usare né simulare gli account personali di Claude o Codex fuori da questi canali autorizzati. Il fallback tra provider
è una cosa; il passaggio di un task tra agenti (handoff) è un'altra: non confonderli.

### 8.2 Smistamento del lavoro ("far lavorare le 3 IA")
- Dalla conversazione o dalla palette: "Guardian, prepara le bozze per i 5 clienti di Quartu" →
  - **anteprima**: task proposti, stanza, agente, modello consigliato, approvazioni previste;
  - Conferma → task reali assegnati;
  - il bridge del PC giusto li mostra all'agente (inbox / `claim`).
  - Niente esecuzione automatica sui PC senza l'ondata dedicata e l'approvazione (§14, ondata 6).
- Pannello **Modelli e quote**: per ogni agente modello in uso, utilizzo reale (dove esiste), limiti noti, stato del provider,
  costo stimato solo se dichiarato come stima.
- Regole di assegnazione: capacità, stanza, carico, disponibilità (`guardian/planner/assign.py` è la base; portala in SQL o
  riusala).

---

## 9. DESIGN JARVIS — DIREZIONE VISIVA

Parti dai token esistenti (`guardian-web/src/styles/tokens.css`, "Cyan Ops" validato) e dalle ricerche già fatte (§1.1).
Obiettivo: **più vivo e cinematografico, senza perdere leggibilità né velocità.**

1. **Profondità a strati**: fondo con griglia prospettica leggerissima, piano medio delle stanze, primo piano dei pannelli.
   Parallasse minima al movimento del puntatore (≤ 6 px, disattivata con reduced-motion e su telefono).
2. **Cornici HUD**: angoli tagliati (`clip-path`), linee di 1 px, etichette maiuscole con tracking. Glow solo su bordi e
   elementi attivi, mai sul testo dei dati.
3. **Colore d'identità per stanza** (tenue: un bordo, un alone), più l'accento ciano di Guardian. Colori di stato riservati,
   sempre con icona e testo.
4. **Mappa operativa** (nuova vista, attivabile nel centro): grafo vivo `persone → agenti → task → aziende` disegnato in SVG o
   canvas.
   - Un collegamento esiste solo se c'è un'assegnazione, un handoff o una dipendenza reale.
   - Un "impulso" corre lungo il collegamento quando arriva un evento Realtime che lo riguarda.
   - Clic su un nodo → pannello.
5. **3D (opzionale, a fasi, ✋ sul look)**: nucleo 3D in Three.js / React Three Fiber (reattore a strati con shader emissivo,
   audio-reattivo) oppure il busto WebGL già creato da Niko (`codex/dashboard`, CC0), riusato dopo l'accordo.
   - Caricamento lazy, fallback all'SVG attuale, pausa con `document.hidden`, DPR ≤ 2, budget di 2 ms per frame a riposo.
   - Niente asset di terzi senza licenza chiara.
6. **Suoni (opt-in, spenti di default)**: tre microsuoni sintetizzati con WebAudio (apertura, conferma, allerta), volume basso,
   rispettano l'orario di silenzio.
7. **Microinterazioni**: numeri che scorrono quando cambiano (solo con un nuovo dato reale), evidenziazione di 1,5 s della riga
   appena aggiornata da Realtime, skeleton eleganti, toast con l'azione "Apri".
8. **Modalità parete (TV/secondo monitor)**: vista a tutto schermo per la sede, senza controlli sensibili, con scorrimento lento
   delle stanze e voce degli annunci critici (opt-in).
9. **Tipografia**: sans per il testo, mono per numeri/ID/log con cifre tabellari. Corpo ≥ 14 px.
10. **Budget**: nessun `backdrop-filter` a tappeto (vedi la diagnosi in `docs/stile-basic.md`), solo transform/opacity
    nelle animazioni, CPU a riposo < 2%, bundle iniziale < 250 KB gzip (oggi 76 KB), 3D e mappa caricati a parte.

Per ogni scelta estetica importante fai **due varianti visibili** (screenshot) e lascia scegliere il titolare ✋. Il gusto è suo.

---

## 10. FLUIDITÀ E DINAMICITÀ (requisiti misurabili)

- Nessun ricaricamento di pagina. Navigazione tra centro, stanze e pannelli con transizioni condivise (View Transitions API se
  supportata, altrimenti FLIP), 200–450 ms.
- Aggiornamenti **ottimistici** con rollback: la UI cambia subito e torna indietro con un messaggio se il DB rifiuta.
- Realtime con **merge incrementale** dei singoli record, invece di ricaricare tutto a ogni evento (oggi ricarica lo snapshot
  con un debounce: miglioralo). Indicatore "Live" solo a canale sottoscritto.
- **Presence**: chi dei tre è nell'HQ adesso (Supabase Presence), con l'avatar in alto. Nessun tracciamento oltre a questo.
- Liste lunghe virtualizzate. Interazioni < 100 ms; INP < 200 ms misurato.
- Installabile come **PWA** (icona sul telefono, schermata di avvio). Le notifiche push arrivano dopo, con un'ondata dedicata ✋.

---

## 11. DATI: VERITÀ E CATALOGO

- Aggiorna `guardian-web/PIANO.md`: **ogni nuovo numero** entra nel catalogo con definizione, fonte, aggiornamento e stato
  vuoto. Niente catalogo, niente numero.
- Nuove tabelle solo con migrazione additiva, RLS, controllo in `tests/pg/check_00N.sql` e parità in `SqliteStore` (se il
  Guardian classico la usa).
- In demo (`VITE_DEMO=1`) i dati d'esempio coprono anche le stanze, ma il banner resta sempre visibile e la demo non tocca mai
  Supabase.

---

## 12. CONTRATTO DEI CONTROLLI

Per ogni ondata aggiorna in `PIANO.md`:
- la **tabella dei controlli**: controllo, dove, azione, effetto, metodo dati, feedback ok e feedback errore;
- la tabella dei **controlli disabilitati** con il motivo.

Un pulsante che non fa nulla è un bug bloccante. Lo stesso vale per i comandi vocali: ogni comando ha un effetto definito e un
test.

---

## 13. TEST E VERIFICA (a ogni ondata)

1. Verdi: `npm test`, `npm run e2e` (in `guardian-web/`), `python -m pytest -q tests`, `bash tests/pg/run.sh`.
2. E2E nuovi per ogni funzione: stanze (apri, chiudi, `Esc`, centro sempre attivo), kanban (sposta e vincolo rifiutato),
   conversazione (con STT finto iniettato nei test: simulare il **microfono** nei test è lecito, non lo è nell'app), barge-in,
   comandi vocali, mappa, presenza (due contesti browser).
3. Screenshot a 390, 768, 1280 e 1920 px, **guardati**. Axe senza violazioni serie. Console pulita.
4. Misure: latenze della voce (§7.2), INP, CPU a riposo, peso del bundle. Riportale nel checkpoint.
5. Niente "fatto" senza prove (output dei comandi e screenshot).

---

## 14. ROADMAP A ONDATE (il ciclo continuo)

Crea e mantieni `guardian-web/ROADMAP.md`, con le ondate e il loro stato. Ogni sessione ne completa una (o una parte, chiusa
bene). Ordine consigliato:

| Ondata | Contenuto | Dipende da | ✋ Decisioni del titolare |
|---|---|---|---|
| 0 | Allineamento: eseguire o aggiornare la fotografia §1, chiudere il passaggio di amico1 (registro sulla plancia team), decidere il destino della PR #2 | — | accordo con Niko sulla PR #2 |
| 1 | **Tre stanze**: modello dati (`stanze`), layout orbita, stanza espansa, filtri per stanza, demo aggiornata | 0 | colori e nomi delle stanze (2 varianti) |
| 2 | **Conversazione vocale livello B** (browser): modalità conversazione, VAD, frase per frase, barge-in, sottotitoli, comandi vocali, diagnostica | 1 | voce preferita |
| 3 | **Voce livello A**: servizio vocale locale nel bridge (sherpa-onnx già pronto), rilevamento automatico, misure di latenza | 2 | ok a far girare il servizio sul PC |
| 4 | **Cervello sul PC** (`guardian_richieste` / `guardian_risposte` + bridge con `claude -p` in sola risposta) | 2 | ok all'uso dell'abbonamento Claude Code |
| 5 | **Stanza Vendite** completa (pipeline senza dati personali, bozze con approvazione) | 1, PC di Niko | migrazione `vendite_pipeline` |
| 6 | **Smistamento del lavoro** dalla conversazione (anteprima → task → inbox dell'agente); poi esecuzione assistita sul PC con conferma locale | 4 | modello di minaccia approvato |
| 7 | **Stanza Amministrazione** (scadenze, documenti, costi manuali, calendario se autorizzato) | 1 | migrazione `costi`, connettore Calendar |
| 8 | **Mappa operativa** animata, Realtime incrementale, aggiornamenti ottimistici, presence | 1 | — |
| 9 | **3D e suoni**: nucleo 3D audio-reattivo o busto WebGL di Niko, microsuoni opt-in, modalità parete | 2 | scelta del look 3D (2 varianti) |
| 10 | PWA, notifiche push (Edge Function), briefing vocale del mattino opt-in | 4 | ok alle notifiche |

Dopo l'ondata 10 il ciclo continua con le idee raccolte in `ROADMAP.md › Idee` (ogni sessione ne aggiunge al massimo 3,
concrete e verificabili, con la fonte se vengono dal web).

---

## 15. CHECKPOINT E CONTINUITÀ

Alla fine di ogni ondata, o quando l'utilizzo si avvicina al limite:
1. Ferma le modifiche non essenziali. Nessun file a metà.
2. Aggiorna `GUARDIAN_STATUS.md`, `GUARDIAN_HANDOFF.md`, `GUARDIAN_TASKS.md`, `GUARDIAN_DECISIONS.md`,
   `guardian-web/ROADMAP.md` e `guardian-web/PIANO.md`: fatto, file, test con output, misure, problemi, **prossimo passo preciso**.
3. Se il bridge è configurato: `python bridge/guardian_bridge.py checkpoint --summary … --next … --tests-pending … --to-agent …`.
4. Riga di registro, commit e push sul tuo branch.
5. Al titolare: **5 righe in italiano semplice** (cosa vede di nuovo, cosa deve fare lui, cosa viene dopo) + 2 screenshot.

---

## 16. REGOLE ASSOLUTE

1. Niente dati, stati, attività, voci "in ascolto" o "Live" finti.
2. Il centro (Guardian) non scompare mai; la conversazione non si perde mai.
3. Ogni controllo e ogni comando vocale fa qualcosa di reale, oppure è disabilitato con il motivo.
4. Nessuna azione esterna senza approvazione registrata; nessuna approvazione solo vocale.
5. Nessun segreto nel client, nel repo o nei log; nessun dato personale dei clienti nel DB condiviso.
6. Codex Vendite fa solo vendite.
7. Non rifare ciò che esiste (§1.1): riusa, integra, cita.
8. Ondate piccole, testate, salvate. Mai dichiarare "fatto" senza prove.
9. Le decisioni ✋ le prende il titolare: proponi due opzioni chiare con una raccomandazione.
10. Bellezza sì, ma leggibilità, velocità e accessibilità prima.

---

## 17. ISTRUZIONE FINALE

Parti in **Plan mode**:
1. verifica l'inventario §1 con `git fetch` e la lettura dei file indicati;
2. elenca le skill lette e cosa applichi;
3. presenta il piano dell'**Ondata 0 + Ondata 1**, con le decisioni ✋ formulate come scelte semplici (due opzioni, una
   consigliata);
4. aspetta l'ok.

Poi esegui, verifica, salva il checkpoint, mostra al titolare cosa è cambiato e proponi l'ondata successiva. Ripeti finché
Guardian HQ non è il posto da cui il titolare guida davvero, a voce, il lavoro delle sue tre IA.

*Il centro resta vivo. La voce risponde davvero. Ogni stanza lavora. Ogni numero è vero.*
