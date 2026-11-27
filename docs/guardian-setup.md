# Guardian Hub — messa in funzione (una volta sola)

Guardian Hub = dashboard condivisa in cloud (`guardian/app.py`) + database Supabase + Guardian Bridge su ogni PC.
Non sostituisce la plancia locale `dashboard/` (branch `claude/dashboard-pc` / `codex/dashboard`): è il punto comune dei tre.

```
PC (bridge, solo HTTPS in uscita) ──RPC con token del PC──► Supabase (Postgres + RLS)
Telefono / PC (browser) ──login email+password──► Streamlit Cloud: guardian/app.py ──► Supabase
registro/*.jsonl su GitHub ──bridge sync-registro──► timeline Attività
```

## 1. Supabase (Menotti, ~10 min, piano gratuito)
1. https://supabase.com → *New project* (regione EU, es. Frankfurt). Salva la password del DB nel tuo gestore password.
2. *SQL Editor* → incolla ed esegui, in ordine, `supabase/migrations/001_guardian.sql` poi `002_command_center.sql`, `003_bridge_agenti.sql` e `004_memoria_handoff.sql`
   (ogni migrazione è rieseguibile; prima del commit è provata su PostgreSQL con `bash tests/pg/run.sh`).
3. Sempre nel SQL Editor, crea i 3 collaboratori con le **loro** email (blocco commentato in fondo al file SQL):
   ```sql
   insert into public.users (id, nome, email, ruolo, agente) values
     ('menotti','Menotti','…','Siti, test, software, dashboard','Claude Code'),
     ('amico1','nikoopusce7-bit','…','Vendite e dati clienti','Codex'),
     ('amico2','Amico 2','…','Amministrazione','Codex');
   ```
4. *Authentication* → *Sign In / Providers* → Email: attivo; disattiva **Allow new users to sign up**.
   *Authentication* → *Users* → *Add user* → una per email (password a scelta, ognuno poi la cambia).
   Solo le email presenti in `public.users` vedono i dati (regole RLS): un account estraneo vede tabelle vuote.
   Poi rendi admin il titolare: `update public.users set accesso = 'admin' where id = 'menotti';`
   (solo un admin modifica gli utenti e può revocare i PC degli altri).
5. *Project Settings* → *API*: copia **Project URL** e **anon public key** (mai la `service_role`).

## 2. Streamlit Community Cloud (Menotti, ~5 min)
1. https://share.streamlit.io → *Create app* → repo `casalimenotti-art/ai-agent-manager`, branch (dopo il merge: `main`), file **`guardian/app.py`**.
2. *Advanced settings* → *Secrets*: incolla il contenuto di `.streamlit/secrets.toml.example` con URL e anon key veri.
3. Se il repo è privato, l'app chiede di autorizzare Streamlit su GitHub. L'indirizzo `https://….streamlit.app`
   si può aprire da PC e telefono; senza login non mostra nulla.

## 3. Ogni PC (ognuno sul proprio)
1. `git pull` del repo, Python 3.10+ (il bridge usa solo la libreria standard).
2. Hub → *Dispositivi* → *Registra un PC* → copia il token (mostrato una volta).
3. `cp bridge/.env.example bridge/.env` e compila URL, anon key e token. Poi l'agente di quel PC:
   - Menotti: `GUARDIAN_CLAUDE_AGENT_ID=menotti-claude` e `python bridge/install_hooks.py claude` (mostra le modifiche) →
     `python bridge/install_hooks.py claude --apply` (chiede conferma e fa una copia di `~/.claude/settings.json`).
     Se c'è già l'hook della plancia locale (`guardian_hook.py`), per quegli eventi non ne aggiunge un secondo.
     L'utilizzo 5h/7g arriva dalla statusline della plancia (`usage.json`), se è attiva.
   - Amici con Codex: `GUARDIAN_CODEX_AGENT_ID=amico1-codex` (o `amico2-codex`) e `python bridge/install_hooks.py codex`
     → aggiungere la riga `notify = [...]` in `~/.codex/config.toml`. **Da verificare**: dopo un turno di Codex deve
     comparire una riga in `~/.guardian/codex-events.jsonl`. Senza questa riga lo stato resta `unknown`.
   - Facoltativo: `GUARDIAN_CAPABILITIES=python,siti,test` e `GUARDIAN_SHARE_PROMPTS=0` per non condividere le richieste.
4. Avvio: `bridge/avvia-bridge.bat` (Windows) o `bridge/avvia-bridge.sh` (un giro ogni 30 s; Ctrl+C = tutto offline).
   Per avviarlo all'accensione: Utilità di pianificazione di Windows → "All'accesso" → `avvia-bridge.bat`.
5. Nell'Hub: *Dispositivi* mostra il PC online, *Agenti* lo stato reale dell'agente (working/idle/needs_approval/unknown).

Cosa viene condiviso: tipo di evento, nome dello strumento, orario, utilizzo % e, se `GUARDIAN_SHARE_PROMPTS=1`,
i primi 200 caratteri delle richieste all'agente (con le chiavi riconosciute sostituite da `[rimosso]`). Mai l'output degli strumenti.

## Comandi del bridge per gli agenti (Claude Code / Codex)
| Quando | Comando |
|---|---|
| inizio task | `python bridge/guardian_bridge.py task-update 4 --stato running` |
| evento utile | `python bridge/guardian_bridge.py event nota "Test passati" --task 4 --file x.py` |
| limite vicino / pausa / passaggio | `python bridge/guardian_bridge.py checkpoint --task 4 --summary "obiettivo + stato" --done "…" --decisions "…" --errors "…" --tests "…" --tests-pending "…" --deps "…" --notes "da non perdere" --next "passo preciso" --to-agent amico1-codex --file a.py` |
| riprendere un passaggio | `python bridge/guardian_bridge.py handoff-take 12 --agent amico1-codex` (stampa tutto il contesto) |
| memoria condivisa | `python bridge/guardian_bridge.py memory add "testo" --tipo decisione --fonte "riunione 27/11"` · `memory search "parole"` |
| fine task | `python bridge/guardian_bridge.py task-update 4 --stato completed` |
| task assegnati a me | `python bridge/guardian_bridge.py pull` (scrive `~/.guardian/inbox.json`, **non** esegue nulla) |
| prendere un task ready | `python bridge/guardian_bridge.py claim 7 --agent menotti-claude` (→ running) |
| importare il registro git | `python bridge/guardian_bridge.py sync-registro --branches` |

Il registro (`registro/scrivi.py`, AGENTS.md) resta obbligatorio: è la traccia in git; il bridge è la vista live.

## Sicurezza
- Nel repo nessuna credenziale: `.env`, `bridge/.env`, `.streamlit/secrets.toml`, `*.db` sono in `.gitignore`.
- Il token del PC è salvato solo come hash sha256; *Revoca token* lo disattiva subito.
- Testi con forma di password/chiave/JWT vengono rifiutati sia dall'Hub sia dal bridge.
- Le azioni esterne passano da *Approvazioni*: Guardian registra la decisione, non esegue invii/pagamenti.

## Sviluppo locale (senza Supabase)
`streamlit run guardian/app.py` → modalità locale su `~/.guardian/hub.db` (dati NON condivisi).
Bridge locale: `python bridge/guardian_bridge.py --local ~/.guardian/hub.db init-local --user menotti --nome PC`.
Export dei task aperti in GUARDIAN_TASKS.md (solo tra i marcatori): `python -m guardian.export_md`.
Test: `python -m pytest -q tests` (include `tests/pg/run.sh` se PostgreSQL è installato).
