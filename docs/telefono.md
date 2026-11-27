# Guardian dal telefono — guida passo passo

Due cose diverse, tutte e due dal telefono:

| Cosa vuoi fare | Come | Voce |
|---|---|---|
| **Vedere la dashboard** (agenti, utilizzo, clienti, siti) e **parlare con Guardian** | Browser del telefono → indirizzo privato `https://…ts.net` (Tailscale) | Sì: tasto Mic, e Guardian risponde con la voce di Isabella |
| **Parlare con me** (questa sessione di Claude Code, quella che lavora sul PC) | App Claude sul telefono + **Remote Control** | Dettatura (microfono della tastiera); le risposte arrivano in tempo reale come testo |

Il PC deve restare acceso con la dashboard aperta (la sospensione con il cavo collegato è già disattivata).

---

## Parte 1 — La dashboard sul telefono (Tailscale)

**Perché Tailscale:** crea una rete privata solo tra i tuoi dispositivi. La dashboard non finisce su internet e nessun altro la vede. Serve anche l'HTTPS, senza il quale il browser del telefono blocca il microfono.

È gratis per uso personale. Il programma va installato e collegato da te, perché serve il login al tuo account.

1. **Sul PC:** scarica Tailscale da https://tailscale.com/download (Windows), installalo e fai il login (Google va bene).
2. **Sul telefono:** installa l'app ufficiale **Tailscale** (App Store / Play Store) e fai il login **con lo stesso account**.
3. **Attiva l'HTTPS (una volta sola):** apri https://login.tailscale.com/admin/dns, attiva **MagicDNS**, poi **HTTPS Certificates** → *Enable*.
4. **Scegli il PIN della dashboard (sul PC):** doppio clic su `dashboard\telefono\imposta-pin.bat`. Il PIN viene salvato solo come impronta cifrata in `dashboard\.env` (mai in chiaro, mai nel repo).
5. **Accendi il collegamento (sul PC):** doppio clic su `dashboard\telefono\attiva-telefono.bat`. Ti mostra un indirizzo tipo `https://nome-pc.tuo-tailnet.ts.net`.
6. **Sul telefono:** con Tailscale acceso, apri quell'indirizzo in Safari/Chrome, inserisci il PIN.
7. **Facoltativo:** dal menu del browser scegli *Aggiungi a schermata Home*, così Guardian si apre come un'app.
8. **Per spegnere l'accesso dal telefono:** `dashboard\telefono\disattiva-telefono.bat`.

Sicurezza:
- Dal PC (localhost) non chiede il PIN; da qualsiasi altro indirizzo sì.
- Dopo 5 tentativi sbagliati l'accesso si blocca per 5 minuti.
- Se il PIN non è impostato, l'accesso remoto resta chiuso.

## Parte 2 — Parlare con me dal telefono (Remote Control)

1. Sul PC, in questa finestra di Claude Code, scrivi `/remote-control`.
2. Sul telefono apri l'app **Claude** (lo stesso account), tocca **Code** e scegli la sessione, oppure inquadra il codice QR che compare nel terminale. Fonte: [Remote Control — Claude Code Docs](https://code.claude.com/docs/en/remote-control).
3. Scrivi o detta con il microfono della tastiera. Io lavoro sul PC e rispondo in tempo reale.
4. Le notifiche sul telefono si attivano da `/config` (le avevi spente).

## Parte 3 — Dopo: conto e soldi (quando ci sarà la SRL)

- Con il conto **aziendale** (es. Revolut Business) si può collegare una sezione **"Cassa"** alla dashboard che **legge soltanto** saldo, entrate e uscite, tramite l'API ufficiale della banca.
- La chiave di accesso resta nel `.env` del PC. La dashboard **non** potrà mai fare pagamenti o bonifici.
- Per il conto personale non c'è un collegamento ufficiale semplice: si può importare l'estratto conto CSV a mano.
- Si fa dopo l'apertura della società e del conto: è nel piano del 14/12.

## Se qualcosa non va

| Problema | Soluzione |
|---|---|
| Il telefono non apre l'indirizzo | Tailscale acceso sul telefono? PC acceso? `attiva-telefono.bat` eseguito? |
| Chiede il PIN e non lo accetta | Rifai `imposta-pin.bat` sul PC |
| Il microfono non va | Deve essere l'indirizzo `https://…ts.net`, non `http://`; consenti il microfono al browser |
| Dashboard ferma | Sul PC: `dashboard\avvia.bat` |
