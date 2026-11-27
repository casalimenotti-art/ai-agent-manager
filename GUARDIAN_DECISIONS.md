# GUARDIAN — decisioni (la più recente in alto; non cancellare le vecchie, segnarle come superate)

- **2026-11-27 · Provider AI: nessuno per ora** (titolare). Planner e router vengono preparati e testati con un server finto; nell'UI il planner risulta "non disponibile". `GUARDIAN_ALLOW_PAID=false` di default.
- **2026-11-27 · Log agenti: metadati + prompt troncati a 200 caratteri** (titolare), passati dal filtro segreti, mai output dei tool. Disattivabile per PC (`GUARDIAN_SHARE_PROMPTS=0`).
- **2026-11-27 · Commit + push a ogni milestone** su `claude/gallant-sagan-fwncjr` (titolare). Niente PR né force push.
- **2026-11-27 · Pacchetto `guardian/`** al posto di `guardian_hub/` (rinominato prima di qualsiasi deploy): core (dominio, archivi), ui (una pagina per modulo), poi planner e providers.
- **2026-11-27 · Nessun backend separato**: Supabase (Postgres + Auth + RLS + RPC) fa da backend; la logica LLM gira nel processo Streamlit, separata dalla UI.
- **2026-11-27 · Streamlit resta**; il "realtime" è polling (10–20 s) dichiarato come tale.
- **2026-11-27 · PC ≠ agente**: la presenza del PC viene dagli heartbeat; lo stato dell'agente solo da eventi reali (hook, notify, comandi). Senza eventi: `unknown`.
- **2026-11-27 · Hub nuovo partendo da main** (titolare): `dashboard/` e la PR #2 non si toccano; gli hook Claude esistenti si riusano dal bridge.
- **2026-11-27 · Bridge**: solo HTTPS in uscita, token per PC salvato come hash, RPC `SECURITY DEFINER`; nessuna esecuzione di comandi remoti.
