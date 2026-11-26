# 🛡️ Guardian — centrale di controllo per Claude Code

**Avvio a un clic:** doppio clic su `dashboard/avvia.bat` (Windows) oppure `dashboard/avvia.sh` (macOS/Linux). Al primo giro crea l'ambiente e installa tutto, poi apre il browser su http://localhost:8501.

Avvio manuale:

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py --server.address localhost
```

Copia `dashboard/.env.example` in `dashboard/.env` per cambiare percorsi, intervalli e permessi.
Test: `python -m pytest dashboard/tests`.

| Modulo | Compito |
|---|---|
| `app.py` | 6 tab (Statistiche, Costi & Output, Agenti, Agente centrale, Skill, Store), fragment `run_every` |
| `theme.py` | tema cyberpunk, componenti HTML, grafici Altair |
| `monitor.py` | processi Claude, CPU totale + storico 2 min, riepilogo token, ricavi manuali |
| `agenti.py` | indice incrementale dei JSONL: sessioni, costi per giorno/ora/progetto/modello, output |
| `chat.py` | `claude -p` in subprocess, stream-json, `--resume` |
| `skill.py` | elenco skill, prompt, installazione da GitHub, catalogo verificato (Store) |
| `fonte.py` | interfaccia `Fonte`: `FonteLocale` (PC) e `FonteRemota` (agent HTTP + token) |
| `hooks/guardian_hook.py` | hook opzionale → `~/.claude/guardian/events.jsonl` |

Hook opzionali: la tab **Agenti** mostra lo snippet da incollare in `~/.claude/settings.json`.

**Costi.** Token × listino ufficiale per modello (cache read/write e soglia Haiku 5.5 inclusi, verificato sulla pagina prezzi il 2026-11-26).
Sono una stima: con un abbonamento a tariffa fissa non è ciò che paghi. Override: `PRICES_JSON` nel `.env`.
**Ricavi.** Si inseriscono a mano nella tab Costi (salvati in `~/.claude/guardian/ricavi.json`) per calcolare margine e ritorno.
**Store.** Catalogo fisso di skill di design lette e scansionate prima dell'inserimento; si installano in `~/.claude/skills`
senza sovrascrivere nulla e con il commit di origine registrato in `.guardian-source.json`.
