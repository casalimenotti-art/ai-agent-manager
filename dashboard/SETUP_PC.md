# Come far usare il PC e il browser a Claude (in sicurezza)

Fonte: documentazione di Claude Code letta da un agente il 26/11/2026 (pagine su chrome, desktop, computer-use, remote-control, permission-modes). Dove la documentazione non dice nulla, è scritto.

## Cosa c'è e cosa fa
| Modalità | Cosa fa | Come si attiva su Windows | Requisiti |
|---|---|---|---|
| **Claude in Chrome** | Usa il **tuo** Chrome (con i tuoi login) | estensione Chrome, poi `claude --chrome` oppure `/chrome` | piano Pro/Max/Ultra/Team/Enterprise, estensione ≥ 1.0.36, `/login` con account claude.ai (non API key); non WSL |
| **Browser integrato** nell'app Desktop | Browser separato, **profilo pulito, senza i tuoi login** | `Ctrl+Shift+B` nell'app | app Claude Desktop |
| **Computer use** | Controlla il desktop (clic, scrittura) | app Desktop → Impostazioni → *This computer* → *System* → **Enable computer use** | su Windows **solo dall'app Desktop**; piani Pro/Max/Ultra (non Team/Enterprise) |
| **Remote Control** | Una sessione che gira **sul tuo PC**, controllabile da claude.ai/code o dall'app sul telefono | `/remote-control` (o `/rc`) in Claude Code, oppure lo switch nell'app Desktop | account claude.ai, piani Pro/Max/Ultra/Team/Enterprise |
| **Sessioni cloud** | Girano su macchine di Anthropic, lavorano su repository GitHub, anche a PC spento | claude.ai/code | **non vedono il tuo PC**: la documentazione non prevede un collegamento diretto a una cartella locale |

**Perché non ho ancora usato il browser dal tuo PC.** Io giro in una sessione cloud e il tuo PC non è collegato (la lista delle cartelle condivise è vuota). La documentazione indica il percorso inverso: una sessione **locale** sul tuo PC (Claude Code) con Remote Control, che tu controlli anche da telefono.

## "Senza chiedermi nulla": cosa si può e cosa no
- **Si può ridurre** le richieste con la modalità permessi (`acceptEdits` o `auto`) e con regole `allow` per comandi precisi (es. `git status`, `pytest`). Nel browser integrato puoi dare "Always allow" a siti precisi.
- **Non si può e non si deve togliere del tutto**: le approvazioni per computer use valgono per la sessione; le scritture su `.git`, `.claude`, `.mcp.json` e simili chiedono sempre conferma; `bypassPermissions` è pensato **solo per macchine virtuali isolate**, non per il tuo PC con account e dati veri.
- Nessuna sessione resta davvero "non presidiata" se un permesso aspetta una risposta: il lavoro si ferma finché non rispondi (anche da telefono con Remote Control).

## Impostazione consigliata (per lavorare di notte senza rischi inutili)
1. **Cartella dedicata** al progetto (`C:\Users\casal\ai-agent-manager`), senza documenti personali dentro.
2. **Profilo Chrome separato** solo per il lavoro con Claude, senza banca, email principale, social personali o account finanziari. Estensione Claude solo lì.
3. **Elenco dei siti consentiti**: solo quelli di ricerca e dei tuoi strumenti.
4. **Computer use**: attivalo solo se serve davvero, solo per le app necessarie; mai su gestori di password, banca, pannelli di sistema. `Esc` lo interrompe.
5. **Permessi**: `acceptEdits` o `auto`; regole `allow` strette; nessuna regola `Bash(*)`.
6. Il PC deve restare **acceso e online** (e, con Remote Control in modalità server, la rete non deve mancare per più di ~10 minuti).
7. Cicli con `/loop`: funzionano solo a sessione aperta e inattiva, scadono dopo 30 giorni.

## Passi, in ordine
1. Installa l'estensione Claude in Chrome nel **profilo dedicato**; in Claude Code scrivi `/chrome` (o avvia con `claude --chrome`).
2. In Claude Code scrivi `/remote-control` per vedere e guidare la sessione da telefono.
3. Se vuoi il controllo del desktop: app Claude Desktop → Impostazioni → This computer → System → Enable computer use. Non farlo ora se non serve.
4. Poi incolla `PROMPT_FINALE.md` e `PROMPT_OBIETTIVO_10K.md`.
