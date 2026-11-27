@AGENTS.md

Per Claude Code: il tuo id nel registro è `menotti`, quindi a fine compito
`python registro/scrivi.py --chi menotti --agente claude-code "…" --file …`.

Branch della dashboard per Claude: `claude/dashboard-pc` (la versione del PC di Menotti). Commit e push dopo ogni passo che funziona.
Regola del titolare: il 40% dell'utilizzo giornaliero di Claude è riservato alle sue richieste dirette. Quando l'utilizzo arriva al 60% (avviso dell'hook o barra di stato), passa il lavoro lungo a Codex con `registro/passa.py apri --per chiunque` e push, poi rispondi solo alle richieste del titolare.
Quando Codex ripassa il lavoro (passaggio `--per menotti`), riassumi al titolare cosa ha fatto Codex e aspetta il suo ok prima di continuare.
