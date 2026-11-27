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

## Aggiornamento M3 (27/11)
- Fatto: `guardian/ui/status.py` (DB ping con latenza, backend, polling dichiarato, bridge/agenti con segnale), Overview v2, Task v2 (progetto, dipendenze, agente, risultato/errore, criteri; filtro per progetto; 4 gruppi di stati), `projects.py`, `logs.py` (filtri agente/PC/progetto/task/livello/periodo), `notifications.py` (contatore nella barra), Approvazioni v2 (tipo, agente, motivo, impatto, dati, storico), icone di gravità nella timeline.
- Test: 41 passati (AppTest su tutte le 10 sezioni); Playwright a 1280/390 px: 0 eccezioni, nessuno scroll orizzontale.
- Prossimo passo: M4. Metodi memory (add/search/supersede) in entrambi gli store, ricerca `ricerca @@ plainto_tsquery('italian', ...)` in Supabase e LIKE in SQLite; Handoff v2 (campi extra già nel DB: from/to_agent_id, tests_pending, dependencies, important_notes, stato aperto/preso/chiuso) con take/close e notifica al destinatario; `python -m guardian.export_md` per rigenerare GUARDIAN_TASKS.md dal DB (facoltativo).

## Aggiornamento M4 (27/11)
- Fatto: `Handoff` v2 (`tests_pending`, `dependencies`, `important_notes`, `from_agent_id`, `to_agent_id`, `stato`, `da_riga`); store: `handoff`, `take_handoff`, `close_handoff`, `memories`, `add_memory`, `supersede_memory` (SQLite + Supabase); migrazione `004_memoria_handoff.sql` (trigger di notifica, `bridge_checkpoint` v2, `bridge_handoff_take`, `bridge_memory_add/search`); bridge `checkpoint` v2, `handoff-take`, `memory add|search`; UI Memoria e Handoff v2; `python -m guardian.export_md`.
- Test: 46 passati; `tests/pg/run.sh` → CHECK 002/003/004 OK; Playwright Handoff/Memoria a 1280/390 px: 0 eccezioni.
- Prossimo passo: M5. `guardian/providers/` (base.py con Provider e costo free/local/paid; openai_compat.py con base_url+key da env, via stdlib o `openai`; router.py con ordine da config, `GUARDIAN_ALLOW_PAID=false`, fallback su errore/429, registro delle chiamate senza contenuti). Test con un server HTTP finto locale. Nessuna chiave è configurata: tutto deve risultare "non disponibile" senza errori.

## Aggiornamento M5 (27/11)
- Fatto: `guardian/providers/` (base, openai_compat con `estrai_json`, config da env/secrets, router con ALLOW_PAID e fallback). Test con un server HTTP finto: 6 nuovi, 52 in totale.
- Prossimo passo: M6 (planner, assign, report, plans nello store, sezione "Guardian" nella UI).
