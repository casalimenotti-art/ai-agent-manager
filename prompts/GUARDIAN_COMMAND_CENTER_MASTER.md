# GUARDIAN — CENTRAL COMMAND DASHBOARD

## Prompt master per Codex / Claude Code · Ecosistema NEXO · Plan mode → implementazione a fasi

> Versione 2 (27/11/2026). Nasce dal prompt di esempio scritto con ChatGPT e lo migliora così:
> 1) parte dal **codice che esiste davvero** in questo repository, invece di immaginare un'app nuova;
> 2) costringe a una **decisione architetturale esplicita**, con raccomandazione;
> 3) definisce un **criterio di accettazione verificabile** per ogni requisito;
> 4) rende **misurabile l'onestà dei dati**: ogni numero ha una fonte, ogni pulsante un contratto;
> 5) integra le regole del repo (AGENTS.md, registro, branch, segreti) e un budget di token.
>
> Uso: incolla tutto il file come primo messaggio a Codex (o Claude Code) aperto nella radice del repo
> `casalimenotti-art/ai-agent-manager`. L'agente **deve partire in Plan mode** e aspettare l'approvazione del titolare
> prima di modificare file.

---

## 0. MISSIONE

Non stai costruendo una dashboard qualunque. Stai progettando e realizzando **l'interfaccia di comando centrale di Guardian**,
il sistema che coordina gli agenti AI dell'ecosistema NEXO: tre collaboratori (Menotti con Claude Code, due soci con Codex),
più agenti, più attività (le "aziende" di NEXO), task, approvazioni, memoria e handoff.

Chi apre Guardian deve capire **in meno di 5 secondi, senza cliccare**:

1. se il sistema è sano (database, bridge dei PC, aggiornamento dati);
2. quali agenti stanno **davvero** lavorando, quali aspettano, quali sono in errore;
3. quali task sono in esecuzione, bloccati o falliti;
4. quali approvazioni aspettano una persona;
5. cosa sta facendo Guardian in questo momento;
6. **cosa Guardian consiglia di fare adesso** (prossime azioni).

L'atmosfera deve ricordare il centro di comando di un'intelligenza artificiale avanzata, ispirata all'immaginario di
JARVIS e dei sistemi di Tony Stark. Deve però restare **un design originale**: niente loghi, nomi, suoni o forme
riconoscibili di proprietà Marvel o Disney. Deve essere spettacolare alla prima apertura e comodo da usare ogni giorno,
da un monitor grande come da un telefono.

Tre parole guida: **Intelligenza · Controllo · Consapevolezza.**

- *Intelligenza*: Guardian capisce le richieste, propone piani e coordina gli agenti.
- *Controllo*: ogni azione sensibile passa da una persona; si vede sempre chi ha deciso cosa.
- *Consapevolezza*: lo stato operativo reale è sempre visibile; nessun indicatore finto.

Regola d'oro dell'intero progetto: **meglio uno stato vuoto onesto che un numero inventato.**

---

## 1. REGOLE DEL REPOSITORY (obbligatorie, prima di tutto)

1. Leggi `AGENTS.md` e `CLAUDE.md`. Contengono regole condivise da tre persone:
   - lavora **solo sul tuo branch** (Codex: `codex/<area>`; Claude Code: `claude/*`), mai direttamente su `main`;
   - a fine di ogni fase scrivi una riga con `python registro/scrivi.py --chi <tuo-id> --agente <codex|claude-code> "…" --file … --esito …`;
   - poi fai commit e push sul tuo branch e apri una PR verso `main` solo quando il titolare lo chiede;
   - non modificare file di altri senza PR;
   - non inviare messaggi o email e non pubblicare nulla da solo.
2. Leggi `GUARDIAN_STATUS.md`, `GUARDIAN_TASKS.md`, `GUARDIAN_DECISIONS.md` e `GUARDIAN_HANDOFF.md`. Sono la memoria del
   progetto. **Non contraddire una decisione registrata** senza proporre esplicitamente di superarla e spiegare perché.
3. Mai segreti nel repo: `.env`, `bridge/.env`, `.streamlit/secrets.toml` e `*.db` sono in `.gitignore` e devono restarci.
   Nel client web può comparire solo la **anon key** di Supabase: la sicurezza vera sono le regole RLS. La `service_role` key
   non deve mai stare nel client.
4. Comandi vietati: `git reset --hard`, `git clean -fd`, force push, cancellazioni di massa, migrazioni distruttive.
   Le migrazioni SQL devono essere **additive e rieseguibili**.
5. Non rompere ciò che funziona: la suite `python -m pytest -q tests` deve restare verde (oggi ha 61 test) e
   `bash tests/pg/run.sh` deve stampare tutti i `CHECK … OK`.
6. **Budget di token**: non rileggere file già analizzati, non stampare file interi, niente documentazione ridondante.
   Lavora a fasi piccole e verificabili. Prima di un'attività lunga salva un checkpoint (§30).

---

## 2. PRIMA AZIONE — ANALISI DEL PROGETTO ESISTENTE (non assumere nulla)

Prima di scrivere codice, ispeziona e **conferma o correggi** questa fotografia (aggiornata al 27/11/2026).

### 2.1 Cosa esiste già

| Area | Dove | Stato |
|---|---|---|
| Dashboard attuale | `guardian/app.py` (Streamlit ≥1.41) + `guardian/ui/*.py` | 12 sezioni: Overview, Guardian, Agenti, Task, Progetti, Attività, Log, Handoff, Memoria, Approvazioni, Notifiche, Dispositivi. Funziona; controllata a 1280 e 390 px |
| Dominio e archivi | `guardian/core/` (`models.py`, `store.py`, `store_sqlite.py`, `store_supabase.py`) | Stessa API per SQLite (locale) e Supabase (condiviso). Validazioni e filtro segreti in `models.py` |
| Database condiviso | `supabase/migrations/001…004` | Tabelle: users, devices, agents, tasks, plans, activity_events, agent_logs, handoffs, approvals, notifications, memory, projects. RLS (admin/member), trigger, RPC del bridge. Provate su PostgreSQL 16 |
| Guardian Bridge | `bridge/` | Gira su ogni PC, solo HTTPS in uscita, token per PC. Ricava lo stato reale degli agenti dagli hook di Claude Code e dal `notify` di Codex. Comandi: claim, checkpoint, handoff-take, memory, sync del registro |
| Intelligence | `guardian/planner/`, `guardian/providers/` | Planner (obiettivo → piano → conferma → task), assegnazione deterministica, `report()` con le prossime azioni, router per provider OpenAI-compatibili (a pagamento esclusi di default) |
| Plancia locale | branch `claude/dashboard-pc`, `codex/dashboard` (PR #2), cartella `dashboard/` | Altra app Streamlit che gira solo sul PC di Menotti: voce offline (sherpa-onnx), avatar WebGL, lancio di `claude` CLI. **Non toccarla** senza una PR concordata. Il suo stile e i suoi asset (`theme.py`, reattore SVG, palette "Cyan Ops") sono **ispirazione riutilizzabile** |
| Test | `tests/`, `tests/pg/` | Pytest, AppTest di Streamlit, migrazioni su Postgres locale |

### 2.2 Stati reali (usa questi; non inventarne altri)

- **Task (10)**: `backlog, planned, ready, running, waiting, blocked, needs_approval, completed, failed, cancelled`.
  Etichette italiane suggerite: Da fare, Pianificato, Pronto, In esecuzione, In attesa, Bloccato, Da approvare,
  Completato, Fallito, Annullato.
- **Agenti (8)**: `online, offline, idle, working, waiting, needs_approval, error, unknown`.
  Lo stato mostrato si calcola con `models.stato_agente()`: diventa `unknown` se il bridge non lo aggiorna da 180 s.
  **La presenza del PC non rende "online" il suo agente.**
- **PC**: online solo se l'heartbeat ha meno di 120 s (`models.stato_dispositivo()`).
- **Approvazioni**: `richiesta, approvata, rifiutata`. Tipi: email, pubblicazione, contatto_cliente, spesa, pagamento,
  irreversibile, account_esterno, comando_pericoloso, altro.
- **Handoff**: `aperto → preso → chiuso`.
- **Gravità degli eventi**: `info, warning, error, critical`.

### 2.3 Mappa dei concetti del brief sui dati reali

| Concetto del brief | Dato reale | Cosa fare |
|---|---|---|
| Aziende / business | `projects` (nome, descrizione, stato) | Usa i progetti come "aziende". Se servono categoria, metriche o clienti, proponi una **migrazione 005 additiva** (es. `projects.tipo`, tabella `project_metrics` con fonte e data). Nessuna azienda d'esempio nel DB reale |
| Workflow | **Non esiste un motore di workflow** | Non creare un Workflow Monitor finto. Mostra lo stato "Non disponibile: nessun motore di workflow collegato" oppure proponi in Plan mode un modello minimo (es. task ricorrenti) e chiedi l'approvazione |
| Progresso % dei task | Non esiste un campo progresso | Non inventare percentuali. Usa lo stato e il "prossimo passo"; un progresso reale si può derivare solo da elementi verificabili (es. task figli completati / totali) |
| Ricavi e spese | Non esistono | Stato "non disponibile" finché non esiste una fonte reale e approvata |
| Comunicazione tra agenti | `handoffs`, `task_assigned`, `depends_on` | Disegna un collegamento solo quando esiste uno di questi legami |
| Voce | Solo nella plancia locale (offline). Nel cloud niente | Nel web si può usare la Web Speech API del browser, se presente (§8). Altrimenti il controllo è disabilitato con il motivo |
| Realtime | Oggi polling ogni 20 s in Streamlit | Supabase Realtime è attivo sul DB (pubblicazione `supabase_realtime`), ma va consumato da un client che lo supporti (§3) |

### 2.4 Cosa consegnare a fine analisi

Una **valutazione architetturale sintetica** (massimo una pagina): cosa funziona, cosa manca, rischi, debito tecnico.
Più l'elenco delle skill lette (§4). Poi il **piano di implementazione** (§29) da far approvare.

---

## 3. DECISIONE ARCHITETTURALE (da presentare in Plan mode, con raccomandazione)

Il brief chiede pannelli laterali che non sostituiscono la vista centrale, Ctrl/Cmd+K, aggiornamenti in tempo reale e voce.
Streamlit fa una parte di queste cose (`st.dialog`, `st.fragment`, componenti custom), ma con limiti:
ogni interazione rilancia lo script, i pannelli sono solo modali, la tastiera globale non c'è e Realtime arriva solo tramite polling.

Presenta **due opzioni**, con costi e rischi, e raccomanda la B.

**Opzione A — Streamlit potenziato** (`guardian/app.py`)
- Pannelli con `st.dialog`, aggiornamenti con `st.fragment(run_every)`, palette comandi e voce come componenti custom
  (`st.components.v1` con HTML/JS minimo).
- Pro: zero nuova infrastruttura, riusa tutto.
- Contro: niente push reale, pannelli limitati, animazioni e scorciatoie poco naturali.

**Opzione B — Web app dedicata `guardian-web/` (raccomandata, a fasi)**
- Stack: Vite + React + TypeScript + `@supabase/supabase-js` (Auth, query con RLS, **Realtime vero** su agents, tasks,
  approvals, notifications, activity_events). CSS con design token (CSS custom properties). Grafici con una libreria leggera
  o SVG fatto a mano.
- Hosting statico **gratuito** (Cloudflare Pages, Vercel o Netlify); stessa Supabase, stesse RLS, stesse RPC.
  **Nessun nuovo backend**.
- Le funzioni Python che servono al client (planner, router dei provider) restano in Python. Per esporle valuta, in ordine:
  - logica spostata in RPC SQL;
  - una Supabase Edge Function;
  - mantenere quelle sezioni in Streamlit.
  Mai una chiave provider nel browser.
- Streamlit **resta online come fallback/admin** finché la web app non ha parità funzionale; poi decide il titolare.
- Pro: drawer veri, Ctrl+K, Realtime, animazioni fluide, Web Speech API, mobile curato.
- Contro: un secondo frontend da mantenere, quindi serve una guida di deploy e test E2E.

Criterio di accettazione: la decisione è scritta in `GUARDIAN_DECISIONS.md` con data, motivazione e cosa resta invariato.
**Non iniziare l'implementazione prima dell'approvazione del titolare.**

Tutto ciò che segue vale **per entrambe le opzioni**. Dove dico "pannello" intendo drawer laterale (B) o `st.dialog` (A).

---

## 4. SKILL — USALE DAVVERO

1. Elenca le skill installate nel tuo ambiente (meccanismo di scoperta dell'agente) e quelle del progetto, se esistono.
2. Leggi le istruzioni **complete** di quelle pertinenti: frontend/UI-UX, design system, animazioni, React/Vite (se B),
   accessibilità, data visualization, test/Playwright, debugging, architettura.
   Sul PC del titolare risulta installata, tra le altre, `ui-ux-pro-max` (già usata per la palette "Cyan Ops"): se c'è, usala.
3. Per grafici, KPI e colori applica i principi di data visualization della §12.4. Se hai una skill di dataviz, seguila e
   **esegui il suo validatore di palette** invece di giudicare a occhio.
4. Non inventare skill. Non installare strumenti a pagamento. Se una skill manca, procedi con la migliore alternativa e scrivilo.
5. Nel piano scrivi quali skill hai letto e **quale regola concreta** ne hai preso (una riga per skill).

---

## 5. PRINCIPIO UX — IL CENTRO NON SCOMPARE MAI

Questo è il requisito più importante dopo l'onestà dei dati.

### 5.1 Centro permanente

La vista centrale (Command Center) resta montata e attiva **sempre**. Aprire "Agenti", un task, un'azienda o le statistiche
apre un **livello aggiuntivo** (drawer a destra, popover, modale per i compiti focalizzati) e non sostituisce la pagina.
La conversazione con Guardian, i filtri e lo scroll **non si perdono**.

### 5.2 Comportamento dei pannelli

Ogni pannello:
- si apre con una transizione breve (≈200–320 ms);
- ha un titolo e un pulsante Chiudi visibile, e si chiude anche con `Esc`;
- riporta il focus all'elemento che l'ha aperto;
- ha un URL condivisibile (es. `?pannello=task&id=42`; con B uso un router, con A `st.query_params`).

Gerarchia: **al massimo un drawer più un modale**. Un nuovo drawer sostituisce il precedente e lascia una traccia di
navigazione ("Agenti › Codex › Task #42") con il pulsante Indietro.
Su mobile il drawer diventa un pannello a tutta altezza che sale dal basso.

### 5.3 Guardian sempre raggiungibile

Da qualsiasi pannello l'utente può scrivere a Guardian, chiedere una statistica, un riassunto o cosa sta succedendo.
La barra di input di Guardian è fissa: in basso al centro su desktop, in basso su mobile.

Criterio di accettazione: un test E2E apre e chiude in sequenza 5 pannelli diversi e verifica che la conversazione,
lo scroll e la vista centrale siano invariati.

---

## 6. DIREZIONE VISIVA E DESIGN SYSTEM

Fusione originale di: centro di comando di un'IA avanzata, mission control, SOC di cybersecurity e software premium.
**Non** un template admin generico con card bianche e bottoni blu standard.

### 6.1 Token (CSS custom properties, un solo file sorgente)

- **Superfici**: nero mezzanotte (fondo), grafite (pannelli), grigio metallico scuro (bordi e elementi rialzati).
  Niente nero puro `#000`.
- **Accento**: ciano elettrico (intelligenza, elementi attivi, focus) e azzurro ghiaccio (secondario).
  Violetto solo come accento raro.
- **Stato (riservati, mai usati per le serie dei grafici)**: verde = sano, ambra = attenzione, arancio = serio,
  rosso = critico. **Sempre con icona e testo**, mai solo colore.
- **Testo**: bianco morbido (primario), grigio chiaro (secondario), grigio medio (terziario).
  Contrasto **AA** (≥ 4.5:1 per il testo normale, ≥ 3:1 per testo grande e icone) verificato con uno strumento, non a occhio.
- **Spaziatura** (4/8/12/16/24/32/48), **raggi** (6/10/16), **ombre**, **blur** (selettivo), **z-index**, **larghezze dei
  pannelli** (360/480/720), **breakpoint** (≤640, ≤1024, ≥1440, ≥1920), **motion** (§19.1).

Riparti dalla palette "Cyan Ops" della plancia locale (`dashboard/theme.py` sul branch `claude/dashboard-pc`) se è coerente:
tiene una continuità visiva per il titolare.

### 6.2 Sfondo

Gradiente radiale scurissimo, griglia tecnica a bassa opacità, luce ambientale soffusa.
Particelle animate solo se costano meno dell'1–2% di CPU a riposo, e sono disattivate con `prefers-reduced-motion`.
Lo sfondo non compete mai con i dati.

### 6.3 Vetro e profondità

Glassmorphism **selettivo**, solo sui livelli sovrapposti (drawer, palette comandi, header).
Le card dei dati restano opache per la leggibilità.

### 6.4 Tipografia

- Sans-serif moderna e molto leggibile per l'interfaccia.
- Monospace tecnica solo per ID degli agenti, timestamp, log, telemetria e numeri tabellari (cifre tabellari).
- Font self-hosted o di sistema: niente dipendenze esterne che rompano la privacy o la velocità.

### 6.5 Icone

Un unico set di icone lineari (es. Lucide), di dimensioni coerenti. **Niente emoji come sistema di icone.**
Oggi la UI Streamlit ne usa: vanno sostituite.

Criterio di accettazione: esiste una pagina o storia "Design system" con tutti i token e i componenti nei loro stati
(normale, hover, focus, attivo, disabilitato, caricamento, errore, vuoto), sia scura sia, se prevista, chiara.

---

## 7. IL NUCLEO DI GUARDIAN (centro visivo e funzionale)

### 7.1 Identità

Un nucleo astratto: un anello o un "reattore" a strati, oppure una forma d'onda.
La plancia locale ha già un reattore SVG con 4 stati: **riusa l'idea, non i file di un altro branch senza PR**.
Dimensione: imponente ma non dominante (≤ 25% dell'area visibile su desktop).

### 7.2 Stati operativi, collegati a stati reali

| Stato visivo | Quando (fonte reale) |
|---|---|
| Online / a riposo | DB raggiungibile, nessuna richiesta in corso |
| In ascolto | Microfono **effettivamente** attivo (permesso concesso e stream aperto) |
| Sto pensando / pianificando | Richiesta al planner o al router in corso |
| Coordino N agenti | N agenti con stato `working` (da `agents`) |
| In attesa di approvazione | Esiste almeno un'approvazione `richiesta` |
| Rispondo | Risposta in streaming o in voce in corso |
| Errore | Ping del DB fallito o errore del provider |
| Offline | Nessuna connessione |

**Nessuna animazione che simuli attività quando non ce n'è.** Il testo di stato è generato dai dati
(es. "Coordino 2 agenti · 1 approvazione in attesa"), mai da frasi fisse.

### 7.3 Conversazione centrale

- Input testuale sempre visibile, cronologia compatta, risposte in streaming se il provider lo supporta,
  voce se disponibile (§8), contesto del pannello aperto (§23).
- Le richieste dell'utente seguono **due binari**:
  1. **Router di intenti deterministico** (funziona senza nessun provider AI). Risponde dai dati a domande frequenti:
     "quanti agenti sono attivi", "task completati oggi", "cosa è bloccato", "approvazioni in attesa",
     "cosa consigli di fare", "riepilogo della giornata".
     Usa `guardian/planner/report.py` (`report()`, `testo_report()`) e le query degli store. Ogni risposta cita la fonte
     ("da 3 agenti, aggiornato 12 s fa") e può aprire il pannello pertinente.
  2. **Planner o LLM** solo per richieste aperte ("pianifica…", "prepara…"), tramite il router dei provider.
     Se non c'è un provider: "Planner non disponibile" e mai una risposta inventata.
- Creare task, delegare a un agente o richiedere un'approvazione dalla chat produce sempre **un'anteprima con Conferma**:
  nulla diventa reale senza un clic umano.

Criterio di accettazione: con zero provider configurati, le 6 domande d'esempio ricevono una risposta corretta e verificabile
dai dati di test.

---

## 8. VOCE (solo dove funziona davvero)

- **Opzione B**: Web Speech API (`SpeechRecognition` e `speechSynthesis`) solo se il browser la supporta.
  Verifica con feature detection e chiedi il permesso al primo uso. Su Chrome il riconoscimento può passare dai server del
  browser: **dichiaralo nelle impostazioni della voce**.
- **Opzione A**: componente custom con la stessa API, oppure il pulsante resta disabilitato.
- Stati visibili: microfono attivo, elaborazione, Guardian parla, voce non disponibile (con il motivo).
  **Mai l'indicatore "in ascolto" se il microfono non è aperto.**
- Annunci proattivi (task completato, approvazione richiesta, errore critico): con livelli configurabili
  (Silenzio / Solo critici / Importanti / Tutti), silenzio di default di notte (orario configurabile) e un massimo di
  annunci all'ora. Si fermano con un clic o con `Esc`.
- L'utente può sempre: silenziare Guardian, disattivare la voce, interrompere un annuncio, tornare al testo.

Criterio di accettazione: su un browser senza Web Speech i controlli vocali sono disabilitati con un tooltip esplicativo
e nessun errore in console.

---

## 9. FLOTTA DEGLI AGENTI

- Caricata **dinamicamente** dalla tabella `agents`: nessun numero fisso di agenti.
- **Card**: nome, tipo (claude-code/codex/api/manuale), collaboratore e PC, stato reale (`stato_agente`), task corrente,
  ultimo segnale, ultima attività, utilizzo 5h/7g (`usage`, solo se presente), errore, capacità.
- **Clic → pannello agente**: identità, capacità, task corrente e recenti (dai task con `assigned_agent_id`),
  log recenti (`agent_logs`, con i filtri), handoff in uscita e in entrata, errori.
  Azioni reali:
  - "Assegna un task" (aggiorna `assigned_agent_id`);
  - "Segna come non disponibile" (aggiorna `disponibile`);
  - "Apri handoff".
- **Feed di attività degli agenti**: righe brevi generate dagli eventi reali (`activity_events` con `agent_id`), es.
  "Codex (amico1) ha preso il task #42". Mai frasi inventate.
- **Collegamenti visivi** tra agenti solo se esiste un handoff, un'assegnazione o una dipendenza reale.

---

## 10. ECOSISTEMA DELLE AZIENDE (= progetti)

- Card dinamiche da `projects`: nome, stato, task aperti e completati, agenti coinvolti (distinti dai task),
  ultimo evento, avvisi (task falliti o bloccati, approvazioni).
- Pannello: panoramica, task, agenti, memoria del progetto (`memory`), eventi, approvazioni.
  Metriche economiche solo con una fonte reale (§2.3).
- Creazione di un'azienda: modulo reale (`create_project`). **Mai aziende create in automatico o di esempio nel DB condiviso.**

---

## 11. TASK — IL CUORE OPERATIVO

- Nella vista centrale: i task **attivi più importanti** (running, needs_approval, blocked, failed, poi ready per priorità),
  massimo 6–8, con "vedi tutti".
- Card: titolo, stato (etichetta + icona), priorità, agente, azienda, ultimo aggiornamento, prossimo passo.
  **Niente % di progresso inventate.**
- Pannello del task:
  - descrizione, piano di origine (`plan_id`), risultato atteso e criteri;
  - dipendenze (cliccabili);
  - handoff e memoria del task (incluso il "punto di ripresa");
  - cronologia (`events(task_id=…)`), errore e risultato.
- Azioni reali, con i vincoli che già esistono nel DB:
  - cambio stato e priorità;
  - assegnazione;
  - richiesta di approvazione;
  - handoff.
  Il DB rifiuta i duplicati, il secondo task `running` per lo stesso agente e i task `ready` con dipendenze aperte:
  **mostra quei messaggi in modo leggibile**.
- Pausa, ripresa e retry **non esistono come esecuzione automatica**: puoi offrire "Metti in attesa" (stato `waiting`) e
  "Riporta a pronto", non un "Riprova" che fingerebbe di rieseguire.

---

## 12. STATISTICHE OPERATIVE

### 12.1 Catalogo delle metriche (da consegnare nel piano)

Una tabella con **ogni** numero mostrato:

| Metrica | Definizione | Fonte (tabella, RPC o funzione) | Aggiornamento | Stato se manca |
|---|---|---|---|---|

Esempi:
- agenti al lavoro (`stato_agente ∈ {working, waiting, needs_approval}`);
- task per stato;
- task completati oggi (eventi `task_completed` di oggi);
- tasso di completamento (completed / (completed + failed + cancelled) in una finestra dichiarata);
- durata media (da `task_started` a `task_completed`, solo se entrambi esistono);
- approvazioni in attesa;
- PC online;
- errori nelle ultime 24 h.

### 12.2 Regole

Niente numeri casuali, niente valori fissi nel codice, niente grafici dimostrativi.
Durante il caricamento usa skeleton, mai zeri finti. Senza dati: stato vuoto curato.

### 12.3 Statistiche a voce o in chat

Le domande dell'utente passano dal router di intenti (§7.3), che apre il pannello Statistiche già filtrato.

### 12.4 Principi di grafici e KPI (dalla skill di data visualization)

1. **Prima la forma, poi il colore.** Spesso la risposta giusta **non è un grafico** ma una stat tile con il numero in
   evidenza, l'etichetta e il delta rispetto a un periodo dichiarato. Grafici solo dove raccontano qualcosa:
   - attività nel tempo (linea o area);
   - carico per agente (barre orizzontali);
   - stati dei task (barra segmentata o barre).
2. **Il colore segue il compito**:
   - categoriale (identità delle serie, ordine fisso, **mai rigenerato o ciclato**, oltre l'8ª serie si raggruppa in "Altro");
   - sequenziale (una tinta, dal chiaro allo scuro);
   - divergente (due tinte più un grigio neutro al centro);
   - stato (riservato ai colori di stato).
   - **Il colore segue l'entità, non la posizione**: un filtro non deve ricolorare gli agenti rimasti.
3. **Un solo asse Y.** Mai grafici a doppio asse: due misure diverse = due grafici.
4. **Valida la palette con uno script** (differenza percettiva tra coppie adiacenti anche per daltonici, ΔE ≥ 8 come
   obiettivo; contrasto) sul fondo scuro. Il tema scuro è una scelta di passi propri, non un'inversione automatica.
5. **Segni sottili**: linee da 2 px, estremità delle barre arrotondate ~4 px ancorate alla base, marker ≥ 8 px,
   2 px di spazio tra i segmenti. Griglia e assi recessivi.
6. **Testi nei colori del testo**, mai nel colore della serie. Legenda sempre presente con ≥ 2 serie, etichette dirette
   selettive (≤ 4 serie), mai un numero su ogni punto.
7. **Interazione di default**: crosshair e tooltip su linee e aree, tooltip per segmento su barre e celle,
   area di hover più grande del segno, filtri (periodo, azienda, agente) **in una riga sopra** i grafici.
8. **Accessibilità**: identità mai affidata al solo colore, vista tabellare alternativa per ogni grafico,
   texture disponibile per stampa e modalità ad alto contrasto.
9. **Renderizza e guarda**: screenshot a 1280 e 390 px per cercare etichette sovrapposte e overflow prima di dichiarare finito.

---

## 13. NOTIFICHE E CENTRO ATTIVITÀ

- Le notifiche esistono già (tabella `notifications`, una riga per destinatario, create da trigger per: approvazione
  richiesta o decisa, task fallito, agente in errore, handoff verso di te).
  Mostra il contatore non lette, la lista, "segna come letta" o "tutte lette".
- **Clic → pannello giusto**: `ref_table`/`ref_id` → task, agente, approvazione, handoff.
- Timeline attività: `activity_events` con filtri per gravità, tipo, collaboratore, agente, azienda, task e periodo,
  e paginazione o virtualizzazione.
- Mai notificare eventi banali. Le notifiche sonore o vocali seguono i livelli della §8.

---

## 14. CENTRO APPROVAZIONI

- Lista: in attesa (in alto, con il contatore nell'header), approvate e rifiutate (storico).
- Dettaglio: azione proposta, **tipo**, agente o persona che la propone, **motivo**, **impatto previsto**,
  **dati coinvolti**, task collegato, chi ha deciso e quando.
- Azioni: Approva / Rifiuta (già reali). "Chiedi modifiche" **non esiste** nel DB: se serve, proponi una migrazione
  additiva (es. stato `modifiche_richieste` + commento) e falla approvare.
  Le approvazioni "scadute" non esistono: non mostrarle finché non c'è una regola reale.
- Guardian **registra** la decisione e non esegue l'azione esterna. Scrivilo nell'interfaccia.

---

## 15. WORKFLOW

Oggi non c'è un motore di workflow (vedi §2.3). Niente monitor finto. Due scelte da presentare in Plan mode:
1. una sezione "Workflow" con stato vuoto onesto e una spiegazione;
2. una proposta minima (es. task ricorrenti con pianificazione, tabella dedicata, esecuzione **solo manuale**
   o tramite agenti con approvazione) come fase separata.

---

## 16. PALETTE COMANDI (Ctrl/Cmd + K)

- Ricerca veloce su agenti, aziende, task, approvazioni, memoria e azioni ("Nuovo task", "Riepilogo di oggi",
  "Apri approvazioni").
- Linguaggio naturale: passa dal router di intenti (§7.3); "Apri i task bloccati" apre il pannello filtrato.
- Navigabile da tastiera, con risultati raggruppati e scorciatoie mostrate.
- Opzione A: componente custom e, se non è affidabile, un pulsante "Cerca" ben visibile.

---

## 17. NAVIGAZIONE

Barra laterale compatta (desktop) o barra in basso (mobile). Le voci **aprono pannelli** e non sostituiscono il centro:
Command Center, Agenti, Aziende, Task, Approvazioni, Memoria, Handoff, Attività/Log, Statistiche, Dispositivi, Impostazioni.
La voce attiva è evidenziata. Chiudendo un pannello si torna allo stato precedente.

Mappa le 12 sezioni Streamlit attuali su questa struttura nel piano: **nessuna funzione esistente deve sparire**.

---

## 18. OGNI PULSANTE FUNZIONA (contratto obbligatorio)

Nel piano consegna la **tabella dei controlli**, una riga per ogni elemento interattivo:

| Controllo | Dove | Azione | Stato che cambia | Pannello | API / RPC / metodo store | Feedback ok | Feedback errore | Test |
|---|---|---|---|---|---|---|---|---|

E la **tabella dei controlli disabilitati**: perché è disabilitato, cosa serve per abilitarlo, testo del tooltip.
Un controllo che non fa nulla è un bug bloccante.

---

## 19. INTERAZIONE E MOVIMENTO

### 19.1 Motion

- Microinterazioni: 120–180 ms.
- Pannelli: 200–320 ms.
- Transizioni ampie: 300–450 ms.
- Curve di easing morbide e coerenti.
- Gli elementi importanti si muovono di più, lo sfondo quasi mai. Mai tutto animato insieme.

### 19.2 Stati

Hover, focus visibile, premuto, caricamento, successo, errore, disabilitato, vuoto: **per ogni componente**.

### 19.3 Accessibilità

- `prefers-reduced-motion`: niente animazioni non essenziali.
- Navigazione completa da tastiera, ordine del focus logico.
- Ruoli e etichette ARIA su pannelli, palette comandi e grafici; annunci `aria-live` per eventi critici.
- Target touch ≥ 44 px su mobile.

---

## 20. RESPONSIVE

- **Desktop (primario, 1440–2560 px)**: centro con Guardian, colonna agenti, colonna task e approvazioni,
  barra di stato in alto. Usa tutta la larghezza senza diventare dispersivo (griglia a 12 colonne).
- **Tablet**: meno card visibili, colonne collassabili, centro preservato.
- **Mobile (390 px)**: Guardian in alto o al centro, input fisso in basso, card compatte, pannelli come fogli a tutta
  altezza, **nessuno scroll orizzontale**, testo ≥ 14 px.
- Criterio: screenshot verificati a 390, 768, 1280 e 1920 px.

---

## 21. ARCHITETTURA DEI COMPONENTI

Componenti riutilizzabili e piccoli (niente file da 1000 righe):
Button, Card, Panel/Drawer, Modal, StatusPill, AgentCard, ProjectCard, TaskCard, ApprovalCard, NotificationItem,
MetricTile, Chart, SearchInput, CommandPalette, EmptyState, ErrorState, Skeleton, Tooltip.

Ogni componente riceve dati e non li inventa. Aggiungere un agente o un'azienda nel DB li fa comparire **senza toccare il codice**.

---

## 22. DATI E TEMPO REALE

- Usa gli **archivi e le RPC esistenti**:
  - opzione A: `SqliteStore`/`SupabaseStore`;
  - opzione B: `supabase-js` con le stesse tabelle, colonne e RLS (attenzione: `devices.token_hash` **non è leggibile**,
    è voluto).
- Non inventare campi senza controllare lo schema. Se ne serve uno nuovo: migrazione `00N_*.sql` additiva +
  `SqliteStore` allineato + controllo in `tests/pg/check_00N.sql`.
- Realtime:
  - B: sottoscrizioni su `agents`, `tasks`, `approvals`, `notifications`, `activity_events` (già nella pubblicazione),
    con riconnessione e indicatore "Live" **solo se il canale è sottoscritto**;
  - A: polling dichiarato ("aggiornato ogni 20 s") con backoff in caso di errore.
- Stati di caricamento (skeleton), vuoto (curato e utile) ed errore (messaggio leggibile, nessun dettaglio tecnico o segreto).

---

## 23. CONTESTO INTELLIGENTE

Con un pannello aperto, la domanda a Guardian riceve il **contesto minimo** dell'entità
(es. id e stato del task, ultimi 5 eventi, prossimo passo). Mai dati personali dei clienti, mai log interi.
Il router di intenti usa lo stesso contesto ("perché questo task è bloccato?" → dipendenze aperte, approvazioni, errore).

---

## 24. AZIONI RAPIDE E RIEPILOGO

- Azioni rapide **contestuali**, al massimo 4–5 visibili, ordinate per urgenza dalle prossime azioni di `report()`:
  Nuovo task, Assegna, Apri approvazioni, Riepilogo di oggi, Nuova azienda.
- **Riepilogo giornaliero** generato dai dati: task completati e ancora attivi, errori, attività degli agenti, approvazioni,
  prossime azioni. Si può copiare o scaricare in Markdown. Opzionale: salvarlo in `memory` (tipo `risultato`, fonte "riepilogo del …").

---

## 25. SALUTE DEL SISTEMA

Indicatore compatto e pannello di dettaglio:
- app;
- database (ping con latenza);
- autenticazione;
- realtime (sottoscritto o in polling);
- bridge (PC online / totali);
- agenti con segnale;
- provider AI (configurati e utilizzabili, `Router.stato()`);
- ultima migrazione applicata (se verificabile).

**Mai un verde senza un controllo reale e recente** (mostra quando è stato fatto).

---

## 26. IMPOSTAZIONI

In un pannello: aspetto, voce, livelli di notifica, orario di silenzio, preferenze della vista centrale, provider
(solo stato e istruzioni, **mai mostrare chiavi**), dispositivi (registra, revoca), profilo.
Le impostazioni personali si salvano per utente (localStorage per le preferenze di interfaccia; DB solo se vanno condivise
e con migrazione). Le azioni da admin (gestione utenti) sono visibili solo agli admin, e la RLS le blocca comunque.

---

## 27. PERFORMANCE (budget misurabili)

- Primo caricamento utile < 2,5 s su una rete 4G (B: bundle JS iniziale < 250 KB gzip, pannelli e grafici lazy).
- Interazioni < 100 ms di risposta visiva.
- CPU a riposo con lo sfondo animato < 2%.
- Liste lunghe (log, eventi) virtualizzate o paginate.
- Nessuna richiesta ripetuta inutile: cache, debounce dei filtri, una query per vista.

---

## 28. TEST E VERIFICA (obbligatori)

1. Test esistenti verdi: `python -m pytest -q tests`, `bash tests/pg/run.sh`.
2. Test nuovi:
   - rendering della vista centrale;
   - apertura e chiusura di **ogni** pannello senza perdere il centro;
   - **ogni riga della tabella dei controlli** (§18);
   - router di intenti con dati di test;
   - stati di caricamento, vuoto ed errore;
   - realtime (B) o polling (A).
3. Playwright (Chromium) a 390, 768, 1280 e 1920 px: screenshot, nessuno scroll orizzontale, nessun errore in console,
   focus visibile, contrasto. **Guarda gli screenshot**: compilare non significa che sia bello.
4. Test di accessibilità automatici (es. axe) sulle viste principali.
5. Test con i dati di esempio **solo in locale** (`GUARDIAN_DB` su SQLite o un seed dedicato). **Mai dati finti nel Supabase condiviso.**

---

## 29. FASI DI LAVORO (ognuna chiusa da test, checkpoint, registro, commit e push)

1. **Audit**: §2 e §4, valutazione, catalogo delle metriche (§12.1), tabella dei controlli (§18).
2. **Decisione architetturale** (§3), da far approvare. Aggiornare `GUARDIAN_DECISIONS.md`.
3. **Design system**: token, componenti base, pagina del design system, palette validata.
4. **Command Center**: nucleo di Guardian (§7), barra di salute (§25), agenti (§9), task attivi (§11),
   approvazioni in attesa (§14), prossime azioni (§24).
5. **Pannelli**: agente, azienda, task, approvazione, notifiche, memoria/handoff, impostazioni.
6. **Dati reali e tempo reale**: nessun mock nei percorsi di produzione, stati di caricamento, vuoto ed errore.
7. **Conversazione, router di intenti, palette comandi, voce** (dove supportata).
8. **Statistiche e grafici** secondo la §12.4.
9. **Test e rifinitura**: E2E, accessibilità, performance, responsive, polish visivo.
10. **Deploy** (B: hosting statico + guida in `docs/`; A: Streamlit Cloud) e passaggio di consegne.

Per ogni fase stima la complessità (S/M/L) e indica cosa serve dal titolare (credenziali, approvazioni, account di hosting).

---

## 30. CONTINUITÀ (se il tuo utilizzo si avvicina al limite)

1. Ferma le modifiche non essenziali. Non lasciare file a metà.
2. Aggiorna `GUARDIAN_STATUS.md`, `GUARDIAN_TASKS.md`, `GUARDIAN_HANDOFF.md` e `GUARDIAN_DECISIONS.md`:
   cosa è fatto, file toccati, test eseguiti, problemi, **prossimo comando preciso**.
3. Se il bridge è configurato, salva anche un handoff:
   `python bridge/guardian_bridge.py checkpoint --summary … --next … --tests-pending …`.
4. Riga di registro, commit e push sul tuo branch.

---

## 31. REGOLE ASSOLUTE

1. Guardian resta l'intelligenza centrale e la vista centrale resta attiva.
2. I pannelli non sostituiscono la vista centrale senza motivo.
3. Ogni pulsante visibile ha un'azione reale; quelli non realizzabili sono disabilitati con il motivo.
4. Ogni numero viene da dati reali, con la fonte indicata nel catalogo.
5. Agenti, aziende e task sono caricati dinamicamente: nessun numero fisso.
6. Nessuna attività, messaggio di stato o comunicazione tra agenti inventati.
7. Non si dichiara realtime, voce o "Live" se non sono attivi davvero in quel momento.
8. Nessun segreto nel client, nel repo o nei log.
9. Nessuna azione esterna senza approvazione umana registrata.
10. Non si distrugge funzionalità esistente e non si crea una seconda architettura Guardian parallela non concordata.
11. Niente animazioni eccessive: l'estetica non vince mai sulla leggibilità.
12. Non si dichiara finito senza test, screenshot guardati e checkpoint aggiornati.

---

## 32. CRITERI FINALI DI ACCETTAZIONE

- **Visivi**: premium, futuristico, originale, coerente; Guardian al centro; zero confusione; contrasto AA;
  screenshot a 4 larghezze approvati dal titolare.
- **Funzionali**: tutte le righe della tabella dei controlli passano i test; tutti i pannelli si aprono e chiudono
  senza perdere il centro; nessuna funzione delle 12 sezioni attuali è andata persa.
- **Tecnici**:
  - dati reali;
  - realtime (B) o polling dichiarato (A);
  - stati di caricamento, vuoto ed errore;
  - design system riutilizzabile;
  - test verdi (vecchi + nuovi) e migrazioni provate su Postgres;
  - budget di performance rispettati.
- **Esperienza**: aprendo Guardian il titolare pensa *"questo è il mio centro di comando AI"*, e lo usa davvero ogni giorno.

---

## 33. ISTRUZIONE FINALE

Parti in **Plan mode**. Analizza il repository, leggi le regole e le skill, verifica la fotografia della §2 e presenta:
la valutazione, la decisione architetturale con la raccomandazione, il catalogo delle metriche, la tabella dei controlli
e il piano a fasi. **Aspetta l'approvazione esplicita del titolare.**

Poi esegui le fasi nell'ordine, ognuna verificata e salvata, senza fermarti a un mockup statico: continua finché la
dashboard è collegata ai dati reali e le interazioni importanti funzionano.
Se una capacità non si può realizzare in sicurezza, documentala e mostrala disabilitata con il motivo.
Non fingere mai che funzioni.

*Il centro resta presente. L'utente resta al comando. Ogni interazione ha uno scopo. Ogni funzione visibile funziona.*
