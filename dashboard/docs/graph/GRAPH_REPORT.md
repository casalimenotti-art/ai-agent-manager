# Graph Report - dashboard  (2026-11-26)

## Corpus Check
- 59 files · ~37,263 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 3, .bat 2, .example 1)

## Summary
- 635 nodes · 1144 edges · 39 communities (26 shown, 13 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `123fffee`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- FonteLocale
- app.py
- config.py
- FonteDemo
- agenti.py
- monitor.py
- re
- clienti.py
- FonteRemota
- test_agenti.py
- Fonte
- Communities (21 total, 12 thin omitted)
- 04 — Agenti, manager Guardian e controllo
- PROMPT_CLAUDE_CODE.md
- PROMPT_NOTTE.md
- Video.tsx
- 03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)
- 05 — Clienti, pipeline e visite di persona
- Prompt per Claude Code — Obiettivo: 10.000 € al mese (due soci, Cagliari)
- Prompt per Claude Code (Opus 5.5) — finire Guardian: tempo reale, agenti, manager, clienti
- 01 — Visione, regole e protocollo di risparmio token
- 06 — Criteri di accettazione, test, consegna e avvio di Streamlit
- 07 — Esempi online e riferimenti (con provenienza)
- Come far usare il PC e il browser a Claude (in sicurezza)
- cacciatore-clienti.md
- guardian-manager.md
- scopritore-problemi.md
- analista-presenza-online.md
- analista-risultati.md
- architetto-squadra.md
- collaudatore-agenti.md
- curatore-skill.md
- forgiatore-agenti.md
- ottimizzatore-prompt.md
- redattore-outreach.md
- verificatore-fonti.md
- azienda.template.md
- compilatore-schede-visita.md
- video-demo/README.md

## God Nodes (most connected - your core abstractions)
1. `Fonte` - 38 edges
2. `FonteRemota` - 37 edges
3. `FonteLocale` - 35 edges
4. `FonteDemo` - 27 edges
5. `esc()` - 16 edges
6. `indice()` - 15 edges
7. `scrivi()` - 14 edges
8. `Indice` - 13 edges
9. `installa_catalogo_locale()` - 13 edges
10. `asst()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Da dove si ricava chi ha avviato chi` --references--> `_Stato`  [INFERRED]
  docs/spec/04-agenti-e-manager.md → agenti.py
- `5. Parlare con Guardian` --references--> `esegui_locale()`  [INFERRED]
  docs/spec/04-agenti-e-manager.md → chat.py
- `Principi` --references--> `Fonte`  [INFERRED]
  docs/spec/01-visione-e-regole.md → fonte.py
- `6. Tecnologia: decidi con una misura, non a sensazione` --references--> `Fonte`  [INFERRED]
  docs/spec/03-ui-visual.md → fonte.py
- `3. Definizioni esatte delle metriche` --references--> `costo()`  [INFERRED]
  docs/spec/02-dati-realtime.md → agenti.py

## Import Cycles
- None detected.

## Communities (39 total, 13 thin omitted)

### Community 0 - "FonteLocale"
Cohesion: 0.05
Nodes (37): FonteLocale, catalogo_locale(), elenca_skill(), _git(), installa_catalogo_locale(), installa_graphify_locale(), installa_locale(), installa_squadra_locale() (+29 more)

### Community 1 - "app.py"
Cohesion: 0.06
Nodes (38): esegui_e_mostra(), fa(), get_fonte(), pannello_scoperte(), scegli_cartella(), sez_agenti(), sez_clienti(), sez_consumi() (+30 more)

### Community 2 - "config.py"
Cohesion: 0.06
Nodes (21): agente_installato(), costruisci_comando(), esegui_locale(), Risposta, _righe_csv(), _run(), test_cartella_inesistente(), test_comando_mancante() (+13 more)

### Community 3 - "FonteDemo"
Cohesion: 0.06
Nodes (11): FonteDemo, leggi_scoperte(), _scoperte_vuote(), test_crea_fonte_demo(), test_demo_dati_finti_e_azioni_disattivate(), test_demo_e_locale_espongono_scoperte(), test_remota_richiede_token(), test_remota_rifiuta_http_non_locale() (+3 more)

### Community 4 - "agenti.py"
Cohesion: 0.07
Nodes (18): costo(), evento_da_strumento(), Indice, maschera(), parse_ts(), prezzo_modello(), _Stato, _testo() (+10 more)

### Community 5 - "monitor.py"
Cohesion: 0.09
Nodes (14): Campionatore, e_processo_claude(), _file_ricavi(), leggi_ricavi(), scrivi_ricavo(), test_cpu_storico_potato(), test_ignora_altri(), test_ignora_bash_che_cita_il_percorso_negli_argomenti_lontani() (+6 more)

### Community 6 - "re"
Cohesion: 0.11
Nodes (21): sez_siti(), 0. Leggi (e basta), 1. Regole non negoziabili, 2. Come lavora la squadra (sciame controllato), 3. Siti demo (uno per cliente), 4. In parallelo: continua la dashboard (la vedi crescere mentre lavori), 5. Notifiche e controllo, 6. Risparmio crediti (obbligatorio) (+13 more)

### Community 7 - "clienti.py"
Cohesion: 0.13
Nodes (19): clienti(), _file_stati(), foto(), imposta_visita(), leggi_leads(), leggi_stati(), salva_foto(), scheda_visita() (+11 more)

### Community 8 - "FonteRemota"
Cohesion: 0.12
Nodes (3): FonteRemota, 🛡️ Guardian — centrale di controllo per Claude Code, test_remota_errore_rete_non_solleva_in_esegui()

### Community 9 - "test_agenti.py"
Cohesion: 0.26
Nodes (22): asst(), indice(), iso(), scrivi(), test_attivita_delega_web_e_risultati_mascherati(), test_attivita_filtri_e_limite(), test_burn_rate_ultime_5_ore(), test_costi_ignora_giorni_fuori_finestra() (+14 more)

### Community 11 - "Communities (21 total, 12 thin omitted)"
Cohesion: 0.11
Nodes (17): Communities (21 total, 12 thin omitted), Community 0 - "skill.py", Community 10 - "scopritore-problemi.md", Community 1 - "app.py", Community 2 - "theme.py", Community 3 - "fonte.py", Community 4 - "clienti.py", Community 6 - "Fonte" (+9 more)

### Community 12 - "04 — Agenti, manager Guardian e controllo"
Cohesion: 0.13
Nodes (14): 04 — Agenti, manager Guardian e controllo, 1. Modello dati di un agente, 2. Il manager: Guardian, 3. Coda di approvazioni, 4. Cancello di sicurezza e interruttore (opzionale ma consigliato), 5. Parlare con Guardian, 6. Squadra (ruoli, già nel repo in `squadra/`), 7. Metriche per agente (per migliorare nel tempo) (+6 more)

### Community 13 - "PROMPT_CLAUDE_CODE.md"
Cohesion: 0.14
Nodes (13): BACKLOG DASHBOARD (una milestone alla volta, con test e commit; `sviluppatore-dashboard` + `revisore-qualita`), CICLO AUTOMATICO (avvialo dopo M1), DEFINIZIONE DI "FATTO" PER OGNI COMPITO, EVERYTHING CLAUDE CODE (ECC) — installazione SICURA, solo un sottoinsieme, FASE 0 — Preparazione (una volta sola, poi riporta in 5 righe), FORMATO DEI TUOI REPORT (sempre, max 8 righe), LA SQUADRA (tu sei il manager), PIANO SRL (3 mesi, 12 settimane) — BOZZA DA VERIFICARE (+5 more)

### Community 14 - "PROMPT_NOTTE.md"
Cohesion: 0.17
Nodes (11): EVERYTHING CLAUDE CODE (ECC), FASE A — Ricerca interfacce e design (prima di scrivere codice grafico), FASE B — Dashboard più dinamica e fluida (stile Cyberpunk 2077 evocato), FASE C — La fabbrica di agenti (almeno 5 nuovi agenti, creati da altri agenti), FASE D — Ricerca clienti a Cagliari (sul PC, con web libero), MISSIONE, NOTIFICHE, Prompt per Claude Code (Opus 5.5) — lavoro autonomo notturno su Guardian, squadra di agenti e ricerca clienti (+3 more)

### Community 15 - "Video.tsx"
Cohesion: 0.30
Nodes (7): Root(), Carosello(), Carta(), COLORI, Cta(), Titolo(), Video()

### Community 16 - "03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)"
Cohesion: 0.18
Nodes (10): 03 — Interfaccia e design (Cyberpunk evocato, fluido, utile), 1. Linguaggio visivo, 2. Struttura (wireframe), 3. Il pannello Consumi (il cuore), 4. Pannello Agenti, 5. Pannello Clienti e Costi, 5b. Pannello Guardian (chat col manager), 5c. Prestazioni, accessibilità, mobile (+2 more)

### Community 17 - "05 — Clienti, pipeline e visite di persona"
Cohesion: 0.18
Nodes (10): 05 — Clienti, pipeline e visite di persona, Agenti coinvolti (catena), Archiviazione, Campi di un lead, Cosa cercare (problemi risolvibili da noi), Limiti e onestà, Obiettivo, Pannello Clienti (+2 more)

### Community 18 - "Prompt per Claude Code — Obiettivo: 10.000 € al mese (due soci, Cagliari)"
Cohesion: 0.18
Nodes (10): 0. Leggi (e basta, nell'ordine), 1. Regole non negoziabili, 2. Il modello di business (da validare, non da credere), 3. Trovare i clienti (la macchina commerciale), 4. Il lavoro dei soci sul campo, 5. Prodotti da realizzare (in quest'ordine, uno alla volta), 6. Vendita e contratti (senza consulenza legale), 7. Ritmo di lavoro e controllo (+2 more)

### Community 19 - "Prompt per Claude Code (Opus 5.5) — finire Guardian: tempo reale, agenti, manager, clienti"
Cohesion: 0.22
Nodes (8): 1. Leggi in questo ordine (e basta), 2. Missione (cosa deve fare Guardian), 3. Regole che non si negoziano, 4. Risparmio crediti (obbligatorio, dettaglio in `01`), 5. Milestone (dettaglio e criteri AC-1…24 in `06`), 6. Ultimo passo: aprire Streamlit, 7. Cosa mi consegni, Prompt per Claude Code (Opus 5.5) — finire Guardian: tempo reale, agenti, manager, clienti

### Community 20 - "01 — Visione, regole e protocollo di risparmio token"
Cohesion: 0.25
Nodes (7): 01 — Visione, regole e protocollo di risparmio token, Cosa stiamo costruendo, Definizione di "fatto", Non-obiettivi (non farli), Principi, Protocollo di risparmio token (obbligatorio), Registro delle decisioni

### Community 21 - "06 — Criteri di accettazione, test, consegna e avvio di Streamlit"
Cohesion: 0.25
Nodes (7): 06 — Criteri di accettazione, test, consegna e avvio di Streamlit, Chiusura: aprire Streamlit e farla vedere al titolare, Criteri di accettazione (misurabili), Esecuzione per milestone (ordine consigliato), Formato del report (max 8 righe), Piano dei test, Ripristino se qualcosa va storto

### Community 22 - "07 — Esempi online e riferimenti (con provenienza)"
Cohesion: 0.33
Nodes (5): 07 — Esempi online e riferimenti (con provenienza), 1. Già trovato (ricerca precedente), 2. Da cercare (almeno altri 12, con URL letto davvero), 3. Come usare la ricerca senza sprecare token, 4. Prezzi e consumo (riferimento verificato)

### Community 23 - "Come far usare il PC e il browser a Claude (in sicurezza)"
Cohesion: 0.33
Nodes (5): Come far usare il PC e il browser a Claude (in sicurezza), Cosa c'è e cosa fa, Impostazione consigliata (per lavorare di notte senza rischi inutili), Passi, in ordine, "Senza chiedermi nulla": cosa si può e cosa no

### Community 24 - "cacciatore-clienti.md"
Cohesion: 0.50
Nodes (3): Come lavori, Consegna, Prima di iniziare

### Community 25 - "guardian-manager.md"
Cohesion: 0.50
Nodes (3): Ciclo, Prima di ogni mossa, Regole

### Community 26 - "scopritore-problemi.md"
Cohesion: 0.50
Nodes (3): Consegna, Cosa cerchi, Regole

## Knowledge Gaps
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Fonte` connect `Fonte` to `FonteLocale`, `app.py`, `FonteDemo`, `agenti.py`, `FonteRemota`, `Communities (21 total, 12 thin omitted)`, `PROMPT_CLAUDE_CODE.md`, `PROMPT_NOTTE.md`, `03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)`, `01 — Visione, regole e protocollo di risparmio token`?**
  _High betweenness centrality (0.158) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Fonte` (e.g. with `God Nodes (most connected - your core abstractions)` and `Suggested Questions`) actually correct?**
  _`Fonte` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `FonteLocale` be split into smaller, more focused modules?**
  _Cohesion score 0.0528169014084507 - nodes in this community are weakly interconnected._
- **Why does `God Nodes (most connected - your core abstractions)` connect `agenti.py` to `FonteLocale`, `app.py`, `config.py`, `FonteRemota`, `Fonte`, `Communities (21 total, 12 thin omitted)`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `FonteRemota` (e.g. with `God Nodes (most connected - your core abstractions)` and `Suggested Questions`) actually correct?**
  _`FonteRemota` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0633879781420765 - nodes in this community are weakly interconnected._
- **Why does `FonteLocale` connect `FonteLocale` to `app.py`, `config.py`, `FonteDemo`, `agenti.py`, `monitor.py`, `clienti.py`, `FonteRemota`, `Fonte`, `Communities (21 total, 12 thin omitted)`, `01 — Visione, regole e protocollo di risparmio token`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._