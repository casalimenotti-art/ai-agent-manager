# Guardian Web — Command Center (React)

Nuova interfaccia del Command Center (opzione B del prompt master): `guardian-web/`.
Usa **lo stesso Supabase** di Guardian (tabelle, RLS, trigger, migrazioni 001–005) e **non ha un backend proprio**.
Il Guardian classico in Streamlit (`guardian/app.py`) resta online come riserva e per le funzioni non ancora portate:
il planner AI (le chiavi dei provider non devono stare nel browser) e la registrazione o revoca dei PC.

## Cosa c'è
- **Tre stanze** attorno a Guardian (Sviluppo & Siti, Vendite, Amministrazione): dati nella tabella `stanze`
  (migrazione 005). Ognuna ha un kanban vero, i suoi agenti, le approvazioni e le attività. Si aprono senza cambiare pagina,
  anche a voce o per iscritto ("apri vendite").
- Vista centrale permanente: nucleo di Guardian con stati reali, KPI, prossime azioni, flotta agenti, task attivi,
  approvazioni, attività, aziende.
- Pannelli laterali: su desktop non coprono il centro, su telefono salgono dal basso. Si chiudono con `Esc` e hanno un
  URL condivisibile (`?p=task&id=42`).
- Guardian sempre raggiungibile: barra in basso. Risponde **dai dati, senza AI** a domande come "quanti agenti sono attivi",
  "cosa è bloccato" o "perché questo task è fermo?" (usa il pannello aperto come contesto).
- `Ctrl/Cmd + K`: cerca agenti, task, aziende e approvazioni, oppure manda la domanda a Guardian.
- Realtime vero con Supabase (indicatore "Live"); se il canale non si collega, polling ogni 20 s, dichiarato.
- Voce: solo se il browser supporta la Web Speech API. Annunci a livelli (Silenzio, Critici, Importanti, Tutti), con un
  orario di silenzio e al massimo 6 annunci all'ora.
- Statistiche: ogni numero ha una fonte (catalogo in `guardian-web/PIANO.md`); i grafici hanno una vista tabella e usano
  una palette validata.

## Sviluppo locale
```bash
cd guardian-web
npm ci
cp .env.example .env.local            # metti URL e anon key di Supabase
npm run dev                            # http://localhost:5173
```
Senza Supabase, **solo in locale**: `VITE_DEMO=1 npm run dev`. Dati di esempio in memoria, banner
"Dati di esempio — solo locale", nessuna scrittura reale.

## Test
```bash
npm test                                             # logica (vitest)
VITE_DEMO=1 npm run build && npm run preview &        # poi:
npm run e2e                                          # Playwright: controlli, 4 larghezze, axe, console pulita
```
La suite Python (`python -m pytest -q tests`) e `bash tests/pg/run.sh` restano quelle del backend.

## Messa online (gratis, hosting statico)
Cloudflare Pages (consigliato), Vercel o Netlify: le impostazioni sono le stesse.
1. Collega il repo `casalimenotti-art/ai-agent-manager`.
2. **Root directory** `guardian-web`; **build command** `npm ci && npm run build`; **output** `dist`.
3. Variabili d'ambiente:
   - `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`: solo la chiave anon pubblica, **mai la service_role**;
   - `VITE_GUARDIAN_CLASSICO_URL`: facoltativa, il link all'app Streamlit;
   - **non** impostare `VITE_DEMO`.
4. Supabase → *Authentication* → *URL Configuration*: aggiungi il dominio del sito in *Site URL* / *Redirect URLs*.
5. Apri il sito ed entra con un account presente in `public.users` (come per Streamlit).
6. Controlla che l'header dica "Live": la diretta usa la pubblicazione `supabase_realtime`, già configurata dalle migrazioni.

## Sicurezza
- Nel browser c'è solo la anon key; ogni lettura e scrittura passa dalle regole RLS:
  - un account non autorizzato vede tabelle vuote;
  - `devices.token_hash` non è leggibile.
- Prima di salvare, i testi vengono controllati per non contenere password o chiavi (stesso filtro di `registro/scrivi.py`).
- Le approvazioni registrano solo la decisione: Guardian non invia email, non paga e non pubblica.

## Limiti noti (onesti)
- La logica "prossime azioni", le metriche e gli stati sono **duplicati in TypeScript** rispetto a Python, con test da
  entrambe le parti. Da spostare in RPC SQL se divergono.
- Non esiste un motore di workflow: la sezione lo dice invece di mostrare flussi finti.
- Non esistono ricavi, spese e clienti nel database: non vengono mostrati.
- Non provato contro un Supabase reale da questo ambiente: va eseguito lo smoke test (`scripts/smoke_supabase.py`) e
  poi aperta la web app con un account vero.
