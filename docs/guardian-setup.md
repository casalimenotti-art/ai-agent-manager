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
2. *SQL Editor* → incolla tutto `supabase/migrations/001_guardian.sql` → *Run*.
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
5. *Project Settings* → *API*: copia **Project URL** e **anon public key** (mai la `service_role`).

## 2. Streamlit Community Cloud (Menotti, ~5 min)
1. https://share.streamlit.io → *Create app* → repo `casalimenotti-art/ai-agent-manager`, branch (dopo il merge: `main`), file **`guardian/app.py`**.
2. *Advanced settings* → *Secrets*: incolla il contenuto di `.streamlit/secrets.toml.example` con URL e anon key veri.
3. Se il repo è privato, l'app chiede di autorizzare Streamlit su GitHub. L'indirizzo `https://….streamlit.app`
   si può aprire da PC e telefono; senza login non mostra nulla.

## 3. Ogni PC (ognuno sul proprio)
1. `git pull` del repo, Python 3.10+ (il bridge usa solo la libreria standard).
2. Hub → *Dispositivi* → *Registra un PC* → copia il token (mostrato una volta).
3. `cp bridge/.env.example bridge/.env` e compila URL, anon key, token, `GUARDIAN_AGENT` (Claude Code / Codex).
4. Prova: `python bridge/guardian_bridge.py heartbeat` → nell'Hub il PC diventa *online*.
5. Lasciare acceso mentre si lavora: `python bridge/guardian_bridge.py heartbeat --loop 60 --status-file ~/.guardian/stato.json`
   (Ctrl+C → offline). Il file di stato, facoltativo, si aggiorna a mano o da script:
   `{"stato":"occupato","current_task":4,"model":"…","limit_reached":false,"error":null}`.

## Comandi del bridge per gli agenti (Claude Code / Codex)
| Quando | Comando |
|---|---|
| inizio task | `python bridge/guardian_bridge.py task-update 4 --stato "in corso"` |
| evento utile | `python bridge/guardian_bridge.py event nota "Test passati" --task 4 --file x.py` |
| limite vicino / pausa | `python bridge/guardian_bridge.py checkpoint --task 4 --summary "obiettivo + stato" --done "…" --decisions "…" --errors "…" --tests "…" --next "passo preciso" --file a.py` |
| fine task | `python bridge/guardian_bridge.py task-update 4 --stato completato` |
| task assegnati a me | `python bridge/guardian_bridge.py pull` (scrive `~/.guardian/inbox.json`, **non** esegue nulla) |
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
Test: `python -m pytest -q tests`.
