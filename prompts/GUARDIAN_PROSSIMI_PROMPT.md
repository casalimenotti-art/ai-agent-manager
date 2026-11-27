# Guardian — 3 prompt per i passi successivi

Da usare **dopo** la messa online di base (M0–M7 sono fatte; stato in `GUARDIAN_STATUS.md`).
Ordine consigliato: 1 → 2 → 3. Il prompt master del design (`prompts/GUARDIAN_COMMAND_CENTER_MASTER.md`) si può avviare
dopo il prompt 1, in parallelo al 2.
Ogni prompt va incollato come primo messaggio a Claude Code o Codex nella radice del repo.

---

## Prompt 1 — Messa online e collaudo dal vivo

```
Agisci come DevOps e Senior Python Engineer sul repository ai-agent-manager (Guardian, ecosistema NEXO).
Parti in Plan mode. Leggi AGENTS.md, GUARDIAN_STATUS.md, GUARDIAN_HANDOFF.md e docs/guardian-setup.md.
Non rileggere file già riassunti in quei documenti se non serve.

Obiettivo: portare Guardian dal "testato in locale" al "funziona dal vivo per i 3 collaboratori".

1. Prepara una checklist di go-live a partire da docs/guardian-setup.md (punti 1–4): cosa fa il titolare, cosa fanno
   gli amici, cosa posso verificare io. Chiedimi solo ciò che serve davvero: credenziali Supabase in un posto sicuro,
   mai incollate in chat.
2. Quando il titolare ha eseguito scripts/smoke_supabase.py, analizza ogni riga FAIL con il metodo di debugging
   sistematico: causa radice, poi la correzione più piccola, poi il test di regressione. Il punto a rischio è
   guardian/core/store_supabase.py: non è mai stato provato contro un Supabase reale (returning, text_search,
   colonne non leggibili, RLS sulle notifiche).
3. Verifica dal vivo con un utente di prova (mai dati dei clienti):
   - login dei 3 utenti, RLS (un account estraneo vede tabelle vuote);
   - registrazione di un PC, `bridge run` con lo stato dell'agente;
   - creazione e conferma di un task e di un'approvazione;
   - handoff tra due agenti, notifiche.
4. Robustezza in produzione:
   - Supabase free va in pausa dopo ~7 giorni senza attività: documenta come evitarlo (heartbeat dei bridge) e cosa fare se succede;
   - Streamlit Cloud iberna l'app: misura il tempo di avvio a freddo e documentalo;
   - prepara la pulizia periodica dei log (funzione pulisci_log_vecchi) con le istruzioni per pg_cron o l'esecuzione manuale.
5. Quando tutto è verde, prepara (ma non unire) la pull request dal branch di lavoro verso main, con la descrizione
   delle migrazioni 001–004 e dei passi manuali. Unisce solo il titolare.
6. Aggiorna GUARDIAN_STATUS.md e GUARDIAN_HANDOFF.md, scrivi la riga di registro, fai commit e push sul tuo branch.

Regole: niente segreti nel repo o nei log; niente force push; non dichiarare "funziona" senza l'output dello smoke test;
budget di token basso (risposte brevi, nessuna rilettura inutile).
```

---

## Prompt 2 — Agenti reali, handoff automatici e voce

```
Agisci come AI Agent Systems Engineer sul repository ai-agent-manager (Guardian).
Parti in Plan mode. Leggi AGENTS.md, GUARDIAN_STATUS.md, GUARDIAN_DECISIONS.md, bridge/ (collectors, hooks, install_hooks.py)
e la plancia locale sul branch claude/dashboard-pc (dashboard/hooks/, dashboard/voce.py, dashboard/voce_out.py),
solo per riferimento, senza modificarla.

Obiettivo: lo stato degli agenti in Guardian deve essere vero e utile ogni giorno, e il passaggio di lavoro deve avvenire
prima che un agente esaurisca il limite.

1. Claude Code (PC del titolare):
   - verifica bridge/install_hooks.py su un settings.json reale (dry-run, poi --apply con la copia di sicurezza);
   - conferma la convivenza con l'hook della plancia locale;
   - aggiungi un hook Stop/PostToolUse che, quando usage.json supera la soglia (60% di default, come
     dashboard/hooks/guardian_passaggio.py), ricorda all'agente di salvare un handoff completo con
     `bridge/guardian_bridge.py checkpoint`. Non deve mai bloccare Claude.
2. Codex (PC degli amici): verifica il formato reale del programma `notify` con la loro versione di Codex
   (fai registrare loro un turno e leggi ~/.guardian/codex-events.jsonl). Correggi bridge/hooks/codex_notify.py e il
   collector con test basati sul formato vero. Se Codex non espone eventi di inizio turno, documentalo:
   lo stato resta idle/unknown, niente stati inventati.
3. Avvio automatico del bridge:
   - Windows: Utilità di pianificazione, all'accesso, finestra nascosta;
   - macOS/Linux: launchd/systemd utente.
   Con script di installazione e disinstallazione, e un log locale ruotato.
4. Esecuzione assistita dei task (solo se il titolare l'approva in Plan mode): il bridge può proporre all'agente locale
   un task ready assegnato a lui, **solo dopo conferma umana sul PC**. Niente esecuzione remota di comandi arbitrari,
   niente porte aperte. Prima progetta il modello di minaccia, poi implementa.
5. Voce (opzionale, dopo il punto 4): annunci vocali degli eventi importanti nel client web (Web Speech API) con livelli
   Silenzio / Solo critici / Importanti / Tutti e orario di silenzio. Nessun indicatore "in ascolto" se il microfono non è aperto.
6. Test: collector con eventi reali registrati (anonimizzati), installer, avvio automatico (dove possibile in CI), migrazioni
   (tests/pg/run.sh). Aggiorna i file GUARDIAN_*.md, scrivi la riga di registro, fai commit e push sul tuo branch.

Regole: privacy dei log (metadati + richieste troncate a 200 caratteri, senza segreti; GUARDIAN_SHARE_PROMPTS rispettato);
nessuna modifica a ~/.claude o ~/.codex senza conferma esplicita; non usare né simulare gli account personali degli agenti.
```

---

## Prompt 3 — Aziende, metriche reali e report

```
Agisci come Product Engineer e Data Engineer sul repository ai-agent-manager (Guardian, ecosistema NEXO).
Parti in Plan mode. Leggi AGENTS.md, i file GUARDIAN_*.md, supabase/migrations/, guardian/core/ e guardian/planner/report.py.
Se disponibile, usa la skill di data visualization ed eseguine il validatore di palette.

Obiettivo: trasformare i "progetti" in vere "aziende" di NEXO, con metriche reali e un report giornaliero affidabile.

1. Modello dati (migrazione 005, additiva e rieseguibile, provata con tests/pg/run.sh):
   - projects.tipo (es. agenzia AI, siti web, receptionist AI, automazioni: lista configurabile, non fissa nel codice);
   - tabella project_metrics (project_id, nome, valore, unità, periodo, **fonte obbligatoria**, inserito_da, data);
   - eventuali clienti solo come conteggi o riferimenti, **mai dati personali** nel DB condiviso
     (la fonte unica dei clienti resta leads/…csv sul branch delle vendite).
   Allinea SqliteStore e SupabaseStore e aggiungi i test.
2. Metriche operative calcolate (nessun valore fisso nel codice): task completati per giorno, tasso di completamento in una
   finestra dichiarata, durata media da task_started a task_completed, carico per agente, approvazioni medie per giorno,
   errori per agente. Ogni metrica ha nome, definizione, fonte e test con dati sintetici solo locali.
3. Report giornaliero:
   - generato da report() + metriche;
   - salvato in memory (tipo risultato, fonte "report del giorno");
   - scaricabile in Markdown;
   - opzionale: una bozza di email (mai inviata da sola: l'invio richiede un'approvazione).
4. Grafici: solo dove raccontano qualcosa; un solo asse Y; colori per entità con ordine fisso; vista tabellare
   alternativa; tooltip; filtri in una riga sopra i grafici; palette validata sul tema scuro.
5. Domande in linguaggio naturale sulle metriche ("quale azienda lavora di più questa settimana?") tramite un router di
   intenti deterministico. Il modello AI è facoltativo e riceve solo i numeri aggregati.
6. Test, screenshot a 390 e 1280 px, file GUARDIAN_*.md, riga di registro, commit e push.

Regole: ogni numero ha una fonte; stato vuoto onesto se mancano dati; nessun dato d'esempio nel Supabase condiviso;
ricavi e spese solo con una fonte reale approvata dal titolare.
```
