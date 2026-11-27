# Per gli amici: come collegarsi (5 minuti)

## 1. Una volta sola
1. Accetta l'invito di Menotti al repo su GitHub (arriva per email).
2. Apri **Codex** (chatgpt.com/codex) → *Environments* → crea un ambiente collegato al repo
   `casalimenotti-art/ai-agent-manager` (accedi con il tuo GitHub quando lo chiede).
   Branch di partenza: **`main`** (se Menotti non ha ancora unito, usa `claude/dashboard-pc`).
3. (Per vedere la dashboard) installa Tailscale, accetta il link di condivisione di Menotti, apri
   https://jarvis-7472.tailc3b182.ts.net e inserisci il PIN ospiti che ti dà Menotti a voce.

## 2. Messaggio da incollare a Codex (la prima volta, poi lo fa da solo)

```
Lavori nel repo ai-agent-manager insieme ad altri due agenti. Leggi AGENTS.md e seguilo sempre.
Il mio id nel registro è <amico1 oppure amico2>.
A OGNI nuovo compito, prima di tutto:
1) esegui `python registro/passa.py aperti`;
2) se c'è un passaggio per me o per "chiunque", leggilo tutto, esegui `python registro/passa.py prendi passaggi/<file>.md --chi <mio-id> --agente codex`,
   parti dal branch indicato nel passaggio e continua dai "Prossimi passi";
3) a fine compito: `python registro/scrivi.py --chi <mio-id> --agente codex "cosa hai fatto" --file ...`,
   e se il passaggio è finito `python registro/passa.py chiudi passaggi/<file>.md --chi <mio-id> --agente codex`;
4) se ti fermi a metà: `python registro/passa.py apri --da <mio-id> --agente codex --per chiunque --compito ... --fatto ... --prossimi ...`.
Lavora su un branch tuo (codex/...), fai commit dopo ogni passo che funziona e apri una pull request. Mai segreti o password nei file.
Ora controlla i passaggi aperti e dimmi cosa trovi.
```

## 3. Ogni giorno
Basta scrivere a Codex: **«controlla i passaggi e continua»**.
