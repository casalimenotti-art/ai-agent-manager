# Regole per gli agenti (Codex e Claude Code)

Questo repository è condiviso da tre persone, ognuna con il proprio agente:

| id | Persona | Agente | Di cosa si occupa | Branch |
|---|---|---|---|---|
| menotti | Menotti | Claude Code | siti, test, software, dashboard Guardian | `claude/*` |
| amico1 | nikoopusce7-bit (GitHub) | Codex | vendite e dati clienti | `codex/vendite` |
| amico2 | salisfrancesco19-stack (GitHub) | Codex | amministrazione | `codex/amministrazione` |

L'elenco ufficiale è `registro/persone.json`. Chiedi alla persona qual è il suo id se non lo sai.

## Registro condiviso: obbligatorio

Tutti e tre devono vedere cosa fa ogni agente. Quindi, **alla fine di ogni compito** (e quando ti blocchi):

1. Scrivi una riga nel registro con il tuo id:
   ```
   python registro/scrivi.py --chi <tuo-id> --agente codex "Cosa hai fatto, in una frase" --file percorso/toccato --esito fatto
   ```
   (`--agente claude-code` se sei Claude; `--esito` può essere `fatto`, `in corso`, `bloccato`, `fallito`.)
2. Fai commit del lavoro **e** della riga del registro sul **tuo** branch, poi push.
   La dashboard di Menotti legge il registro da tutti i branch su GitHub, anche prima del merge.

Regole del registro:
- Scrivi **solo** nel tuo file `registro/<tuo-id>.jsonl`. Mai modificare o cancellare righe esistenti.
- Mai password, chiavi API, token, codici, né dati personali dei clienti (telefoni, email): solo cosa hai fatto e quali file.

## Passaggio di lavoro tra agenti (Claude ↔ Codex)

Se un agente sta per fermarsi (utilizzo quasi finito, fine giornata, compito da passare), **non lascia il lavoro a metà in silenzio**:
1. Fa commit e push di quello che ha fatto, anche se incompleto, sul suo branch.
2. Apre un passaggio:
   ```
   python registro/passa.py apri --da <tuo-id> --agente <claude-code|codex> --per <id o chiunque> --compito "..." --fatto "..." --prossimi "..." --file ...
   ```
   Crea `passaggi/<data>-<id>.md` con cosa stava facendo, cosa è fatto, i prossimi passi e il branch. Commit e push.

**All'inizio di ogni compito** controlla i passaggi aperti: `python registro/passa.py aperti` (dopo `git pull`/`git fetch`).
Se ce n'è uno per te o per «chiunque» e la persona ti chiede di continuare: `passa.py prendi passaggi/<file>.md --chi <tuo-id>`,
parti dal branch indicato, e a lavoro finito `passa.py chiudi ...`. Commit e push ogni volta.

**Ritorno a Claude:** quando un Codex finisce un lavoro che gli ha passato Claude, chiude il passaggio e ne apre uno di ritorno
`--per menotti` con cosa ha fatto, branch/PR e cosa resta: Claude lo riassume a Menotti, che decide come continuare.
(Claude passa il lavoro lungo quando arriva al 60% di utilizzo: il 40% resta a Menotti per le sue richieste.)

## Aggiornare GitHub passo passo

Dopo **ogni passo che funziona** (test verdi): commit piccolo con messaggio chiaro + riga nel registro + push sul tuo branch.
Così gli altri vedono sempre la versione più recente e possono continuare da lì.

## Come si lavora insieme

- Ognuno lavora sul proprio branch e apre una pull request verso `main`. Nessuno modifica i file di un altro senza PR.
- File condivisi: `leads/2026-11-26-30-clienti.csv` (fonte unica dei clienti), `visite/*.md`, `esiti.csv`.
- Nessun agente invia messaggi, email o pubblica qualcosa da solo: prepara bozze, le invia una persona.
- Non committare mai `.env` o altri file con segreti.
