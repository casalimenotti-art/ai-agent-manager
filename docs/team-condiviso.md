# Lavorare in tre: registro condiviso e dashboard per gli amici

Tre persone, tre agenti: Menotti con Claude Code, due amici con Codex (piano ChatGPT).
Il posto unico dove tutti vedono cosa fa ogni agente è **il repository GitHub privato**
`casalimenotti-art/ai-agent-manager`, con la cartella `registro/`. La dashboard Guardian lo mostra nello spazio **Team**.

## Come funziona

```
 Amico 1 (Codex) ──push──┐
 Amico 2 (Codex) ──push──┼──► GitHub (repo privato) ──fetch ogni 5 min──► Guardian sul PC di Menotti ──► spazio Team
 Menotti (Claude) ─push──┘                                                    ▲
                                                Amici: browser via Tailscale + PIN ospiti (sola lettura)
```

- Ogni agente, a fine compito, esegue `python registro/scrivi.py --chi <id> ...`: aggiunge **una riga** a `registro/<id>.jsonl`.
  Ognuno scrive solo nel proprio file, quindi git non va mai in conflitto.
- Poi fa commit e push **sul proprio branch**. Guardian legge il registro da **tutti** i branch su GitHub, anche prima del merge.
- Lo spazio Team mostra anche gli ultimi commit di tutti i branch: se un agente si dimentica la riga, il commit si vede comunque.
- Le regole per gli agenti sono in `AGENTS.md` (Codex lo legge da solo) e `CLAUDE.md` (lo legge Claude Code).

## Passi una tantum

### Menotti (sul PC)
1. **Rinomina gli amici** in `registro/persone.json` (campo `nome`; l'`id` può restare `amico1`/`amico2` o diventare il loro nome, minuscolo e senza spazi) e nella tabella in cima ad `AGENTS.md`.
2. **Commit e push** di questo lavoro (cartella `registro/`, `AGENTS.md`, `CLAUDE.md`, dashboard). Va unito a `main` perché gli amici partano da qui.
3. **Invita gli amici sul repo:** GitHub → repo → *Settings* → *Collaborators* → *Add people* (il loro utente GitHub). Ruolo: *Write*.
   Facoltativo ma consigliato: *Settings* → *Branches* → proteggi `main` (merge solo da pull request).
4. **PIN ospiti:** doppio clic su `dashboard\telefono\imposta-pin-ospiti.bat`. È un PIN diverso dal tuo: chi entra con questo vede solo gli spazi *Team* e *Agenti*, senza chat con Guardian e senza poter lanciare agenti. Comunicalo agli amici a voce o di persona, non in chiaro su gruppi.
5. **Accesso remoto (Tailscale, già usato per il telefono):** vedi sotto.

### Ogni amico
1. Accetta l'invito GitHub.
2. In **Codex** collega il repo `casalimenotti-art/ai-agent-manager` (Codex web: *Environments* → repo GitHub; oppure Codex CLI in una cartella clonata con `git clone`).
3. Prima richiesta a Codex: «Leggi AGENTS.md. Il mio id è `amico1`. Da ora, a fine di ogni compito, scrivi la riga nel registro e fai push sul mio branch.»
4. Installa Tailscale, accetta la condivisione del PC di Menotti, apri l'indirizzo `https://…ts.net` e inserisci il PIN ospiti.

## Rendere la dashboard raggiungibile dagli amici: le opzioni

| Opzione | Chi la vede | Pro | Contro | Consiglio |
|---|---|---|---|---|
| **Tailscale + condivisione del PC** | Solo gli account Tailscale che inviti | Niente su internet, HTTPS, gratis, già pronto per il telefono | Ogni amico installa Tailscale e fa login | **Sì** |
| Cloudflare Tunnel + Cloudflare Access | Solo le email che autorizzi (codice via email) | Gli amici non installano nulla | Serve un dominio su Cloudflare, più configurazione | Se un amico non può installare Tailscale |
| Tailscale Funnel / ngrok / porta aperta sul router | **Chiunque** abbia l'indirizzo | Facile | La dashboard è su internet: resta solo il PIN a difenderla, e da lì si comanda Claude sul tuo PC | **No** |

### Tailscale: condividere solo il PC con gli amici
1. Sul PC, Tailscale deve essere installato e collegato (vedi `docs/telefono.md`, parte 1).
2. Apri https://login.tailscale.com/admin/machines → riga del PC → menu **⋯** → **Share…** → copia il link d'invito e mandalo a ciascun amico.
   La condivisione dà accesso **solo a quel PC**, non al resto della tua rete, e si revoca dallo stesso menu.
3. Ogni amico: installa Tailscale (https://tailscale.com/download), fa login con il proprio account, apre il link e accetta.
4. Sul PC: `dashboard\telefono\attiva-telefono.bat` (lo stesso del telefono) mostra l'indirizzo `https://nome-pc.….ts.net`.
5. L'amico apre quell'indirizzo e inserisce il **PIN ospiti**.

Da sapere:
- La dashboard è accesa solo quando il PC è acceso e Guardian è avviato.
- Dallo spazio *Agenti* gli amici vedono i compiti dei tuoi agenti Claude (il testo delle richieste). Non scrivere lì dati che non vuoi mostrare.
- Il PIN titolare resta tuo: chi lo conosce può usare la chat e lanciare agenti sul tuo PC con il tuo account Claude.
- Ogni persona usa **il proprio** account (Claude, ChatGPT, GitHub, Tailscale): nessuno condivide le password.

## Uso quotidiano
- Guardian fa `git fetch` da solo al massimo ogni 5 minuti quando apri lo spazio Team; il pulsante *Aggiorna da GitHub* lo fa subito.
  Il fetch non cambia i tuoi file né il tuo branch.
- Riga a mano (senza agente): `python registro/scrivi.py --chi amico1 --agente "a mano" "Visita da Bellini: interessato" --esito fatto`.
