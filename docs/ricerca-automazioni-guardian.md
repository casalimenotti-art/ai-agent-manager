# Automazioni dalla dashboard Guardian (ricerca 2026-11-26)

Complementa ricerca-email-automazioni-skill.md (non ripetuta). Fonti = pagine code.claude.com lette oggi.
Le versioni citate (v2.1.xxx) vengono dalle pagine; verificare con `claude --version`.

## 1. Cosa c'è (verificato)
- Agente con nome: `claude --agent NOME` (sessione intera come quell'agente, prende tools/model). Inline: `--agents '{"nome":{"description":"..","prompt":"..","tools":["Read","Grep"],"model":"sonnet"}}'`; con `-p` anche percorso a file JSON (v2.1.281+). Agenti su file: `.claude/agents/` (progetto) o `~/.claude/agents/`. [sub-agents]
- Frontmatter agente utile: `tools`, `disallowedTools`, `permissionMode`, `maxTurns`, `isolation: worktree`. Limitare Bash a certi comandi = hook PreToolUse che esce con codice 2. [sub-agents]
- Headless: `claude -p "..." --output-format stream-json --verbose --include-partial-messages` = una riga JSON per evento. Il primo evento `system/init` ha modello, tool, MCP. Il messaggio `result` ha costo e session_id. Messaggi dei subagent hanno `parent_tool_use_id` (non null). [headless]
- `--output-format json` dà `session_id` e `total_cost_usd` (stima client). Riprendi con `--resume ID`; `--max-turns N` (solo -p); `--max-budget-usd` citato nella pagina headless (flag non riletto in tabella: da verificare). [headless, cli-reference]
- Con stream-json i rifiuti compaiono come messaggi `permission_denied`; il `result` elenca `permission_denials`. [headless]
- Hook (settings.json): `Notification` (matcher: permission_prompt, idle_prompt, agent_needs_input, agent_completed...), `Stop`, `SubagentStop` (matcher = nome agente), `SessionStart`. Stdin JSON: session_id, transcript_path, cwd, agent_id/agent_type. Su Stop usare `last_assistant_message` (il transcript può essere in ritardo). [hooks]
- Hook `type: "http"`: POST dello stesso JSON a un URL (header, `$VAR` da allowedEnvVars); errore non2xx = non bloccante. Quindi la dashboard può esporre un endpoint locale e ricevere eventi senza leggere i .jsonl. [hooks]
- Scheduling (tabella confronto): cloud (1 h minimo, no file locali, macchina spenta ok), Desktop (locale, 1 min/1 h), `/loop` (solo a sessione aperta, scade dopo 30 giorni, minimo 1 min). [scheduled-tasks]
- Permessi: `--allowedTools "Bash(git diff *)"` (lo spazio prima di `*` conta); `--permission-mode dontAsk` nega tutto ciò che chiederebbe; `--permission-prompts none` (v2.1.259+) per runs senza nessuno che risponde; da v2.1.302 `-p` parte in Manual se nulla imposta la modalità. [headless]
- Regole Bash capiscono `&&`, `;`, `|`: ogni sottocomando deve essere consentito. Regole deny/ask non sono un confine di sicurezza (forme diverse dello stesso programma sfuggono). Su Windows esistono regole `PowerShell(...)`. Per segreti: `Read(./.env)` in deny. `bypassPermissions` solo in VM/container. [permissions]
- `--bare`: salta hook, skill, CLAUDE.md, subagent auto-scoperti, richiede ANTHROPIC_API_KEY (non usa il login abbonamento). Senza `--bare`, un `-p` esegue gli hook di `.claude/settings.json` del progetto senza dialogo di trust. [headless]

## 2. Lacune della dashboard attuale
1. Feed solo da .jsonl: ritardo e nessun evento "serve il tuo OK". Aggiungere hook http -> endpoint locale.
2. Chat con `--resume` bloccante: passare a stream-json per mostrare i passi (tool_use) in diretta.
3. Nessun lancio con nome/budget/permessi per-job: serve un "job runner" con profilo di permessi fisso.
4. Nessun log di costo per job: salvare `total_cost_usd` e `permission_denials` dal `result`.

## 3. Sei automazioni (comandi per PowerShell; sostituire NOME/CARTELLA)
A. "Manda il web-designer su questo cliente"
`claude -p "Rivedi il sito in C:\clienti\NOME e proponi 5 miglioramenti" --agent web-designer --output-format stream-json --verbose --include-partial-messages --permission-mode dontAsk --allowedTools "Read,Grep,Glob" --max-turns 15`
Rischio: se l'agente web-designer ha tools estesi, `--allowedTools` non li restringe: metterli nel file agente. Costo non limitato se manca il tetto (aggiungere `--max-budget-usd`, da verificare).
B. Notifica in tempo reale (Stop + Notification)
settings.json: `"Notification":[{"matcher":"permission_prompt|idle_prompt","hooks":[{"type":"http","url":"http://127.0.0.1:8765/hook"}]}]` e uguale per `Stop`/`SubagentStop`.
Rischio: endpoint locale senza autenticazione = chiunque sul PC può falsificare eventi; usare token in header e bind su 127.0.0.1.
C. Revisione codice in sola lettura prima di consegnare
`claude -p "Rivedi git diff e segnala bug" --permission-mode dontAsk --allowedTools "Bash(git diff *),Bash(git status *),Read" --output-format json`
Rischio basso; leggere `result` e `permission_denials`.
D. Bozza risposta cliente (senza invio)
`claude -p "Scrivi bozza risposta a: ..." --agent redattore --disallowedTools "Bash,Write,Edit" --output-format json`
Rischio: prompt injection se il testo del cliente entra nel prompt: trattarlo come dato, mai dare tool di invio. Verificare che `--disallowedTools` sia accettato da -p (non riletto).
E. Ripresa di un job interrotto da un click
`claude -p "Continua da dove eri" --resume SESSION_ID --output-format stream-json --verbose`
Rischio: `--resume` riporta il costo totale cumulato; con `--fork-session` si evita di toccare la sessione originale.
F. Report ricorrente (mattina)
Cloud task (/schedule, minimo 1 h, fresh clone: NON vede C:\) oppure Desktop scheduled task (locale). Non verificato: sintassi esatta di /schedule (pagina routines non letta).
Rischio: cloud non accede ai file locali dei clienti; locale richiede PC acceso. `/loop` si ferma a 30 giorni.

## 4. Profilo permessi consigliato per i job dalla dashboard
- Default: `--permission-mode dontAsk` + allowlist minima; mai `bypassPermissions`.
- Deny globali in `~/.claude/settings.json`: `Read(./.env)`, `PowerShell(Remove-Item *)`, `Bash(rm *)`, `Bash(git push *)`.
- Dashboard: non costruire il comando concatenando stringhe dell'utente; passare args come lista (subprocess senza shell=True) e il prompt via stdin.
- Un job per volta per cartella; timeout + SIGINT (non SIGTERM) per chiudere il turno in modo pulito. [headless]

## 5. Non verificato
Pagine non lette: agent-sdk/*, routines.md (sintassi /schedule), channels, PermissionRequest hook per approvare dalla dashboard (citato in headless: da leggere). Flag `--max-budget-usd`/`--disallowedTools` con -p: esistono in cli-reference, sintassi da testare.

## Fonti
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/permissions
- https://code.claude.com/docs/en/scheduled-tasks
- https://code.claude.com/docs/en/cli-reference
