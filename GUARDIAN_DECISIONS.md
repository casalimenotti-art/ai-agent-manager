# GUARDIAN — decisioni (la più recente in alto; non cancellare le vecchie, segnarle come superate)

- **2026-11-27 · M2: stato agente = ultimo stato riferito dal bridge**, ma `unknown` se il bridge non lo aggiorna da più di 180 s (`models.stato_agente`), e `unknown` se l'hook non produce eventi da 30 min (Claude potrebbe essere chiuso). Codex: solo `idle` dopo un turno (notify non ha un evento di inizio).
- **2026-11-27 · M2: un PC gestisce solo gli agenti del proprio collaboratore** (controllo nelle RPC `bridge_agent_*`); `claim` solo su task `ready` del proprio collaboratore e non assegnati ad altri.
- **2026-11-27 · M2: rimosso `guardian/core/adapters.py`** (solo interfacce non usate), sostituito dai collector reali in `bridge/collectors/`.
- **2026-11-27 · M2: hook Claude nello stesso formato della plancia locale** (`~/.claude/guardian/events.jsonl`): le due cose convivono senza duplicati.

- **2026-11-27 · M1: livello di accesso in `users.accesso` (admin/member)**, non in `ruolo`: `ruolo` contiene già la mansione (registro/persone.json).
- **2026-11-27 · M1: regole nel DB**: titoli unici tra i task aperti dello stesso progetto, al massimo un task `running` per agente, `ready`/`running` solo con dipendenze completate; un'approvazione aperta porta il task in `needs_approval`, l'approvazione lo riporta a `ready` (o `planned`), il rifiuto a `blocked`. In Postgres sono trigger e indici, in SQLite lo stesso comportamento in Python.
- **2026-11-27 · M1: notifiche per utente** (una riga per destinatario, così "letta" è personale), create dai trigger in Postgres.
- **2026-11-27 · M1: stati v1 convertiti** (in attesa→ready, in corso→running, bloccato→blocked, completato→completed); `_valida_task` accetta ancora i nomi v1 come alias.

- **2026-11-27 · Provider AI: nessuno per ora** (titolare). Planner e router vengono preparati e testati con un server finto; nell'UI il planner risulta "non disponibile". `GUARDIAN_ALLOW_PAID=false` di default.
- **2026-11-27 · Log agenti: metadati + prompt troncati a 200 caratteri** (titolare), passati dal filtro segreti, mai output dei tool. Disattivabile per PC (`GUARDIAN_SHARE_PROMPTS=0`).
- **2026-11-27 · Commit + push a ogni milestone** su `claude/gallant-sagan-fwncjr` (titolare). Niente PR né force push.
- **2026-11-27 · Pacchetto `guardian/`** al posto di `guardian_hub/` (rinominato prima di qualsiasi deploy): core (dominio, archivi), ui (una pagina per modulo), poi planner e providers.
- **2026-11-27 · Nessun backend separato**: Supabase (Postgres + Auth + RLS + RPC) fa da backend; la logica LLM gira nel processo Streamlit, separata dalla UI.
- **2026-11-27 · Streamlit resta**; il "realtime" è polling (10–20 s) dichiarato come tale.
- **2026-11-27 · PC ≠ agente**: la presenza del PC viene dagli heartbeat; lo stato dell'agente solo da eventi reali (hook, notify, comandi). Senza eventi: `unknown`.
- **2026-11-27 · Hub nuovo partendo da main** (titolare): `dashboard/` e la PR #2 non si toccano; gli hook Claude esistenti si riusano dal bridge.
- **2026-11-27 · Bridge**: solo HTTPS in uscita, token per PC salvato come hash, RPC `SECURITY DEFINER`; nessuna esecuzione di comandi remoti.
