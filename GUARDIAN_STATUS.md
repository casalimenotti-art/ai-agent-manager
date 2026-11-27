# GUARDIAN — stato (aggiornato 2026-11-27, branch claude/gallant-sagan-fwncjr)

Piano v2 completato nel codice: **M0–M7 fatte** (dettagli in GUARDIAN_TASKS.md, scelte in GUARDIAN_DECISIONS.md).
Manca solo ciò che richiede gli account del titolare: messa online e prova dal vivo.

**Nuovo (27/11): Command Center web** `guardian-web/` (React + Supabase): vista centrale permanente con nucleo di Guardian, pannelli laterali, Realtime, Ctrl+K, risposte dai dati senza AI, voce dal browser, statistiche con fonti. Verificato con vitest, E2E Playwright a 4 larghezze e axe. Guida: `docs/guardian-web.md`.

## Funziona (verificato)
- **Hub** `guardian/app.py` (Streamlit), 12 sezioni: Overview (stato reale del sistema), Guardian (planner + prossime azioni),
  Agenti, Task (10 stati, progetti, dipendenze, agente), Progetti, Attività (gravità, filtri), Log (filtri), Handoff (v2),
  Memoria, Approvazioni (tipo/motivo/impatto/dati), Notifiche, Dispositivi. Login Supabase o modalità locale SQLite.
- **Database**: migrazioni `supabase/migrations/001–004`, provate su PostgreSQL 16 (`bash tests/pg/run.sh`): conversione dati v1,
  vincoli (duplicati, un solo running per agente, dipendenze), trigger (needs_approval, notifiche), RLS admin/membro/estraneo, RPC del bridge.
- **Guardian Bridge** `bridge/`: PC + agenti (`run`), stato reale da hook Claude Code / notify Codex, log (metadati + richieste
  troncate senza segreti), utilizzo 5h/7g, `claim`, `checkpoint` v2, `handoff-take`, `memory`, `sync-registro`; installer hook con conferma.
- **Intelligence** `guardian/planner/` + `guardian/providers/`: piano validato → conferma → task; assegnazione deterministica;
  report e prossime azioni dal database; router OpenAI-compatibile con paid escluso di default.
- **Test**: `python -m pytest -q tests` → 61 passati (store, migrazioni Postgres, bridge, collector, provider con server finto,
  planner, smoke, AppTest di tutte le sezioni). Interfaccia controllata nel browser a 1280 e 390 px.

## Non ancora verificato dal vivo (serve il titolare)
- `SupabaseStore` e login contro un progetto Supabase reale → `scripts/smoke_supabase.py` (guida, punto 4).
- Hook Claude Code su un PC reale; `notify` di Codex sui PC degli amici (formato da confermare; senza, lo stato Codex resta `unknown`).
- Planner AI: non disponibile finché non si configura un provider nei Secrets.

## Prossimi passi
1. Titolare: punti 1–4 di `docs/guardian-setup.md` (Supabase + migrazioni 001–004, utenti, admin; Streamlit Cloud; PC e bridge; smoke test).
2. Amici: punto 3 (token del PC, `GUARDIAN_CODEX_AGENT_ID`, notify) e conferma che compaia `~/.guardian/codex-events.jsonl`.
3. Mettere online `guardian-web/` su Cloudflare Pages (o Vercel/Netlify) seguendo `docs/guardian-web.md`.
4. Unire il branch a `main` con una pull request (dopo l'ok del titolare), poi puntare Streamlit Cloud su `main`.
5. Facoltativo: provider AI per il planner; collegare la plancia locale `dashboard/` (altri branch) allo stesso database.
