# GUARDIAN — milestone (piano v2, approvato il 27/11)

| # | Milestone | Stato | Note |
|---|---|---|---|
| M0 | Riorganizzazione in `guardian/` (core + ui, nessun cambio funzionale) | ✅ fatto | 21 test verdi |
| M1 | Migrazione 002 (projects, agents, plans, agent_logs, notifications, memory; 10 stati per i task; gravità degli eventi; anti-duplicati) + parità SQLite | ✅ fatto | 28 test; `tests/pg/run.sh` verde |
| M2 | Agenti separati dai PC + Bridge v2 (collectors per hook Claude Code, usage, Codex notify, log, claim, script di avvio) | ⏳ prossimo | Codex notify da verificare sui PC degli amici |
| M3 | UI: stato del sistema, Task Manager v2, Activity con gravità, Log con filtri, Notifiche, Approvazioni v2 | da fare | |
| M4 | Memoria condivisa + Handoff v2 + export dei file .md | da fare | |
| M5 | Provider + router (nessun provider configurato: test con server finto) | da fare | ALLOW_PAID=false |
| M6 | Planner + assegnazione + report e prossime azioni | da fare | planner "non disponibile" senza provider |
| M7 | Doc di deploy + smoke test live | bloccato | servono Supabase/Streamlit Cloud del titolare |
