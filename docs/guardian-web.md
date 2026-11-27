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
npm run e2e                                          # Playwright: controlli, 4 larghezze, axe, console pulita, PWA offline
npm run e2e:voce                                     # voce locale: microfono finto → servizio del bridge (riconoscitore di prova)
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
7. Sul telefono: apri il sito → Chrome «Installa app» / «Aggiungi a schermata Home», Safari «Condividi → Aggiungi alla schermata Home».
   Si apre a tutto schermo come un'app. Il service worker (`public/sw.js`) salva solo la grafica (HTML, JS, CSS, icone),
   mai i dati: senza rete l'app si apre ma chiede la connessione per mostrare i dati.
8. Per la voce locale sul PC (facoltativa): sul PC `GUARDIAN_HQ_ORIGINI=https://indirizzo-del-sito` e `python bridge/guardian_bridge.py voce`
   (vedi `docs/guardian-setup.md` §3c).
9. Schermo grande in ufficio: `https://indirizzo-del-sito/?parete=1`.

## Il volto di Guardian (sfondo vivo)
Lo sfondo dell'HQ è il volto di **NEXO Sentinel**: un robot originale, renderizzato in Blender con
`tools/volto3d/strati.py` e composto dal vivo da uno shader WebGL2 (`src/volto/`).
- **Si anima solo con cose vere.** Si sveglia a ogni richiesta (chat, voce, palette). Gli anelli girano mentre pensa;
  l'occhio e la griglia pulsano mentre parla; l'iride si apre mentre ascolta. Un evento nuovo produce un lampo; se lo
  interrompi si spegne subito. Gli anelli diventano ambra con le approvazioni, rosso con gli errori. **Non segue il mouse.**
- **Impostazioni → Volto di Guardian**:
  - Animato, Solo immagine o Spento;
  - Vetro forte, Vetro leggero o Pannelli opachi.
- **Ripieghi.** Sul telefono, con «riduci movimento» o senza WebGL2 si vede l'immagine ferma da 960 px con l'occhio che si
  illumina. Senza gli strati si torna al nucleo classico.
- **Ampiezza della voce.** Con la voce del browser è *stimata* parola per parola, perché il browser non dà l'audio della
  sintesi. Lo dice anche Diagnostica voce.
- **Peso.** Circa 2 MB di immagini (WebP) caricati dopo la pagina. Il codice del volto è in un pezzo separato di circa 5 KB.

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
- Ricavi e clienti non sono nel database. Pipeline, scadenze e costi (migrazione 008) ci sono solo se inseriti a mano con la fonte.
- Notifiche push sul telefono: non ancora (servono chiavi VAPID e un piccolo servizio che le invii).
- Non provato contro un Supabase reale da questo ambiente: va eseguito lo smoke test (`scripts/smoke_supabase.py`) e
  poi aperta la web app con un account vero.
