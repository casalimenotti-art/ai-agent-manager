# Guardian HQ: il CERVELLO 3D (prompt per la Plan mode)

**Usalo così:** in Claude Code, nella cartella `C:\Users\casal\hq-worktree` (branch `claude/gallant-sagan-fwncjr`), entra in **Plan mode**, incolla questo file e presenta il piano. Dopo l'ok del titolare lavora a ondate con `/loop`, fermandoti al **95% di utilizzo settimanale**. Vale anche la regola dei PC amici di `prompts/GUARDIAN_HQ_CONTINUA.md` §4.

> **Stato al 28/11 ore 03:00.**
> - L'Atlas 2D, ondate 1 e 2 (commit 6280590), è online ma al titolare **non piace**: "fa schifo, rendilo tipo 3D".
> - L'ondata 3 (interazione) è stata interrotta a metà: nella worktree potrebbero esserci modifiche non committate a `atlas.ts` e `atlas.test.ts`. **Prima cosa da fare: `git status`, poi decidi se tenerle o scartarle** (`git checkout -- <file>`).
> - Il pannello Dispositivi / Registra PC è fatto e funziona.

## 1. Il riferimento (analizzato: `atlas-view-3.jpg` sul Desktop del titolare, NON va nel repo)
Il titolare lo vuole **proprio così come esempio**, cioè stessa atmosfera, non copia del prodotto. Cosa lo rende bello:
- **Densità**: circa 1.500 puntini e 2.200 linee. Il vuoto è poco e il "cielo" è pieno, mentre la nostra versione con 4 nodi è vuota e piatta.
- **Profondità**: alcuni puntini sono più grandi e luminosi (vicini), altri piccoli e tenui (lontani). Sembra uno spazio, non un disegno.
- **Linee**: sottilissime e quasi trasparenti (alpha 0,04-0,12), tantissime, a raggiera dal centro e tra i cluster. Dove si incrociano formano una "nebbia" luminosa.
- **Nucleo**: un disco grande e azzurro-ghiaccio fatto di **anelli concentrici di puntini** (non un cerchio pieno), con un punto bianco al centro e un alone morbido.
- **Cluster**: 6-8 gruppi, ognuno con **una tinta sua** (lilla, rosa, ciano, verde acqua, ambra, corallo). Ogni cluster ha un "fiore" di puntini al centro e dei satelliti intorno.
- **Etichette**: MAIUSCOLO, molto spaziato, piccolo, bianco al 70%, sopra il cluster, senza riquadro.
- **Fondo**: blu-notte quasi nero (#05070d → #0a0f1e), con una leggerissima vignettatura.

## 2. Come diventa il cervello di Guardian (in 3D vero, ma leggero)
- **Motore**: Canvas 2D con **proiezione prospettica fatta a mano**. Ogni nodo ha x, y, z: lo si ruota sull'asse Y, si divide per (z + d) per la prospettiva e si scalano dimensione e alpha con la profondità. **Niente dipendenze nuove.**
  Se dopo la misura degli fps il 2D non basta, proponi three.js (circa 150 KB) al titolare ✋. Non installarlo senza ok.
- **Rotazione lenta continua**: un giro ogni circa 90 secondi, così si capisce che è 3D. Trascinando con il mouse o il dito lo si ruota, con la rotellina si fa zoom. Con reduced-motion resta fermo.
- **Struttura** (dati veri e, dove i dati sono pochi, "polvere" decorativa che **non finge di essere un dato**):
  - **Nucleo Guardian** al centro: anelli di puntini su piani diversi, come un atomo. Pulsa quando il cervello risponde.
  - **3 cluster grandi**, le stanze Sviluppo (ciano), Vendite (ambra) e Amministrazione (lilla), disposti su una sfera attorno al nucleo. Più cluster piccoli per i **progetti** (`projects`), uno per azienda o cliente.
  - Gli **agenti** sono "fiori" di 30-60 puntini nel cluster della loro stanza. Quelli attivi sono luminosi e ruotano piano su se stessi, quelli fermi sono tenui.
  - I **task** e gli **eventi delle ultime 24 ore** sono satelliti dell'agente: un puntino per ogni elemento, che si accende quando l'evento arriva in diretta.
  - La **polvere neurale** è fatta di 600-1.200 puntini fermi e tenui, distribuiti nel volume, con le linee più vicine tra loro. Serve per la densità del riferimento. È decorativa e lo si dice nel riepilogo accessibile.
  - **Linee**: nucleo → stanze → agenti → task sono "nervi" più visibili. Polvere ↔ polvere sono quasi invisibili. Sulle linee degli agenti attivi scorrono **impulsi**, come sinapsi che sparano, dal nucleo verso l'agente e ritorno.
- **Etichette** come nel riferimento: maiuscolo spaziato per le stanze e per gli agenti attivi, con "cosa sta facendo" al massimo in 40 caratteri. Si vedono solo per i nodi davanti (z vicino), per non affollare.
- **Stati**: bloccato = anello ambra o rosso che lampeggia. Serve OK = puntino rosa che chiama.
- **Interazione** (dall'ondata 3 interrotta, rifatta in 3D): passaggio del mouse → tooltip; clic su agente o task → apre il pannello; clic su una stanza → la camera vola verso il cluster; Esc → vista completa. Filtri: Tutti / stanze / Solo attivi.
- **Barra del tempo** in basso: "riproduci le ultime 24 ore".

## 3. Prestazioni (il PC del titolare ha una Intel Iris integrata)
- Al massimo 30 fps, pausa con `document.hidden`, DPR fino a 1,5.
- Ordinamento per z una sola volta per fotogramma. Linee della polvere precalcolate (k vicini) e disegnate in un unico path per fascia di alpha.
- Niente `filter` o `shadowBlur` per fotogramma. Il glow si fa con sprite radiali **precalcolati** (un canvas offscreen per colore) disegnati con `drawImage`.
- Obiettivo: 1.500 nodi e 2.500 linee a 30 fps su una grafica integrata. Misuralo, e se non ci arriva riduci la polvere in automatico (qualità adattiva).

## 4. Piano a ondate (da presentare in Plan mode)
1. **Motore 3D**: proiezione, rotazione, profondità, sprite di glow, polvere, nucleo ad anelli. Test della proiezione con vitest. Misura degli fps.
2. **Dati veri**: stanze, progetti, agenti e task sulla sfera, con colori ed etichette del riferimento.
3. **Vita**: impulsi sinaptici, respiro, stati, eventi live che si accendono.
4. **Interazione 3D**: trascinamento, zoom, volo della camera, tooltip, filtri. Su telefono il tocco e una versione con meno polvere.
5. **Tempo e parete**: barra delle 24 ore e modalità parete a tutto schermo con rotazione lenta.
6. **Confronto col riferimento**: screenshot affiancati (in locale, mai nel repo) e regolazione di densità, alpha e colori. Voto del titolare.

## 5. Verifica a ogni ondata
- `npm run build` e `npx vitest run` verdi. Screenshot a 1440 e 390 px sul **sito pubblicato** https://guardian-nexo.pages.dev, dopo 1-2 minuti di build Cloudflare. Console pulita e fps misurati.
- Aggiorna `guardian-web/ROADMAP.md` e scrivi la riga di registro. Commit piccolo, poi `git fetch` + rebase + `git push origin hq-locale:claude/gallant-sagan-fwncjr`.
- Il "fatto" vale solo dopo averlo visto a schermo.
