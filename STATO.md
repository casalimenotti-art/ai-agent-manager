# STATO — Operazione 30 clienti (2026-11-26)

## Divisione del lavoro (decisa dal titolare, 2026-11-26)
- **Claude (Claude Code, account Pro del titolare): siti, test e software.** Siti demo e siti dei clienti, dashboard Guardian, test, software su misura, chatbot. Branch: claude/quirky-ritchie-u85igr.
- **Codex (account Pro del socio): vendite.** Lettura di leads/ e visite/, bozze di contatto (solo bozze, le invia un socio), preventivi, esiti.csv dopo le visite. Lavora su un proprio branch (es. codex/vendite) e apre pull request: nessuno dei due modifica i file dell'altro senza PR.
- File condivisi: leads/2026-11-26-30-clienti.csv (fonte unica dei clienti), visite/*.md, esiti.csv. Ognuno usa il proprio account.

## Fatto
- Squadra installata in ~/.claude/agents (13 agenti), profilo azienda salvato in ~/.claude/guardian/azienda.md
- Guardian avviato con avvia.bat su http://localhost:8501 (0 eccezioni)

- 8 cacciatori-clienti completati: 78 righe in 8 CSV (adattamento 4: 20, 3: 22, 2: 28, 1: 8) -> 42 lead con fit >= 3, nessuno ancora verificato da un secondo agente
- Dashboard: feed Agenti con nome e compito dei subagenti, stato FINITO, promemoria interni nascosti, nessun link che apre altre schede (+3 test)

- leads/2026-11-26-30-clienti.csv: 30 lead (top fit) con indirizzo/telefono/email pubblicati; 3 verificatori su tutti e 30 -> 29 confermati, 1 smentito (n20 Sun & Sardinia, fit 2). Grezzi e verifiche in leads/grezzi/
- siti-demo/: 30 siti demo (bozze, dati reali solo nella prova; orari/foto/prezzi "da inserire")

- n20 sostituito: Gisella B&B (Selargius) confermato -> 30/30 lead confermati
- 10 siti personalizzati (Terra e Mari, Libarium, Dar Mammozzaro, Il Cagliarese, Bellini, Borriello, Bernardi, Ungari, Estetica Maxia, Black and White); poi anche gli altri 20: 30/30 siti personalizzati (5 versioni migliorate di siti esistenti); controllo automatico OK su tutti (footer, nessuna risorsa esterna, modulo demo, WhatsApp solo se pubblicato)
- visite/: 30 schede di visita + GIRO.md per zona
- Dashboard: Siti demo mostra la versione salvata/personalizzata; "Salva i mancanti" non sovrascrive

## Dashboard Guardian (aggiornato 26/11 sera)
- Plancia unica: Guardian in alto (chat salvata in ~/.claude/guardian/conversazioni, microfono, voce Isabella/Elsa, comandi vocali), utilizzo reale 5 ore/settimana a destra, spazi sotto (Agenti con riga OGGI, Skill, Squadra, Store, Clienti, Siti demo con galleria, Scoperte), Catalogo agenti/skill a sinistra con pop-up, Guida rapida.
- Telefono: pronto con Tailscale + PIN (guida docs/telefono.md); per parlare con Claude Code dal telefono: /remote-control + app Claude.
- Voce: FUNZIONA offline con sherpa-onnx + Parakeet v3 (non serve più Python 3.12).
- Statusline/usage: approvata e attiva dal 26/11.
- Test: 222 passati, 0 falliti, 1 saltato (symlink senza privilegi su Windows). Verificata con più schede aperte insieme e alla larghezza di un telefono.
- Dettagli giro per giro: CONTINUA.md.

## Team condiviso (27/11 notte)
- registro/ (persone.json, scrivi.py, un .jsonl per persona) + AGENTS.md (Codex) + CLAUDE.md: ogni agente scrive una riga a fine compito e fa push sul suo branch.
- Dashboard: spazio Team (legge il registro da tutti i branch, anche origin/*, e i commit degli ultimi 7 giorni; fetch automatico max ogni 5 min).
- PIN ospiti (dashboard\telefono\imposta-pin-ospiti.bat): gli amici vedono solo Team e Agenti, niente chat/lanci. Guida: docs/team-condiviso.md.
- Test: 238 passati, 1 saltato.
- Da fare dal titolare: nomi degli amici in persone.json, commit/push, invito collaboratori GitHub, PIN ospiti, condivisione Tailscale del PC.

## In corso
- (niente) - in attesa di revisione dei soci

## In coda
- Commit (manca identità git: chiedere nome/email al titolare)
- Decidere con il titolare: lanci dalla dashboard con permission-mode acceptEdits? (oggi default)
- Coda del titolare in CONTINUA.md (collegamento colleghi 27/11 00:30, Smashtag, bozze PR discoteca, social/email)

## Bloccato
- (niente)
