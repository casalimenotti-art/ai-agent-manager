# Graph Report - dashboard  (2026-11-26)

## Corpus Check
- 68 files · ~49,034 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 3, .bat 2, .example 1)

## Summary
- 831 nodes · 1554 edges · 59 communities (33 shown, 26 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 79 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `123fffee`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_skill.py
- app.py
- voce.py
- FonteDemo
- agenti.py
- monitor.py
- re
- clienti.py
- FonteRemota
- test_agenti.py
- Fonte
- Communities (39 total, 13 thin omitted)
- theme.py
- PROMPT_CLAUDE_CODE.md
- PROMPT_NOTTE.md
- Video.tsx
- 04 — Agenti, manager Guardian e controllo
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
- chat.py
- FonteLocale
- esegui_e_mostra
- test_fonte.py
- crea_fonte
- pannello_scoperte
- dialog_lancia_agente
- 03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)
- plancia.py
- vista_statistiche
- grafico_costi
- leggi_usage
- tabella_clienti

## God Nodes (most connected - your core abstractions)
1. `Fonte` - 41 edges
2. `FonteLocale` - 37 edges
3. `FonteRemota` - 37 edges
4. `FonteDemo` - 30 edges
5. `Communities (39 total, 13 thin omitted)` - 27 edges
6. `esc()` - 22 edges
7. `indice()` - 16 edges
8. `scrivi()` - 15 edges
9. `asst()` - 14 edges
10. `Indice` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Da dove si ricava chi ha avviato chi` --references--> `_Stato`  [INFERRED]
  docs/spec/04-agenti-e-manager.md → agenti.py
- `Principi` --references--> `Fonte`  [INFERRED]
  docs/spec/01-visione-e-regole.md → fonte.py
- `6. Tecnologia: decidi con una misura, non a sensazione` --references--> `Fonte`  [INFERRED]
  docs/spec/03-ui-visual.md → fonte.py
- `3. Definizioni esatte delle metriche` --references--> `costo()`  [INFERRED]
  docs/spec/02-dati-realtime.md → agenti.py
- `1. Fonti dei dati` --references--> `_Stato`  [INFERRED]
  docs/spec/02-dati-realtime.md → agenti.py

## Import Cycles
- None detected.

## Communities (59 total, 26 thin omitted)

### Community 0 - "test_skill.py"
Cohesion: 0.07
Nodes (35): catalogo_locale(), elenca_skill(), _git(), installa_catalogo_locale(), installa_graphify_locale(), installa_locale(), installa_squadra_locale(), leggi_azienda() (+27 more)

### Community 1 - "app.py"
Cohesion: 0.15
Nodes (17): _chiudi_dettaglio(), dati_attivita(), dati_sessioni(), dati_skill(), dettaglio_agente(), fa(), griglia_agenti(), microfono() (+9 more)

### Community 2 - "voce.py"
Cohesion: 0.07
Nodes (29): test_installa_pinnato_solo_wheel(), test_motore_sherpa_finto(), test_senza_pacchetto_messaggio_chiaro(), test_trascrizione_con_motore_finto_e_normalizzazione(), test_validazione_audio(), test_wav_a_mono16k(), wav(), wav_formato() (+21 more)

### Community 4 - "agenti.py"
Cohesion: 0.06
Nodes (20): costo(), evento_da_strumento(), Indice, maschera(), parse_ts(), prezzo_modello(), _Stato, _testo() (+12 more)

### Community 5 - "monitor.py"
Cohesion: 0.07
Nodes (14): _scoperte_vuote(), e_processo_claude(), _file_ricavi(), leggi_ricavi(), riepilogo_token(), scrivi_ricavo(), test_ignora_altri(), test_ignora_bash_che_cita_il_percorso_negli_argomenti_lontani() (+6 more)

### Community 6 - "re"
Cohesion: 0.12
Nodes (20): 0. Leggi (e basta), 1. Regole non negoziabili, 2. Come lavora la squadra (sciame controllato), 3. Siti demo (uno per cliente), 4. In parallelo: continua la dashboard (la vedi crescere mentre lavori), 5. Notifiche e controllo, 6. Risparmio crediti (obbligatorio), 7. Cosa mi consegni (+12 more)

### Community 7 - "clienti.py"
Cohesion: 0.10
Nodes (20): clienti(), _file_stati(), foto(), imposta_visita(), leggi_leads(), leggi_stati(), _righe_csv(), salva_foto() (+12 more)

### Community 9 - "test_agenti.py"
Cohesion: 0.14
Nodes (27): God Nodes (most connected - your core abstractions), elabora(), _finestra(), main(), scrivi_atomico(), asst(), indice(), iso() (+19 more)

### Community 11 - "Communities (39 total, 13 thin omitted)"
Cohesion: 0.06
Nodes (35): Communities (39 total, 13 thin omitted), Community 0 - "FonteLocale", Community 11 - "Communities (21 total, 12 thin omitted)", Community 12 - "04 — Agenti, manager Guardian e controllo", Community 13 - "PROMPT_CLAUDE_CODE.md", Community 14 - "PROMPT_NOTTE.md", Community 15 - "Video.tsx", Community 16 - "03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)" (+27 more)

### Community 12 - "theme.py"
Cohesion: 0.11
Nodes (19): test_giro8_fermi_vecchi_browser_e_nomi(), barra_utilizzo(), barre_orizzontali(), card_scoperta(), card_skill(), card_store(), _desc_3righe(), dettaglio_agente() (+11 more)

### Community 13 - "PROMPT_CLAUDE_CODE.md"
Cohesion: 0.14
Nodes (13): BACKLOG DASHBOARD (una milestone alla volta, con test e commit; `sviluppatore-dashboard` + `revisore-qualita`), CICLO AUTOMATICO (avvialo dopo M1), DEFINIZIONE DI "FATTO" PER OGNI COMPITO, EVERYTHING CLAUDE CODE (ECC) — installazione SICURA, solo un sottoinsieme, FASE 0 — Preparazione (una volta sola, poi riporta in 5 righe), FORMATO DEI TUOI REPORT (sempre, max 8 righe), LA SQUADRA (tu sei il manager), PIANO SRL (3 mesi, 12 settimane) — BOZZA DA VERIFICARE (+5 more)

### Community 14 - "PROMPT_NOTTE.md"
Cohesion: 0.17
Nodes (11): EVERYTHING CLAUDE CODE (ECC), FASE A — Ricerca interfacce e design (prima di scrivere codice grafico), FASE B — Dashboard più dinamica e fluida (stile Cyberpunk 2077 evocato), FASE C — La fabbrica di agenti (almeno 5 nuovi agenti, creati da altri agenti), FASE D — Ricerca clienti a Cagliari (sul PC, con web libero), MISSIONE, NOTIFICHE, Prompt per Claude Code (Opus 5.5) — lavoro autonomo notturno su Guardian, squadra di agenti e ricerca clienti (+3 more)

### Community 15 - "Video.tsx"
Cohesion: 0.30
Nodes (7): Root(), Carosello(), Carta(), COLORI, Cta(), Titolo(), Video()

### Community 16 - "04 — Agenti, manager Guardian e controllo"
Cohesion: 0.14
Nodes (13): 04 — Agenti, manager Guardian e controllo, 1. Modello dati di un agente, 2. Il manager: Guardian, 3. Coda di approvazioni, 4. Cancello di sicurezza e interruttore (opzionale ma consigliato), 6. Squadra (ruoli, già nel repo in `squadra/`), 7. Metriche per agente (per migliorare nel tempo), 8. Test (+5 more)

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

### Community 39 - "chat.py"
Cohesion: 0.08
Nodes (21): agente_installato(), agenti_installati(), anteprima_lancio(), costruisci_comando(), esegui_locale(), lancia_in_background(), _corpo(), prepara_lancio() (+13 more)

### Community 40 - "FonteLocale"
Cohesion: 0.11
Nodes (3): FonteLocale, 🛡️ Guardian — centrale di controllo per Claude Code, test_locale_implementa_interfaccia()

### Community 42 - "test_fonte.py"
Cohesion: 0.22
Nodes (8): leggi_scoperte(), test_demo_e_locale_espongono_scoperte(), test_remota_errore_rete_non_solleva_in_esegui(), test_remota_richiede_token(), test_remota_rifiuta_http_non_locale(), test_scoperte_file_corrotto(), test_scoperte_file_mancante(), test_scoperte_file_valido()

### Community 43 - "crea_fonte"
Cohesion: 0.50
Nodes (3): get_fonte(), crea_fonte(), test_crea_fonte_demo()

### Community 45 - "dialog_lancia_agente"
Cohesion: 0.33
Nodes (3): dialog_lancia_agente(), sez_squadra(), nome_ruolo()

### Community 50 - "03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)"
Cohesion: 0.18
Nodes (10): 03 — Interfaccia e design (Cyberpunk evocato, fluido, utile), 1. Linguaggio visivo, 2. Struttura (wireframe), 3. Il pannello Consumi (il cuore), 4. Pannello Agenti, 5. Pannello Clienti e Costi, 5b. Pannello Guardian (chat col manager), 5c. Prestazioni, accessibilità, mobile (+2 more)

### Community 51 - "plancia.py"
Cohesion: 0.05
Nodes (40): _azione_browser(), _blocco_dati(), categoria_skill(), _chiave(), conta_categorie(), costruisci_suggerimento(), data_italiana(), descrivi_usage() (+32 more)

### Community 52 - "vista_statistiche"
Cohesion: 0.23
Nodes (10): dati_costi(), dialog_scheda_visita(), sez_clienti(), sez_consumi(), sez_costi(), sez_siti(), utilizzo_reale(), vista_costi() (+2 more)

### Community 53 - "grafico_costi"
Cohesion: 0.33
Nodes (3): grafico_costi(), grafico_cpu(), heatmap_giorni()

## Knowledge Gaps
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Fonte` connect `Fonte` to `agenti.py`, `monitor.py`, `FonteLocale`, `test_agenti.py`, `FonteRemota`, `Communities (39 total, 13 thin omitted)`, `crea_fonte`, `PROMPT_CLAUDE_CODE.md`, `PROMPT_NOTTE.md`, `03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)`, `01 — Visione, regole e protocollo di risparmio token`, `.usage`, `.documenti_radice`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Fonte` (e.g. with `God Nodes (most connected - your core abstractions)` and `Suggested Questions`) actually correct?**
  _`Fonte` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_skill.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
- **Why does `God Nodes (most connected - your core abstractions)` connect `test_agenti.py` to `test_skill.py`, `FonteDemo`, `agenti.py`, `FonteLocale`, `FonteRemota`, `Fonte`, `Communities (39 total, 13 thin omitted)`, `theme.py`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `FonteLocale` (e.g. with `God Nodes (most connected - your core abstractions)` and `Suggested Questions`) actually correct?**
  _`FonteLocale` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `voce.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06778476589797344 - nodes in this community are weakly interconnected._
- **Why does `Graph Report - dashboard  (2026-11-26)` connect `Communities (39 total, 13 thin omitted)` to `test_agenti.py`, `agenti.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._