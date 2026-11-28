# Prompt per Codex: collega il PC di Niko o di Francesco a Guardian HQ

**Per l'amico (Niko = `amico1`, vendite; Francesco = `amico2`, amministrazione):** apri Codex nella cartella del repo `casalimenotti-art/ai-agent-manager` (se non ce l'hai, Codex te la scarica al passo 2) e incolla tutto questo file. Codex fa il lavoro e ti chiede solo le cose che puoi fare tu: login, password, codici.

---

Sei il Codex di un socio di NEXO SRL. Il tuo compito è **collegare questo PC a Guardian HQ**, la dashboard condivisa del team, passo per passo, spiegando in parole semplici. Fai tu tutto quello che puoi fare da terminale. Fermati e chiedi alla persona **solo** quando servono login, password, codici o un clic suo.

## Cosa esiste già (non ricrearlo)
- **Dashboard online**: https://guardian-nexo.pages.dev, con database Supabase "guardian-nexo" e login obbligatorio.
- **Repo**: `casalimenotti-art/ai-agent-manager`. Il codice della dashboard e del bridge sta sul branch `claude/gallant-sagan-fwncjr`, cartelle `guardian-web/` e `bridge/`.
- **Regole comuni**: `AGENTS.md`, cioè registro condiviso, branch personale e niente invii senza ok umano. Leggile per prime.
- **Guida tecnica del collegamento**: `guardian-web/docs/collega-pc.md`.

## Passi
1. **Chi sei**: chiedi alla persona se è Niko (`amico1`, stanza Vendite, branch `codex/vendite`) o Francesco (`amico2`, stanza Amministrazione, branch `codex/amministrazione`). Da qui in poi usa quell'id.
2. **Prerequisiti** (controlla, e installa solo con il suo ok):
   - Git e Python 3.11 o più recente. Su Windows: `winget install Git.Git` e `winget install Python.Python.3.12`.
   - Accesso al repo su GitHub. Se `git clone` fallisce con un 404, il titolare (Menotti) deve invitarlo come collaboratore: diglielo e fermati.
   - Poi `git clone https://github.com/casalimenotti-art/ai-agent-manager.git` e `git checkout claude/gallant-sagan-fwncjr`.
3. **Account della dashboard** (lo crea Menotti, non tu):
   - La persona chiede a Menotti di aggiungerla. Menotti la crea in Supabase → Authentication → Users → Add user, con la sua email, e la aggiunge a `public.users` con il suo id.
   - La persona apre https://guardian-nexo.pages.dev ed entra con email e password. **La password la scrive lei**, mai tu.
4. **Codice del PC** (lo crea Menotti dal pannello Dispositivi → Registra PC, scegliendo come persona l'amico):
   - Menotti manda il codice alla persona **in privato**, non in chat di gruppo e non nel repo.
   - Chiedi alla persona di incollarlo lei nel file `.env` (passo 5). Tu non devi leggerlo, stamparlo, salvarlo altrove o farne il commit.
5. **Configurazione del bridge**:
   - Copia `bridge/.env.example` in `bridge/.env`.
   - Inserisci tu i valori non segreti: l'URL della dashboard e l'URL del progetto Supabase (stanno in `guardian-web/docs/collega-pc.md`), il nome dell'agente (`amico1-codex` o `amico2-codex`) e la persona.
   - Per la chiave anon pubblica e il codice del PC, apri il file e lascia che li incolli la persona.
   - Controlla che `bridge/.env` sia in `.gitignore`: **non deve mai finire su GitHub**.
6. **Collegare Codex al bridge**: esegui `python bridge/install_hooks.py --codex`, oppure il comando indicato in `collega-pc.md`. Stampa una riga da incollare nelle impostazioni di Codex: falla incollare alla persona.
7. **Avvio**:
   - Doppio clic su `bridge/avvia-bridge.bat`, oppure `python bridge/guardian_bridge.py` da terminale.
   - Nella dashboard, stanza Vendite o Amministrazione, il PC deve risultare **online** entro 1 minuto, e l'agente deve mostrare cosa sta facendo.
   - Se non succede, leggi l'errore del bridge e risolvilo (URL sbagliato, codice revocato, rete). Non disattivare mai controlli di sicurezza.
8. **Avvio automatico** (facoltativo, solo con l'ok della persona): un collegamento a `avvia-bridge.bat` nella cartella Esecuzione automatica di Windows (`shell:startup`). Così, ogni volta che il PC è acceso, la dashboard lo vede, e Claude di Menotti può passargli il lavoro quando supera il 60% di utilizzo (regola in `CLAUDE.md`).
9. **Fine**:
   - Scrivi la riga di registro `python registro/scrivi.py --chi <id> --agente codex "PC collegato a Guardian HQ" --esito fatto`.
   - Fai commit e push **solo** del registro sul tuo branch personale, mai di `.env`.
   - Riassumi alla persona in 5 righe cosa è stato fatto.

## Dopo il collegamento: come lavorare con il team
- All'inizio di ogni sessione: `git fetch` e `python registro/passa.py aperti` (lo script sta sul branch `claude/dashboard-pc`). Se c'è un passaggio `--per <tuo id>` o `--per chiunque` e la persona vuole continuare, prendilo e segui i "prossimi passi".
- Lavora solo nella tua stanza: Vendite per Niko, Amministrazione per Francesco. Dopo ogni passo che funziona fai commit e push sul tuo branch.
- **Mai**: inviare messaggi, email o post da solo; scrivere password, token o dati personali dei clienti nel repo o nel registro; disattivare l'RLS o le protezioni del database.
