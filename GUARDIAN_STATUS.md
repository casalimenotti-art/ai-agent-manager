# GUARDIAN — stato (aggiornato 2026-11-27, branch claude/gallant-sagan-fwncjr)

> Piano v2 approvato: milestone in GUARDIAN_TASKS.md, decisioni in GUARDIAN_DECISIONS.md. **M0 fatta**: codice in `guardian/` (core/ + ui/, una pagina per modulo).

## Funziona (verificato)
- `app.py` (starter) di nuovo avviabile: corretto l'errore di indentazione che lo bloccava.
- **Guardian Hub** `guardian/app.py`: Overview, Agenti, Task, Attività (aggiornamento ogni 20 s), Handoff, Approvazioni, Dispositivi.
  Verificato con AppTest (7 pagine, 0 eccezioni) e nel browser a 1280 px e 390 px (telefono), senza scroll orizzontale.
- Archivio: `SqliteStore` (locale, testato) e `SupabaseStore` (codice pronto; **non provato contro un progetto Supabase reale**).
- Migrazione `supabase/migrations/001_guardian.sql`: provata su PostgreSQL 16 con ruoli anon/authenticated simulati.
  RLS ok (un estraneo vede 0 righe e non può scrivere; anon non legge le tabelle; token_hash non leggibile), RPC del bridge ok e idempotenti, rieseguibile.
- **Guardian Bridge** `bridge/guardian_bridge.py`: heartbeat (anche in loop e da file di stato), event, task-update, checkpoint (+ copia .md locale), pull, sync-registro (anche da tutti i branch). Testato end-to-end in modalità `--local`; payload HTTP verso Supabase testato con un server finto.
- Test: `python -m pytest -q tests` → 21 passati.

## Non ancora attivo
- Supabase e Streamlit Cloud: servono le azioni manuali in `docs/guardian-setup.md`.
- Integrazioni automatiche con Claude Code e Codex: solo interfacce (`guardian/core/adapters.py`). Oggi lo stato arriva da bridge, file di stato e registro.
- Gateway modelli (FreeLLMAPI ecc.): non collegato.
- Plancia locale `dashboard/` (altri branch): non ancora collegata al DB condiviso.

## Prossimo passo
0. Sviluppo: M1 (migrazione 002), vedi GUARDIAN_TASKS.md.
1. Menotti: punti 1-2 di `docs/guardian-setup.md` (Supabase + Streamlit Cloud).
2. Ognuno: registra il PC e avvia il bridge (punto 3).
3. Sviluppo: hook di Claude Code che aggiorna `~/.guardian/stato.json` (StatusFileAdapter.scrivi), poi il collegamento di `dashboard/` al DB condiviso.
