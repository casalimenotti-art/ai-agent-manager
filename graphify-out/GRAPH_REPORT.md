# Graph Report - ai-agent-manager  (2026-11-26)

## Corpus Check
- 134 files · ~100,487 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: .csv 13, .bat 5, (none) 3)

## Summary
- 1317 nodes · 2251 edges · 109 communities (72 shown, 37 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 96 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `123fffee`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- cache_data
- voce.py
- accesso.py
- re
- time
- agenti.py
- app.py
- clienti.py
- Communities (39 total, 13 thin omitted)
- FonteRemota
- Miglioramenti suggeriti (self-improvement, 26/11/2026)
- Fonte
- FonteDemo
- costruisci_suggerimento
- Guardian dal telefono — guida passo passo
- Streamlit 1.67: app fluida e reattiva - 12 tecniche
- dashboard/app.py
- chiave_widget
- PROMPT_CLAUDE_CODE.md
- catalogo.py
- PROMPT_NOTTE.md
- Video.tsx
- 03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)
- 05 — Clienti, pipeline e visite di persona
- Prompt per Claude Code — Obiettivo: 10.000 € al mese (due soci, Cagliari)
- test_robustezza.py
- 2. Lavori automatici
- Antica Trattoria Dar Mammozzaro (ristorante, Quartu Sant'Elena)
- Bellini B&B (B&B, Cagliari - San Benedetto)
- Bernardi Foto Ottica (ottico, Cagliari)
- Black and White Parrucchieri (parrucchiere, Selargius)
- ChiaroVista di Mario Orru' (ottica, Assemini)
- Comfort & Beauty (Estetica Maxia) (centro estetico, Cagliari)
- Fenicottero B&B (B&B, Elmas)
- Il Borgo (B&B Villanova) (B&B, Cagliari - Villanova)
- Il Cagliarese B&B (B&B, Cagliari - Marina)
- Le Tre Nasse B&B (B&B, Quartu Sant'Elena)
- Libarium Nostrum (bar-ristorante, Cagliari - Castello)
- Ottica Borriello (ottica, Quartu S.E., Assemini, Monserrato, Cagliari)
- Ottica Ungari (ottica, Selargius - Su Planu)
- Pani e Casu (ristorante, Cagliari - Castello)
- Ristorante 51 (ristorante, Cagliari - Via Pola)
- theme.py
- Prompt per Claude Code (Opus 5.5) — finire Guardian: tempo reale, agenti, manager, clienti
- Stili HUD scuri ma accessibili - ricerca
- Giro di visita consigliato (30 lead confermati; n 20 = Gisella B&B, sostituto di Sun & Sardinia smentito)
- 06 — Criteri di accettazione, test, consegna e avvio di Streamlit
- Automazioni dalla dashboard Guardian (ricerca 2026-11-26)
- AI Agent Manager — Streamlit Starter
- CONTINUA — come riprendere il lavoro (qualsiasi modello)
- config.py
- STATO — Operazione 30 clienti (2026-11-26)
- 07 — Esempi online e riferimenti (con provenienza)
- Audit interfaccia dashboard (giro 11)
- Come far usare il PC e il browser a Claude (in sicurezza)
- Ricerca UI "Jarvis" / HUD per assistenti AI (rapporto del 2026-11-26)
- Ricerca WhatsApp e Instagram con Claude Code (26/11/2026)
- plancia.py
- Idee di design (ricerca, nov 2026)
- Ricerca skill per gli agenti (2026-11-26)
- Riconoscimento vocale italiano offline (Windows 11, Python 3.15.2) — 2026-11-26
- riassumi_risultato
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
- 🛡️ Guardian — centrale di controllo per Claude Code
- 04 — Agenti, manager Guardian e controllo
- azienda.template.md
- compilatore-schede-visita.md
- video-demo/README.md
- 4-canti-bistrot.md
- anania-guesthouse.md
- antica-cagliari-ristorante.md
- b-b-casa-spano.md
- beauty-center-valentino.md
- clelsy-centro-estetico.md
- clinical-beauty-farm-srl.md
- coccole-centro-estetico.md
- el-carnicero-assemini.md
- fattoria-giaccu.md
- gisella-b-b.md
- ristorante-arke.md
- ristorante-terra-e-mari.md
- sa-mola-sarda.md
- stanze-centro-storico.md
- domanda_agente
- FonteLocale
- test_fonte.py
- testo_evento
- dividi_agenti
- titolo_scoperta
- streamlit
- theme.py
- fonte.py

## God Nodes (most connected - your core abstractions)
1. `Fonte` - 41 edges
2. `FonteLocale` - 37 edges
3. `FonteRemota` - 37 edges
4. `FonteDemo` - 30 edges
5. `Communities (39 total, 13 thin omitted)` - 27 edges
6. `esc()` - 24 edges
7. `sez_guardian()` - 17 edges
8. `indice()` - 16 edges
9. `griglia_agenti()` - 15 edges
10. `scrivi()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Da dove si ricava chi ha avviato chi` --references--> `_Stato`  [INFERRED]
  dashboard/docs/spec/04-agenti-e-manager.md → dashboard/agenti.py
- `5. Parlare con Guardian` --references--> `esegui_locale()`  [INFERRED]
  dashboard/docs/spec/04-agenti-e-manager.md → dashboard/chat.py
- `Principi` --references--> `Fonte`  [INFERRED]
  dashboard/docs/spec/01-visione-e-regole.md → dashboard/fonte.py
- `6. Tecnologia: decidi con una misura, non a sensazione` --references--> `Fonte`  [INFERRED]
  dashboard/docs/spec/03-ui-visual.md → dashboard/fonte.py
- `BACKLOG DASHBOARD (una milestone alla volta, con test e commit; `sviluppatore-dashboard` + `revisore-qualita`)` --references--> `Fonte`  [INFERRED]
  dashboard/PROMPT_CLAUDE_CODE.md → dashboard/fonte.py

## Import Cycles
- None detected.

## Communities (109 total, 37 thin omitted)

### Community 0 - "cache_data"
Cohesion: 0.16
Nodes (12): _corpo_voce(), dati_percorso_skill(), dati_scheda_agente(), dati_scoperte(), dati_skill(), mappa_skill_it(), pannello_scoperte(), sez_skill() (+4 more)

### Community 1 - "voce.py"
Cohesion: 0.06
Nodes (35): w(), test_agente_manager_nel_comando(), test_installa_pinnato_solo_wheel(), test_motore_sherpa_finto(), test_normalizzazione_e_comandi(), test_senza_pacchetto_messaggio_chiaro(), test_trascrizione_con_motore_finto_e_normalizzazione(), test_validazione_audio() (+27 more)

### Community 2 - "accesso.py"
Cohesion: 0.11
Nodes (16): attesa_dopo(), crea_hash(), host_locale(), passa_da_proxy(), richiedi_pin(), verifica_pin(), main(), _pagina_remota() (+8 more)

### Community 3 - "re"
Cohesion: 0.05
Nodes (40): esegui_e_mostra(), agente_installato(), agenti_installati(), anteprima_lancio(), costruisci_comando(), esegui_locale(), _corpo(), prepara_lancio() (+32 more)

### Community 4 - "time"
Cohesion: 0.07
Nodes (49): lancia_in_background(), God Nodes (most connected - your core abstractions), elabora(), _finestra(), main(), scrivi_atomico(), aggiungi(), carica_giorno() (+41 more)

### Community 5 - "agenti.py"
Cohesion: 0.06
Nodes (24): costo(), evento_da_strumento(), Indice, maschera(), parse_ts(), prezzo_modello(), _Stato, _testo() (+16 more)

### Community 6 - "app.py"
Cohesion: 0.15
Nodes (12): fallback_plan(), get_client(), get_secret(), make_plan(), parse_json(), riepilogo_oggi(), test_cambio_giorno_a_mezzanotte(), test_conteggi_e_ultimo() (+4 more)

### Community 7 - "clienti.py"
Cohesion: 0.09
Nodes (21): clienti(), _file_stati(), foto(), imposta_visita(), leggi_leads(), leggi_stati(), _righe_csv(), salva_foto() (+13 more)

### Community 8 - "Communities (39 total, 13 thin omitted)"
Cohesion: 0.06
Nodes (35): Communities (39 total, 13 thin omitted), Community 0 - "FonteLocale", Community 11 - "Communities (21 total, 12 thin omitted)", Community 12 - "04 — Agenti, manager Guardian e controllo", Community 13 - "PROMPT_CLAUDE_CODE.md", Community 14 - "PROMPT_NOTTE.md", Community 15 - "Video.tsx", Community 16 - "03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)" (+27 more)

### Community 10 - "Miglioramenti suggeriti (self-improvement, 26/11/2026)"
Cohesion: 0.20
Nodes (9): 1. Gli agenti dicono "fatto" senza averlo visto, 2. Lezioni Streamlit 1.67 da non riscoprire, 3. Report degli agenti e brief, 4. Stato del progetto che invecchia, 5. Soglie di utilizzo, Frasi del titolare (contesto), Già a posto, Miglioramenti suggeriti (self-improvement, 26/11/2026) (+1 more)

### Community 13 - "costruisci_suggerimento"
Cohesion: 0.20
Nodes (12): _blocco_dati(), costruisci_suggerimento(), domanda_clienti(), domanda_oggi(), domanda_riassunto(), domanda_skill(), test_chiave_sconosciuta(), test_clienti_conta_stati() (+4 more)

### Community 14 - "Guardian dal telefono — guida passo passo"
Cohesion: 0.33
Nodes (5): Guardian dal telefono — guida passo passo, Parte 1 — La dashboard sul telefono (Tailscale), Parte 2 — Parlare con me dal telefono (Remote Control), Parte 3 — Dopo: conto e soldi (quando ci sarà la SRL), Se qualcosa non va

### Community 15 - "Streamlit 1.67: app fluida e reattiva - 12 tecniche"
Cohesion: 0.12
Nodes (15): 10. Navigazione tra "spazi": st.navigation + st.Page (N), 11. Sfondi animati e HTML: st.html, non components.v1.html (H, CH), 12. Interattivita' bidirezionale solo con componenti v2 (V2), 1. Fragment per aggiornare solo una parte (F, FC), 2. Live update con run_every (F, FC), 3. st.rerun(scope="fragment") invece di st.rerun() (F), 4. Fragment con key + st.rerun("key") da callback (F, FC), 5. parallel=True per fragment lenti e indipendenti (F, FC) (+7 more)

### Community 16 - "dashboard/app.py"
Cohesion: 0.14
Nodes (17): _chiudi_dettaglio(), dati_attivita(), dati_clienti(), dati_sessioni(), dettaglio_agente(), fa(), griglia_agenti(), microfono() (+9 more)

### Community 17 - "chiave_widget"
Cohesion: 0.50
Nodes (3): sez_store(), chiave_widget(), test_chiave_widget_stabile()

### Community 18 - "PROMPT_CLAUDE_CODE.md"
Cohesion: 0.14
Nodes (13): BACKLOG DASHBOARD (una milestone alla volta, con test e commit; `sviluppatore-dashboard` + `revisore-qualita`), CICLO AUTOMATICO (avvialo dopo M1), DEFINIZIONE DI "FATTO" PER OGNI COMPITO, EVERYTHING CLAUDE CODE (ECC) — installazione SICURA, solo un sottoinsieme, FASE 0 — Preparazione (una volta sola, poi riporta in 5 righe), FORMATO DEI TUOI REPORT (sempre, max 8 righe), LA SQUADRA (tu sei il manager), PIANO SRL (3 mesi, 12 settimane) — BOZZA DA VERIFICARE (+5 more)

### Community 19 - "catalogo.py"
Cohesion: 0.12
Nodes (16): carica_mappa_it(), categoria_agente(), filtra(), leggi_frontmatter(), percorso_skill(), raggruppa(), scheda_agente(), test_categorie_agenti() (+8 more)

### Community 20 - "PROMPT_NOTTE.md"
Cohesion: 0.17
Nodes (11): EVERYTHING CLAUDE CODE (ECC), FASE A — Ricerca interfacce e design (prima di scrivere codice grafico), FASE B — Dashboard più dinamica e fluida (stile Cyberpunk 2077 evocato), FASE C — La fabbrica di agenti (almeno 5 nuovi agenti, creati da altri agenti), FASE D — Ricerca clienti a Cagliari (sul PC, con web libero), MISSIONE, NOTIFICHE, Prompt per Claude Code (Opus 5.5) — lavoro autonomo notturno su Guardian, squadra di agenti e ricerca clienti (+3 more)

### Community 21 - "Video.tsx"
Cohesion: 0.30
Nodes (7): Root(), Carosello(), Carta(), COLORI, Cta(), Titolo(), Video()

### Community 22 - "03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)"
Cohesion: 0.18
Nodes (10): 03 — Interfaccia e design (Cyberpunk evocato, fluido, utile), 1. Linguaggio visivo, 2. Struttura (wireframe), 3. Il pannello Consumi (il cuore), 4. Pannello Agenti, 5. Pannello Clienti e Costi, 5b. Pannello Guardian (chat col manager), 5c. Prestazioni, accessibilità, mobile (+2 more)

### Community 23 - "05 — Clienti, pipeline e visite di persona"
Cohesion: 0.18
Nodes (10): 05 — Clienti, pipeline e visite di persona, Agenti coinvolti (catena), Archiviazione, Campi di un lead, Cosa cercare (problemi risolvibili da noi), Limiti e onestà, Obiettivo, Pannello Clienti (+2 more)

### Community 24 - "Prompt per Claude Code — Obiettivo: 10.000 € al mese (due soci, Cagliari)"
Cohesion: 0.18
Nodes (10): 0. Leggi (e basta, nell'ordine), 1. Regole non negoziabili, 2. Il modello di business (da validare, non da credere), 3. Trovare i clienti (la macchina commerciale), 4. Il lavoro dei soci sul campo, 5. Prodotti da realizzare (in quest'ordine, uno alla volta), 6. Vendita e contratti (senza consulenza legale), 7. Ritmo di lavoro e controllo (+2 more)

### Community 25 - "test_robustezza.py"
Cohesion: 0.12
Nodes (16): leggi_usage(), descrivi_usage(), _epoch(), eta_dato(), etichetta_reset(), test_chat_continua_con_storico_non_scrivibile(), test_dati_vecchi_oltre_10_minuti(), test_five_hour_null_file_recente_appena_azzerato() (+8 more)

### Community 26 - "2. Lavori automatici"
Cohesion: 0.20
Nodes (9): 1. Connettori Gmail / Calendar / Drive, 2. Lavori automatici, 3. Skill per agenti e subagenti, Cloud /schedule (code.claude.com/docs/en/routines), Desktop scheduled tasks (code.claude.com/docs/en/desktop-scheduled-tasks), Hook Stop e Notification (code.claude.com/docs/en/hooks), /loop (code.claude.com/docs/en/scheduled-tasks), Notifiche push (code.claude.com/docs/en/remote-control) (+1 more)

### Community 27 - "Antica Trattoria Dar Mammozzaro (ristorante, Quartu Sant'Elena)"
Cohesion: 0.20
Nodes (9): Antica Trattoria Dar Mammozzaro (ristorante, Quartu Sant'Elena), Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Problema e prova (+1 more)

### Community 28 - "Bellini B&B (B&B, Cagliari - San Benedetto)"
Cohesion: 0.20
Nodes (9): Bellini B&B (B&B, Cagliari - San Benedetto), Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Problema e prova (+1 more)

### Community 29 - "Bernardi Foto Ottica (ottico, Cagliari)"
Cohesion: 0.20
Nodes (9): Bernardi Foto Ottica (ottico, Cagliari), Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Problema e prova (+1 more)

### Community 30 - "Black and White Parrucchieri (parrucchiere, Selargius)"
Cohesion: 0.20
Nodes (9): Black and White Parrucchieri (parrucchiere, Selargius), Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Problema e prova (+1 more)

### Community 31 - "ChiaroVista di Mario Orru' (ottica, Assemini)"
Cohesion: 0.20
Nodes (9): ChiaroVista di Mario Orru' (ottica, Assemini), Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Problema e prova (+1 more)

### Community 32 - "Comfort & Beauty (Estetica Maxia) (centro estetico, Cagliari)"
Cohesion: 0.20
Nodes (9): Comfort & Beauty (Estetica Maxia) (centro estetico, Cagliari), Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Problema e prova (+1 more)

### Community 33 - "Fenicottero B&B (B&B, Elmas)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Fenicottero B&B (B&B, Elmas), Foto (SOLO con permesso del titolare), Problema e prova (+1 more)

### Community 34 - "Il Borgo (B&B Villanova) (B&B, Cagliari - Villanova)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Il Borgo (B&B Villanova) (B&B, Cagliari - Villanova), Problema e prova (+1 more)

### Community 35 - "Il Cagliarese B&B (B&B, Cagliari - Marina)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Il Cagliarese B&B (B&B, Cagliari - Marina), Problema e prova (+1 more)

### Community 36 - "Le Tre Nasse B&B (B&B, Quartu Sant'Elena)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Le Tre Nasse B&B (B&B, Quartu Sant'Elena), Problema e prova (+1 more)

### Community 37 - "Libarium Nostrum (bar-ristorante, Cagliari - Castello)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Libarium Nostrum (bar-ristorante, Cagliari - Castello), Problema e prova (+1 more)

### Community 38 - "Ottica Borriello (ottica, Quartu S.E., Assemini, Monserrato, Cagliari)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Ottica Borriello (ottica, Quartu S.E., Assemini, Monserrato, Cagliari), Problema e prova (+1 more)

### Community 39 - "Ottica Ungari (ottica, Selargius - Su Planu)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Ottica Ungari (ottica, Selargius - Su Planu), Problema e prova (+1 more)

### Community 40 - "Pani e Casu (ristorante, Cagliari - Castello)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Pani e Casu (ristorante, Cagliari - Castello), Problema e prova (+1 more)

### Community 41 - "Ristorante 51 (ristorante, Cagliari - Via Pola)"
Cohesion: 0.20
Nodes (9): Cosa osservare, Da NON dire, Da sapere prima, Domande al titolare, Esito da registrare, Foto (SOLO con permesso del titolare), Problema e prova, Ristorante 51 (ristorante, Cagliari - Via Pola) (+1 more)

### Community 42 - "theme.py"
Cohesion: 0.11
Nodes (13): dati_costi(), sez_consumi(), sez_costi(), utilizzo_reale(), vista_costi(), vista_statistiche(), barre_orizzontali(), grafico_costi() (+5 more)

### Community 43 - "Prompt per Claude Code (Opus 5.5) — finire Guardian: tempo reale, agenti, manager, clienti"
Cohesion: 0.22
Nodes (8): 1. Leggi in questo ordine (e basta), 2. Missione (cosa deve fare Guardian), 3. Regole che non si negoziano, 4. Risparmio crediti (obbligatorio, dettaglio in `01`), 5. Milestone (dettaglio e criteri AC-1…24 in `06`), 6. Ultimo passo: aprire Streamlit, 7. Cosa mi consegni, Prompt per Claude Code (Opus 5.5) — finire Guardian: tempo reale, agenti, manager, clienti

### Community 44 - "Stili HUD scuri ma accessibili - ricerca"
Cohesion: 0.22
Nodes (8): Contrasti calcolati (a mano, testo su sfondo), Fonti, Principi di stile, Requisiti verificati (fonti lette), Stili HUD scuri ma accessibili - ricerca, Tipografia (font di sistema, nessun download), Variante A - "Cyan Ops" (freddo, moderno), Variante B - "Amber Terminal" (caldo, retro, meno affaticante)

### Community 45 - "Giro di visita consigliato (30 lead confermati; n 20 = Gisella B&B, sostituto di Sun & Sardinia smentito)"
Cohesion: 0.22
Nodes (8): Assemini, Cagliari (per quartiere), Elmas, Fasce prudenti (consiglio), Giro di visita consigliato (30 lead confermati; n 20 = Gisella B&B, sostituto di Sun & Sardinia smentito), Monserrato, Quartu Sant'Elena, Selargius

### Community 47 - "06 — Criteri di accettazione, test, consegna e avvio di Streamlit"
Cohesion: 0.25
Nodes (7): 06 — Criteri di accettazione, test, consegna e avvio di Streamlit, Chiusura: aprire Streamlit e farla vedere al titolare, Criteri di accettazione (misurabili), Esecuzione per milestone (ordine consigliato), Formato del report (max 8 righe), Piano dei test, Ripristino se qualcosa va storto

### Community 48 - "Automazioni dalla dashboard Guardian (ricerca 2026-11-26)"
Cohesion: 0.25
Nodes (7): 1. Cosa c'è (verificato), 2. Lacune della dashboard attuale, 3. Sei automazioni (comandi per PowerShell; sostituire NOME/CARTELLA), 4. Profilo permessi consigliato per i job dalla dashboard, 5. Non verificato, Automazioni dalla dashboard Guardian (ricerca 2026-11-26), Fonti

### Community 49 - "AI Agent Manager — Streamlit Starter"
Cohesion: 0.25
Nodes (7): AI Agent Manager — Streamlit Starter, Before connecting real tools, Deploy on Streamlit Community Cloud, Recommended production architecture, Run locally, What it does, What it does NOT do yet

### Community 50 - "CONTINUA — come riprendere il lavoro (qualsiasi modello)"
Cohesion: 0.29
Nodes (6): Coda del titolare (dopo la plancia, in quest'ordine), CONTINUA — come riprendere il lavoro (qualsiasi modello), Dove sta tutto, Plancia (stato 2026-11-26 pomeriggio), Prossimi passi (in ordine), Regole fisse

### Community 51 - "config.py"
Cohesion: 0.07
Nodes (16): Campionatore, e_processo_claude(), _file_ricavi(), leggi_ricavi(), riepilogo_token(), scrivi_ricavo(), test_monitor_processi_parallelo(), test_cpu_storico_potato() (+8 more)

### Community 52 - "STATO — Operazione 30 clienti (2026-11-26)"
Cohesion: 0.25
Nodes (7): Bloccato, Dashboard Guardian (aggiornato 26/11 sera), Divisione del lavoro (decisa dal titolare, 2026-11-26), Fatto, In coda, In corso, STATO — Operazione 30 clienti (2026-11-26)

### Community 53 - "07 — Esempi online e riferimenti (con provenienza)"
Cohesion: 0.33
Nodes (5): 07 — Esempi online e riferimenti (con provenienza), 1. Già trovato (ricerca precedente), 2. Da cercare (almeno altri 12, con URL letto davvero), 3. Come usare la ricerca senza sprecare token, 4. Prezzi e consumo (riferimento verificato)

### Community 54 - "Audit interfaccia dashboard (giro 11)"
Cohesion: 0.33
Nodes (5): Audit 26/11 sera, Audit interfaccia dashboard (giro 11), Cosa resta, Problemi trovati e corretti, Verifica

### Community 55 - "Come far usare il PC e il browser a Claude (in sicurezza)"
Cohesion: 0.33
Nodes (5): Come far usare il PC e il browser a Claude (in sicurezza), Cosa c'è e cosa fa, Impostazione consigliata (per lavorare di notte senza rischi inutili), Passi, in ordine, "Senza chiedermi nulla": cosa si può e cosa no

### Community 56 - "Ricerca UI "Jarvis" / HUD per assistenti AI (rapporto del 2026-11-26)"
Cohesion: 0.33
Nodes (5): Fonti lette (URL aperti davvero), Integrazione in Streamlit, Non verificato, Pattern realizzabili, Ricerca UI "Jarvis" / HUD per assistenti AI (rapporto del 2026-11-26)

### Community 57 - "Ricerca WhatsApp e Instagram con Claude Code (26/11/2026)"
Cohesion: 0.33
Nodes (5): 1. WhatsApp, 2. Instagram, 3. Server MCP, 4. Raccomandazione (dal piu' sicuro al meno), Ricerca WhatsApp e Instagram con Claude Code (26/11/2026)

### Community 58 - "plancia.py"
Cohesion: 0.15
Nodes (6): _chiave(), data_italiana(), nome_strumento(), normalizza_voce(), riconosci_comando(), test_guida_comandi_esistono()

### Community 59 - "Idee di design (ricerca, nov 2026)"
Cohesion: 0.40
Nodes (4): Da evitare, Dashboard di controllo agenti, Idee di design (ricerca, nov 2026), Siti per attivita' locali

### Community 60 - "Ricerca skill per gli agenti (2026-11-26)"
Cohesion: 0.40
Nodes (4): Comandi, Lacune, Ricerca skill per gli agenti (2026-11-26), Rischi

### Community 61 - "Riconoscimento vocale italiano offline (Windows 11, Python 3.15.2) — 2026-11-26"
Cohesion: 0.40
Nodes (4): Fonti lette, Passi consigliati, Raccomandazione, Riconoscimento vocale italiano offline (Windows 11, Python 3.15.2) — 2026-11-26

### Community 62 - "riassumi_risultato"
Cohesion: 0.29
Nodes (7): accorcia(), _frase_ris(), riassumi_risultato(), test_accorcia_a_fine_parola(), test_riassumi_risultato_browser(), test_riassumi_risultato_libero_tronca(), test_riassumi_risultato_nasconde_metadati_interni()

### Community 63 - "cacciatore-clienti.md"
Cohesion: 0.50
Nodes (3): Come lavori, Consegna, Prima di iniziare

### Community 64 - "guardian-manager.md"
Cohesion: 0.50
Nodes (3): Ciclo, Prima di ogni mossa, Regole

### Community 65 - "scopritore-problemi.md"
Cohesion: 0.50
Nodes (3): Consegna, Cosa cerchi, Regole

### Community 77 - "04 — Agenti, manager Guardian e controllo"
Cohesion: 0.13
Nodes (14): 04 — Agenti, manager Guardian e controllo, 1. Modello dati di un agente, 2. Il manager: Guardian, 3. Coda di approvazioni, 4. Cancello di sicurezza e interruttore (opzionale ma consigliato), 5. Parlare con Guardian, 6. Squadra (ruoli, già nel repo in `squadra/`), 7. Metriche per agente (per migliorare nel tempo) (+6 more)

### Community 100 - "domanda_agente"
Cohesion: 0.20
Nodes (6): domanda_agente(), domanda_ultimo(), durata_testo(), _pulisci(), riassunto_agenti(), test_durata_testo()

### Community 101 - "FonteLocale"
Cohesion: 0.05
Nodes (37): FonteLocale, catalogo_locale(), elenca_skill(), _git(), installa_catalogo_locale(), installa_graphify_locale(), installa_locale(), installa_squadra_locale() (+29 more)

### Community 102 - "test_fonte.py"
Cohesion: 0.22
Nodes (8): leggi_scoperte(), test_demo_e_locale_espongono_scoperte(), test_remota_richiede_token(), test_remota_rifiuta_http_non_locale(), test_scoperte_file_corrotto(), test_scoperte_file_mancante(), test_scoperte_file_valido(), test_scoperte_mancante_o_rotta()

### Community 103 - "testo_evento"
Cohesion: 0.22
Nodes (5): _azione_browser(), testo_browser(), testo_evento(), testo_semplice(), test_testo_semplice()

### Community 105 - "dividi_agenti"
Cohesion: 0.33
Nodes (3): dividi_agenti(), pulisci_risultato(), test_dividi_e_pulisci()

### Community 107 - "titolo_scoperta"
Cohesion: 0.47
Nodes (4): titolo_scoperta(), test_repo(), test_semplice_e_vuoto(), test_skill()

### Community 108 - "streamlit"
Cohesion: 0.22
Nodes (9): barra_laterale(), dialog_conversazioni(), dialog_guida(), dialog_lancia_agente(), dialog_scheda_visita(), dialog_voce(), scegli_cartella(), sez_clienti() (+1 more)

### Community 109 - "theme.py"
Cohesion: 0.09
Nodes (25): dati_catalogo_agenti(), sez_squadra(), nome_ruolo(), raggruppa_agenti(), scheda(), test_dettaglio_tutti_eventi_ed_escape(), test_domanda_agente_limite_e_pulizia(), test_giro8_fermi_vecchi_browser_e_nomi() (+17 more)

### Community 118 - "fonte.py"
Cohesion: 0.14
Nodes (4): get_fonte(), crea_fonte(), _scoperte_vuote(), test_crea_fonte_demo()

## Knowledge Gaps
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Fonte` connect `Fonte` to `re`, `time`, `agenti.py`, `FonteLocale`, `Communities (39 total, 13 thin omitted)`, `FonteRemota`, `🛡️ Guardian — centrale di controllo per Claude Code`, `.usage`, `.documenti_radice`, `PROMPT_CLAUDE_CODE.md`, `PROMPT_NOTTE.md`, `03 — Interfaccia e design (Cyberpunk evocato, fluido, utile)`, `fonte.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Fonte` (e.g. with `God Nodes (most connected - your core abstractions)` and `Suggested Questions`) actually correct?**
  _`Fonte` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Should `voce.py` be split into smaller, more focused modules?**
  _Cohesion score 0.059562841530054644 - nodes in this community are weakly interconnected._
- **Why does `God Nodes (most connected - your core abstractions)` connect `time` to `FonteLocale`, `agenti.py`, `Communities (39 total, 13 thin omitted)`, `FonteRemota`, `Fonte`, `FonteDemo`, `theme.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `FonteLocale` (e.g. with `God Nodes (most connected - your core abstractions)` and `Suggested Questions`) actually correct?**
  _`FonteLocale` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `accesso.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1103448275862069 - nodes in this community are weakly interconnected._
- **Why does `Graph Report - dashboard  (2026-11-26)` connect `Communities (39 total, 13 thin omitted)` to `re`, `time`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._