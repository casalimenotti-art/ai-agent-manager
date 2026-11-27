# Handoff — Guardian Hub v1

- da: menotti (claude-code) · branch `claude/gallant-sagan-fwncjr` (da main) · 2026-11-27
- stato: v1 completa e testata in locale; in attesa delle credenziali Supabase/Streamlit Cloud del titolare.

## Obiettivo
Dashboard unica in cloud per i 3 collaboratori (PC + telefono): agenti, PC online, task, timeline, handoff, approvazioni.

## Decisioni prese
- Hub nuovo partendo da main (scelta del titolare): `dashboard/` e la PR #2 non sono stati toccati.
- Streamlit (già usato) + Supabase (Postgres, Auth, RLS). Nessun altro framework.
- Bridge solo con libreria standard, in uscita, token per PC (salvato come hash), funzioni RPC `SECURITY DEFINER`: sui PC non c'è nessuna service key.
- Online = heartbeat da meno di 120 s (`models.ONLINE_SECONDI`), calcolato e non dichiarato.
- Formato handoff: `models.Handoff.markdown()` (sezioni: obiettivo/stato, completato, decisioni, problemi, test, file, prossimo passo).

## File
guardian/app.py · guardian/core/{models,store,store_sqlite,store_supabase,adapters}.py · guardian/ui/*.py · bridge/guardian_bridge.py · supabase/migrations/001_guardian.sql ·
tests/{conftest,test_store,test_bridge,test_app}.py · docs/guardian-setup.md · .streamlit/{config.toml,secrets.toml.example} ·
.env.example · bridge/.env.example · .gitignore · requirements.txt · app.py (fix) · GUARDIAN_STATUS.md · GUARDIAN_HANDOFF.md

## Test eseguiti
- `python -m pytest -q tests` → 21 passati.
- Migrazione su PostgreSQL 16 locale con un finto ambiente Supabase: RLS e RPC verificate, eseguita 2 volte senza errori.
- Playwright: Overview e Agenti a 1280 e 390 px, 0 eccezioni.

## Problemi noti
- `SupabaseStore` non è provato contro un'istanza reale (mancano le credenziali): al primo avvio controllare login, creazione task e registrazione PC.
- La timeline si aggiorna con un polling di 20 s, non con un push realtime (la pubblicazione realtime è già abilitata nel DB per il futuro).

## Prossimo passo preciso
Con URL e anon key: creare `.streamlit/secrets.toml`, eseguire `streamlit run guardian/app.py`, fare il login con un utente
presente in `public.users`, creare un task, registrare un PC, poi `python bridge/guardian_bridge.py heartbeat` → il PC deve risultare online.

## Aggiornamento M0 (27/11)
Rinominato `guardian_hub/` → `guardian/`; store diviso in `store.py` (comuni + factory), `store_sqlite.py`, `store_supabase.py`; UI divisa in `guardian/ui/` (un modulo per pagina, `render(ctx)`). Test: 21 passati. Prossimo passo: M1 (vedi GUARDIAN_TASKS.md).

## Aggiornamento M1 (27/11)
- Fatto: `supabase/migrations/002_command_center.sql`; `store_sqlite.py` con migrazione v1→v2 automatica; `store_supabase.py` allineato (i trigger fanno notifiche e cambi di stato, Python scrive solo gli eventi); API nuove: projects/create_project, agents/upsert_agent/set_agent_state, notifications/mark_read, create_task con project/deps/agente, request_approval con action_type/reason/impact/data_involved, ping.
- Test: 28 passati; `bash tests/pg/run.sh` → CHECK 002 OK.
- Da sapere: le tabelle `plans`, `agent_logs` e `memory` esistono già, ma i metodi dello store arrivano in M2 (log), M4 (memoria) e M6 (piani).
- Prossimo passo: M2. In `bridge/collectors/` va un collector che legge `~/.claude/guardian/events.jsonl` (formato dell'hook in `origin/claude/dashboard-pc:dashboard/hooks/guardian_hook.py`) e `usage.json`; poi le RPC `bridge_agent_*` in una migrazione 003 e i metodi specchio in SqliteStore.

## Aggiornamento M2 (27/11)
- Fatto: `supabase/migrations/003_bridge_agenti.sql` (RPC bridge_agent_register/state/logs, bridge_claim_task); specchi in SqliteStore + `agent_logs()` in entrambi gli store; `bridge/collectors/` (base, claude_code, codex), `bridge/hooks/` (claude_hook.py, codex_notify.py), `bridge/install_hooks.py`, comandi `run`, `agent-register`, `claim`; `avvia-bridge.bat/.sh`; pagina Agenti separata dai PC (`models.stato_agente`).
- Test: 37 passati; `tests/pg/run.sh` → CHECK 002 OK + CHECK 003 OK.
- Non verificato dal vivo: hook installati su un PC reale e il formato di Codex notify.
- Prossimo passo: M3. Stato del sistema (`store.ping`, modalità, polling, numero di bridge vivi), Task Manager v2 (progetto, dipendenze, agente assegnato, risultato/errore, 10 stati), pagina Log (`store.agent_logs` con filtri), Notifiche (`store.notifications` / `mark_read`), Approvazioni v2 (action_type, reason, impact, data_involved, agente), Progetti.
