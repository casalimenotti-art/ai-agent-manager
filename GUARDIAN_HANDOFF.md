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
guardian_hub/{__init__,app,store,models,adapters}.py · bridge/guardian_bridge.py · supabase/migrations/001_guardian.sql ·
tests/{conftest,test_store,test_bridge,test_hub_app}.py · docs/guardian-setup.md · .streamlit/{config.toml,secrets.toml.example} ·
.env.example · bridge/.env.example · .gitignore · requirements.txt · app.py (fix) · GUARDIAN_STATUS.md · GUARDIAN_HANDOFF.md

## Test eseguiti
- `python -m pytest -q tests` → 21 passati.
- Migrazione su PostgreSQL 16 locale con un finto ambiente Supabase: RLS e RPC verificate, eseguita 2 volte senza errori.
- Playwright: Overview e Agenti a 1280 e 390 px, 0 eccezioni.

## Problemi noti
- `SupabaseStore` non è provato contro un'istanza reale (mancano le credenziali): al primo avvio controllare login, creazione task e registrazione PC.
- La timeline si aggiorna con un polling di 20 s, non con un push realtime (la pubblicazione realtime è già abilitata nel DB per il futuro).

## Prossimo passo preciso
Con URL e anon key: creare `.streamlit/secrets.toml`, eseguire `streamlit run guardian_hub/app.py`, fare il login con un utente
presente in `public.users`, creare un task, registrare un PC, poi `python bridge/guardian_bridge.py heartbeat` → il PC deve risultare online.
