# Tailscale per gli amici: usare la dashboard di Menotti

Tailscale crea una rete privata tra i vostri PC: la dashboard **non** va su internet, la vedono solo gli account invitati.

1. Scarica Tailscale da https://tailscale.com/download (Windows/Mac, oppure app per telefono) e installalo.
2. Apri Tailscale e fai **login con il tuo account** (Google/Microsoft/GitHub vanno bene). È gratis per uso personale.
3. Apri il **link di condivisione** che ti manda Menotti e premi *Accept*: nella tua lista dispositivi compare `jarvis-7472`.
4. Con Tailscale acceso apri **https://jarvis-7472.tailc3b182.ts.net** nel browser.
5. Inserisci il **PIN ospiti** (te lo dice Menotti a voce). Vedi gli spazi *Team* e *Agenti* in sola lettura.

Se non si apre: Tailscale è acceso (icona verde)? Il PC di Menotti è acceso con la dashboard avviata?
Per uscire basta spegnere Tailscale. Menotti può revocare la condivisione quando vuole.

## Se vuoi che anche il TUO PC entri nella rete comune (per il piano "hub")
Dopo il login, il tuo PC è nella tua rete Tailscale. Per essere raggiungibile dalla dashboard di Menotti
condividi a tua volta il tuo PC con lui (admin console → Machines → ⋯ → Share). Fallo solo quando il
"ponte" descritto in `passaggi/` è pronto e protetto da token: non aprire porte senza autenticazione.
