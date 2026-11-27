# Ricerca: email, automazioni, skill (verificata 2026-11-26)

Fonti: code.claude.com/docs (scheduled-tasks, routines, remote-control, sub-agents, skills, hooks, mcp) e support.claude.com/en/articles/10166901 (Use Google Workspace connectors).

## 1. Connettori Gmail / Calendar / Drive
Fonte: support.claude.com/en/articles/10166901
- Gmail: cerca/legge email e metadati allegati; allegati fino a ~12 MB; crea bozze e le elenca; invia, risponde, inoltra; gestisce etichette e thread.
- Calendar: legge eventi/calendari (anche condivisi); crea, modifica, elimina eventi; trova disponibilita comuni; accetta/rifiuta/forse agli inviti.
- Drive: cerca e legge Docs, Sheets, Slides, PDF, immagini, Office (solo testo); carica file, crea cartelle, vede permessi; condivide, sposta, cestina.
- Conferma: fuori da Auto mode serve approvazione esplicita per ogni azione. Nominati: Gmail invia/risponde/inoltra e Drive condividi/sposta/cestina. Calendar ed etichette: la pagina non li separa, vale la regola generale.
- Auto mode: le azioni possono partire senza chiedere, salvo controllo automatico di rischio (la pagina avverte che puo sfuggire qualcosa).
- Nel CLI i connettori compaiono in /mcp come "claude.ai Gmail" ecc. e si disattivano per progetto (code.claude.com/docs/en/mcp). Le singole chiamate seguono le regole permessi MCP: dettaglio conferme in Claude Code = non documentato nella parte letta.
- Consiglio operativo (deduzione, non citato): per le email creare bozze e non inviare.

## 2. Lavori automatici
### /loop (code.claude.com/docs/en/scheduled-tasks)
- `/loop 5m <prompt>` intervallo fisso; senza intervallo Claude sceglie (1 min-1 h). Minimo 1 minuto.
- Limiti: scatta solo con Claude Code aperto e inattivo; chiudere il terminale lo ferma; PC acceso. Nessun recupero dei giri persi. Scadenza ricorrenti: 30 giorni (7 giorni prima della v2.1.330). Max 50 task per sessione. Un /loop auto-ritmato non viene ripristinato con --resume.
- Salta le skill con disable-model-invocation: true.
### Cloud /schedule (code.claude.com/docs/en/routines)
- Girano su cloud Anthropic, anche a PC spento e sessione chiusa. Disponibili su Pro. Si creano con `/schedule` o claude.ai/code/routines. "Research preview".
- Intervallo minimo 1 ora (tabella confronto in scheduled-tasks). Max 100 esecuzioni/ora per account.
- Usano i connettori claude.ai: per default tutti quelli collegati, anche in scrittura (Gmail inclusa); conviene togliere quelli inutili. Partono in auto mode (classificatore al posto delle conferme). Nessun accesso a file locali (clone nuovo).
- Consumano il normale uso dell'abbonamento; se esaurito, le esecuzioni vengono rifiutate fino al reset.
### Desktop scheduled tasks (code.claude.com/docs/en/desktop-scheduled-tasks)
- Locali, persistenti, PC acceso, sessione non necessaria; accedono ai file locali (solo dalla tabella di confronto).
### Hook Stop e Notification (code.claude.com/docs/en/hooks)
- Stop: scatta quando Claude finisce di rispondere; exit 2 o decision:"block" lo fa continuare; riceve last_assistant_message.
- Notification: matcher es. permission_prompt, idle_prompt, agent_completed; non puo bloccare.
- Configurazione in settings.json (`hooks.Stop`, `hooks.Notification`); tipi: command, http, mcp_tool, prompt, agent.
- Windows: shell form usa Git Bash se presente, altrimenti PowerShell; per .ps1 usare powershell.exe -NoProfile -ExecutionPolicy Bypass -File. Gli hook funzionano solo a sessione attiva.
### Notifiche push (code.claude.com/docs/en/remote-control)
- Serve Remote Control attivo (`/remote-control` o `claude remote-control`), app Claude mobile con stesso account, permesso notifiche.
- In `/config`: "Push when Claude decides" (notifiche proattive, es. fine task lunga) e "Push when actions required" (permessi/domande). Si puo chiedere "avvisami quando finiscono i test".
- Limiti: il processo claude locale resta in esecuzione e il PC acceso; chiuso il terminale la sessione va offline; dopo sospensione/rete persa si riconnette (server mode rinuncia dopo ~10 min offline). Non per piani con API key; Pro supportato.

## 3. Skill per agenti e subagenti
- Attivazione automatica: Claude decide dalla `description` (+ `when_to_use`), troncata a 1.536 caratteri; il corpo si carica solo all'uso. disable-model-invocation: true la rende solo manuale (skills).
- Subagenti e strumento Skill: si', per default possono scoprire e invocare skill di progetto/utente/plugin tramite lo strumento Skill (sub-agents). Per impedirlo: omettere `Skill` da `tools` o metterlo in `disallowedTools`.
- Campo `skills` nel frontmatter: precarica il contenuto completo all'avvio (max 32 nomi); non limita l'accesso alle altre. Skill con disable-model-invocation non precaricabili. Gli agenti built-in non precaricano.
- Campo `tools`: lista di strumenti consentiti; se omesso eredita tutto (inclusi gli strumenti MCP/connettori). Per precaricare skill usare `skills`, non elencare `Skill` in tools (sub-agents). Per i connettori: `mcp__<server>` o `mcp__*` in tools/disallowedTools; nome esatto dei connettori claude.ai = non documentato.
- Attenzione: se `tools` e' un elenco senza `Skill`, il subagente non puo invocare skill da solo; allora usare `skills` per precaricarle.
- Alternativa: skill con `context: fork` e `agent: <nome agente in .claude/agents>` esegue la skill dentro quel subagente (skills).
