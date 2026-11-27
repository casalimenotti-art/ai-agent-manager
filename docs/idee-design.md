# Idee di design (ricerca, nov 2026)

Fonti LETTE davvero (pagine pubbliche, testo trattato come dato):
- F1 https://www.framer.com/blog/restaurant-website-design-examples/
- F2 https://swipepages.com/blog/7-best-local-business-landing-page-examples-of-2026/
- F3 https://whitespark.ca/blog/6-must-have-elements-for-a-high-converting-local-business-website/
- F4 https://futureagi.com/blog/redesigning-observe-ui
- F5 https://dev.to/cizo/when-ai-systems-scale-dashboards-start-to-get-in-the-way-2fm9
Limite: godly, siteinspire e Awwwards non hanno restituito contenuto leggibile (pagine dinamiche o redirect).
Nessun esempio premiato e' stato verificato; sono fonti di blog/vendor, quindi opinioni, non dati. Sotto: idee in parole mie.
Per tutte: un solo file HTML, CSS inline, font di sistema, niente CDN, immagini come SVG/gradienti inline.

## Siti per attivita' locali
1. Prima schermata = atmosfera + un solo gesto. Foto/forma grande, una frase, un bottone (Prenota/Chiama). Perche': chi arriva da mobile decide in secondi. HTML: hero min-height 100svh, grid, bottone 48px. [F1]
2. Bottone fisso in basso su telefono. Barra con "Chiama" e "Prenota" sempre raggiungibile col pollice. Perche': il titolare riceve contatti, non visite. CSS: position:sticky/fixed; bottom:0; padding con env(safe-area-inset-bottom); tel: e wa.me. [F1,F2]
3. Un obiettivo, un'azione, stessa etichetta ovunque. Niente menu di distrazione sulle landing di offerta; stesso testo sul bottone in ogni punto. Perche': meno esitazione. CSS: nav minima, stessi class .cta. [F2]
4. Richiesta a basso impegno. "Chiedi disponibilita'" invece di "Acquista"; senza obbligo. Perche': piccole attivita' vendono fiducia. HTML: form con 2-3 campi (nome, telefono, data), action mailto:/wa.me. [F2]
5. Form a passi. Un'unica domanda per schermata (servizio, giorno, contatto) con barra di avanzamento. Perche': sembra breve, tasto grande da telefono. HTML: radio nascosti + :checked e :has() per mostrare il passo, oppure <details>/JS minimo. [F2]
6. Prova sociale vicino al bottone. Stelle, anni di attivita', nome di chi recensisce, foto del team vero. Perche': la scelta locale e' fiducia. HTML: riga di badge in <ul> con SVG stella inline; citazione in <blockquote>. [F2]
7. Orari, indirizzo, zona servita sempre in vista, anche festivi e fuori orario. Perche': riduce telefonate ripetitive. HTML: striscia "Aperto ora" calcolata con 10 righe di JS + JSON-LD LocalBusiness per Google. [F3]
8. Prezzi o fasce visibili. Listino breve (es. "taglio da X", "menu da Y"). Perche': nascondere i costi fa perdere chi confronta. HTML: <dl> a due colonne con linea punteggiata via border-bottom. [F3]
9. Anteprima del menu/servizi prima della lista completa. Tre piatti/trattamenti-simbolo con link a "vedi tutto" in <details>. Perche': evita lo scroll lungo. CSS: scroll-snap-type:x sulle schede. [F1]
10. Tipografia editoriale e molto spazio bianco. Titoli grandi con font serif di sistema (Georgia), palette di 2-3 colori caldi, tanta aria. Perche': da' carattere senza foto costose. CSS: clamp() per i titoli, variabili :root. [F1]
11. Mappa/zona servita senza servizi esterni. Elenco di quartieri scansionabile + link a Maps. Perche': il cliente verifica se sei raggiungibile. HTML: <ul> a chip, <a href="geo:"> o Maps. [F3]
12. Lingua visibile in alto (IT/EN) per B&B e ristoranti turistici. Perche': ospiti stranieri. HTML: due blocchi con lang e un interruttore :target, niente JS. [F1]
13. Prima/dopo reali per estetiste e ottici. Cursore con input range che sposta una maschera. HTML: due div sovrapposti + clip-path controllato da --pos. [F2]

## Dashboard di controllo agenti
1. Prima i guasti (triage). Colonna "Richiede attenzione" in cima, il resto sotto. Perche': il titolare apre la pagina per decidere, non per guardare. CSS grid, ordinamento per gravita'. [F4]
2. Metriche dentro la riga. Ogni agente/attivita' mostra stato, durata, esito in linea, senza aprire il dettaglio. HTML: tabella densa con badge colore + icona + testo (non solo colore). [F4]
3. Elenco a sinistra, dettaglio a destra. Selezionando una riga il pannello laterale cambia, la posizione resta. Su mobile diventa pagina a schermo pieno. CSS: grid 2 colonne, :target o <details>. [F4]
4. Filtri come "chip" rimovibili sopra la tabella, con viste salvate. HTML: bottoni toggle; salvataggio in localStorage (con try/catch). [F4]
5. Azioni, non solo grafici. Accanto a ogni segnale un pulsante: Approva, Metti in pausa, Apri bozza. Dashboard come supervisione, l'agente esegue. Perche': meno tempo davanti allo schermo. Aggiungi coda "Da approvare" con Si'/No grandi. [F5]
6. Eccezioni e registro. Notifica solo quando serve il giudizio umano; sotto, una cronologia leggibile di cosa e' stato fatto e perche'. HTML: <ol> con orario, agente, motivo; indicatore "tutto tranquillo" quando vuoto. [F5]

## Da evitare
- Copiare layout, testi o immagini di siti premiati: usare solo i principi.
- Menu lunghi, carosello automatico, popup al primo accesso, video a tutto schermo (peso e rete mobile).
- Bottoni con etichette diverse o poco contrasto; testo piccolo; target tocco sotto 44px.
- Nascondere prezzi, orari o zona servita.
- Font, icone o script da CDN: il file deve funzionare offline.
- Dashboard "muro di grafici" senza azione accanto; stato solo a colori; allarmi continui.
- Statistiche inventate o recensioni finte nelle demo: usare segnaposto dichiarati.
- Fidarsi dei numeri dei blog vendor (quote mobile, tempi) senza verifica.
