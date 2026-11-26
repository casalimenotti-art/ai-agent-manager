# 🛡️ Guardian — centrale di controllo per Claude Code

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py --server.address localhost
```

Copia `dashboard/.env.example` in `dashboard/.env` per cambiare percorsi, intervalli e permessi.
Test: `python -m pytest dashboard/tests`.

| Modulo | Compito |
|---|---|
| `app.py` | tab, tema scuro, fragment `run_every` |
| `monitor.py` | processi Claude, CPU totale + storico 2 min, riepilogo token/costo |
| `agenti.py` | indice incrementale dei JSONL in `~/.claude/projects` + eventi hook |
| `chat.py` | `claude -p` in subprocess, stream-json, `--resume` |
| `skill.py` | elenco skill, prompt, installazione da GitHub |
| `fonte.py` | interfaccia `Fonte`: `FonteLocale` (PC) e `FonteRemota` (agent HTTP + token) |
| `hooks/guardian_hook.py` | hook opzionale → `~/.claude/guardian/events.jsonl` |

Hook opzionali: la tab **Agenti** mostra lo snippet da incollare in `~/.claude/settings.json`.
