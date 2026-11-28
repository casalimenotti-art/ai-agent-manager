# Guardian HQ: si riparte da qui (28/11/2026)

Prompt da usare all'inizio di ogni sessione, in Claude Code (anche con `/loop`) o in Codex, nella radice del repo.
Il ciclo di lavoro completo è in `prompts/GUARDIAN_HQ_MASTER_V3.md`, la memoria delle ondate in `guardian-web/ROADMAP.md`.
Questo file aggiunge **lo stato reale di oggi** e **l'elenco delle funzioni che il titolare vuole**.

---

## 1. Stato reale (verificato il 28/11)
- **La dashboard è online**: https://guardian-nexo.pages.dev (Cloudflare Pages). È collegata a questo branch, `claude/gallant-sagan-fwncjr`, quindi **ogni push la ripubblica da sola**.
  Impostazioni: cartella `guardian-web`, build `npm ci && npm run build`, uscita `dist`.
- **Database**: progetto Supabase `guardian-nexo`, organizzazione nexo srl, regione Europa.
  - Sono applicate le migrazioni da 001 a 008.
  - Ci sono 19 tabelle e tutte hanno l'RLS attivo.
  - Le iscrizioni libere sono spente.
  - Site URL e redirect puntano a `https://guardian-nexo.pages.dev`.
- **GRANT**: il progetto è stato creato con "Grant API access to new tables" SPENTO. È stato aggiunto a mano `grant select, insert, update, delete on all tables in schema public to authenticated`, insieme alle sequences e ai default privileges.
  **Ogni nuova migrazione deve includere i propri `grant ... to authenticated`.** Mai dare permessi sulle tabelle ad `anon`: il bridge usa solo le RPC.
- **Utenti**:
  - `menotti` è admin (`public.users`, `accesso = 'admin'`).
  - Niko (`amico1`) e Francesco (`amico2`) non hanno ancora un account. Il titolare li crea in Supabase → Add user, poi li si aggiunge a `public.users`.
- **Ancora da fare**:
  - Nessun PC è collegato: bridge non avviato, nessun codice dispositivo.
  - Il "cervello" è spento.
  - Mancano i dati di vendite e amministrazione.

## 2. Prossime ondate (in quest'ordine)
1. **"Registra PC" nella dashboard**: un pulsante, solo per gli admin, che crea il codice dispositivo. Per ora si fa solo dalla dashboard Streamlit vecchia.
   Poi va scritta una guida da 3 passi per avviare `bridge/avvia-bridge.bat` sul PC del titolare, con `.env` presi da `bridge/.env.example`. Mai mettere chiavi nel repo.
2. **Collegare il PC del titolare**:
   - avviare il bridge e il cervello (`guardian_bridge.py cervello`), così Guardian risponde con il Claude Code del titolare;
   - verificare in dashboard che il PC risulti "online" e che gli agenti si vedano in diretta.
3. **Ingresso dei soci**: aggiungere i soci a `public.users` (con email inserite dal titolare). Poi bridge sui loro PC e collegamento del loro Codex.
4. **"Codex a distanza"**: le domande per Niko o Francesco passano al loro Codex in sola lettura. ✋ Solo con il loro ok, perché usa il loro abbonamento.
5. **Lo stile del video**: il titolare manderà un video di come vuole la dashboard.
   - Salvarlo in `docs/riferimenti/` e descrivere in `VOLTO-STILE.md` cosa cambia.
   - Applicare le modifiche a ondate, ognuna confrontata con il video tramite screenshot.

## 3. Funzioni che il titolare vuole (backlog completo, da raccolta delle sessioni 26-28/11)
| Area | Funzione | Regola |
|---|---|---|
| Voce | Conversazione a voce continua, risposta parlata con voce italiana locale, barge-in | L'audio non esce dal PC; testo riconosciuto sempre visibile |
| Volto/logo | Si muove sempre: riposo, ascolto, pensa, parla (pulsa con le parole) | Prefers-reduced-motion rispettato |
| Telefono | PWA installabile; su Tailscale c'è già il link alla dashboard Streamlit | Login obbligatorio |
| Team | Stanze per Menotti, Niko e Francesco; diretta degli agenti; passaggi Claude ↔ Codex | Al 60% di utilizzo Claude passa il lavoro lungo |
| Approvazioni | Centro unico "da approvare": invii, pubblicazioni, spese | Niente parte senza un sì umano |
| Instagram | Coda DM con bozze di risposta, invio con un tocco | Solo API ufficiale Meta (`docs/instagram-dm-ufficiale.md`), mai librerie non ufficiali |
| Email | Bozze Gmail (connettore già presente) | Invio solo con ok per ogni messaggio |
| WhatsApp | Solo WhatsApp Business API ufficiale | Mai automazioni non ufficiali |
| Vendite | Lead dal CSV (`leads/`), pipeline, visite, preventivi, siti demo dei clienti | Il DB rifiuta telefoni ed email nei campi liberi |
| Amministrazione SRL | Scadenze, costi, documenti, calendario (connettore Google Calendar) | ✋ Ok al connettore |
| Discoteca / PR | Liste, tavoli, serate, bozze per i locali (es. Patron) | Niente dati inventati |
| Cassa | Revolut Business in **sola lettura**, dopo l'apertura della SRL | Mai pagamenti né bonifici |
| Utilizzo | Barra di utilizzo di Claude (5 ore e settimana) visibile in alto | — |
| Sicurezza | Accesso con login; "Registra PC" solo per l'admin; registro di chi entra | Nessun segreto nel repo o nel browser |

## 4. Chi lavora: regola del titolare (28/11), da controllare all'inizio di OGNI giro
1. Leggi l'utilizzo **settimanale** di Claude da `~/.claude/guardian/usage.json` (`seven_day.pct`).
2. Controlla se il PC di Niko o di Francesco è **acceso e collegato**:
   - nel database, tabella `devices` (o `agents`), guarda se il loro dispositivo ha dato segno di vita negli **ultimi 5 minuti**;
   - in alternativa guarda la dashboard: un PC "online" nella stanza Vendite o Amministrazione.
3. Decidi:
   - **settimana ≥ 60% e un PC amico online** → apri un passaggio per quel socio (`--per amico1` o `--per amico2`). Lo prende il suo Codex. Fai commit e push, poi rispondi solo alle richieste dirette del titolare.
   - **settimana ≥ 60% ma nessun PC amico online** → **continua tu**, a giri piccoli. Ricontrolla al giro dopo.
   - **settimana ≥ 95%** → fermati comunque: salva lo stato, apri un passaggio `--per chiunque` e avvisa il titolare.
   - **settimana < 60%** → continua tu.
4. Se lavori a ciclo continuo, a fine giro rimanda a te stesso questo stesso prompt (in Claude Code: `/loop` dinamico). Ogni giro rifà il controllo del punto 4.

Stato al 28/11: nessun PC amico è registrato, quindi per ora continua Claude.

## 5. Regole del giro (come nel MASTER V3, in breve)
- Una ondata piccola per giro, così: test → build → E2E → **screenshot vero a 1440 e 390 px** → commit → push. Il push ripubblica il sito.
- Aggiorna `guardian-web/ROADMAP.md` e scrivi la riga nel registro (`registro/scrivi.py`).
- Se l'utilizzo supera il 60%: `registro/passa.py apri --per chiunque` e push.
- Il "fatto" vale solo dopo averlo visto a schermo sul sito pubblicato.
