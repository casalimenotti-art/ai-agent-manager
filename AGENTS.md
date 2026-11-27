# Regole per gli agenti (Codex e Claude Code)

Questo repository è condiviso da tre persone, ognuna con il proprio agente:

| id | Persona | Agente | Di cosa si occupa | Branch |
|---|---|---|---|---|
| menotti | Menotti | Claude Code | siti, test, software, dashboard Guardian | `claude/*` |
| amico1 | nikoopusce7-bit (GitHub) | Codex | vendite e dati clienti | `codex/vendite` |
| amico2 | (da rinominare) | Codex | amministrazione | `codex/amministrazione` |

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

## Come si lavora insieme

- Ognuno lavora sul proprio branch e apre una pull request verso `main`. Nessuno modifica i file di un altro senza PR.
- File condivisi: `leads/2026-11-26-30-clienti.csv` (fonte unica dei clienti), `visite/*.md`, `esiti.csv`.
- Nessun agente invia messaggi, email o pubblica qualcosa da solo: prepara bozze, le invia una persona.
- Non committare mai `.env` o altri file con segreti.
