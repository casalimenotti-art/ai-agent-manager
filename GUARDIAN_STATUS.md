# GUARDIAN — stato (aggiornato 2026-11-27, branch claude/gallant-sagan-fwncjr)

> Piano v2 approvato: milestone in GUARDIAN_TASKS.md, decisioni in GUARDIAN_DECISIONS.md. **M0–M6 fatte**: codice in `guardian/` (core/ + ui/); schema v2 (migrazione 002) con progetti, agenti, piani, log, notifiche, memoria, 10 stati dei task e vincoli; SQLite allineato; Bridge v2 (`run`) con stato reale degli agenti da hook Claude Code / notify Codex, log, utilizzo, `claim`; UI con 10 sezioni (Overview con stato reale del sistema, Agenti, Task con progetti/dipendenze/agente, Progetti, Attività con gravità e filtri, Log con filtri, Handoff, Approvazioni dettagliate, Notifiche, Dispositivi); memoria condivisa per progetto/task con fonte e ricerca; handoff v2 (destinatario, test mancanti, dipendenze, note; aperto → preso → chiuso) da Hub e da bridge; export dei task in GUARDIAN_TASKS.md; provider AI OpenAI-compatibili con router (paid escluso di default); sezione «Guardian» con planner (obiettivo → piano → conferma → task), assegnazione, report e prossime azioni.

## Funziona (verificato)
- `app.py` (starter) di nuovo avviabile: corretto l'errore di indentazione che lo bloccava.
- **Guardian Hub** `guardian/app.py`: Overview, Agenti, Task, Attività (aggiornamento ogni 20 s), Handoff, Approvazioni, Dispositivi.
  Verificato con AppTest (7 pagine, 0 eccezioni) e nel browser a 1280 px e 390 px (telefono), senza scroll orizzontale.
- Archivio: `SqliteStore` (locale, testato) e `SupabaseStore` (codice pronto; **non provato contro un progetto Supabase reale**).
- Migrazione `supabase/migrations/001_guardian.sql`: provata su PostgreSQL 16 con ruoli anon/authenticated simulati.
  RLS ok (un estraneo vede 0 righe e non può scrivere; anon non legge le tabelle; token_hash non leggibile), RPC del bridge ok e idempotenti, rieseguibile.
- **Guardian Bridge** `bridge/guardian_bridge.py`: heartbeat (anche in loop e da file di stato), event, task-update, checkpoint (+ copia .md locale), pull, sync-registro (anche da tutti i branch). Testato end-to-end in modalità `--local`; payload HTTP verso Supabase testato con un server finto.
- Test: `python -m pytest -q tests` → 59 passati (compresa la migrazione 001+002 su PostgreSQL 16 con `tests/pg/run.sh`: conversione dati v1, vincoli, trigger, RLS admin/membro/estraneo, notifiche private).

## Non ancora attivo
- Supabase e Streamlit Cloud: servono le azioni manuali in `docs/guardian-setup.md`.
- Integrazione Claude Code: hook pronti e testati con eventi simulati, **non ancora installati su un PC reale**. Codex notify: formato da verificare sui PC degli amici.
- Planner AI: codice pronto e testato con un server finto; **non disponibile finché non configuri un provider** (Secrets).
- Plancia locale `dashboard/` (altri branch): non ancora collegata al DB condiviso.

## Prossimo passo
0. Sviluppo: M7 (smoke test Supabase e documentazione di deploy). Vedi GUARDIAN_TASKS.md.
1. Menotti: punti 1-2 di `docs/guardian-setup.md` (Supabase + Streamlit Cloud).
2. Ognuno: registra il PC e avvia il bridge (punto 3).
3. Sviluppo: hook di Claude Code che aggiorna `~/.guardian/stato.json` (StatusFileAdapter.scrivi), poi il collegamento di `dashboard/` al DB condiviso.
