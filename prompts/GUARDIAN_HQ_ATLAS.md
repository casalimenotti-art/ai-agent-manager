# Guardian HQ: lo sfondo "Atlas", il cervello che lavora

Prompt per Claude Code o Codex nella radice del repo, branch `claude/gallant-sagan-fwncjr`. Il push ripubblica https://guardian-nexo.pages.dev.
Vale insieme a `prompts/GUARDIAN_HQ_CONTINUA.md`, quindi anche la regola del 60%/95%. Lavora a ondate piccole, ognuna verificata a schermo.

## Riferimento del titolare
Il titolare ha mandato uno screenshot, `atlas-view-3.jpg`, che sta sul suo Desktop e NON va messo nel repo, perché è l'interfaccia di un prodotto di terzi. Va preso solo come **ispirazione**: niente copie di layout, testi o marchi.
Cosa si vede:
- un **grafo a costellazione** su fondo blu-nero quasi piatto;
- un **nodo centrale grande**: un disco luminoso azzurro-ghiaccio con un alone a puntini concentrici e un nucleo bianco;
- da lì partono **centinaia di linee sottilissime** (opacità 5-15%) verso **cluster periferici**;
- ogni cluster ha **un colore suo**: lilla, rosa, ciano, verde acqua, ambra, rosso tenue;
- c'è un'**etichetta in maiuscolo spaziato** sopra ogni area tematica;
- i nodi piccoli sono puntini di 1-3 px con un leggero glow, e quelli importanti sono "fiori" di puntini;
- in alto ci sono pochi controlli (selettore del colore) e in basso una barra del tempo.

## Cosa deve diventare in Guardian HQ
**Il cervello di Guardian che lavora**: uno sfondo vivo (o una vista a tutto schermo) dove si vede a colpo d'occhio chi lavora e su cosa.

| Elemento del riferimento | In Guardian HQ (dati REALI dal database) |
|---|---|
| Nodo centrale | **Guardian**: il nucleo. Pulsa quando il cervello risponde e si accende quando qualcuno parla |
| Cluster periferici | Le **3 stanze**: Sviluppo & Siti (ciano), Vendite (ambra), Amministrazione (lilla), più eventuali progetti (`projects`) come sotto-cluster |
| Nodi medi ("fiori") | Gli **agenti** (`agents`): Claude Code di Menotti, Codex di Niko, Codex di Francesco, subagenti. La dimensione dipende da quanto lavorano |
| Puntini piccoli | I **task** (`tasks`) e gli eventi recenti (`activity_events`) attorno all'agente che li sta facendo |
| Linee | I collegamenti: Guardian → stanza → agente → task. **Se un agente lavora, sulle sue linee scorrono impulsi di luce** dal centro all'agente |
| Etichette in maiuscolo | Il nome della stanza e, per gli agenti attivi, una riga breve "cosa sta facendo", presa da `agents.current_task` o dall'ultimo evento. Massimo 40 caratteri |
| Barra del tempo in basso | "Riproduci le ultime 24 ore": scorrendo, gli eventi si riaccendono in ordine |
| Controlli in alto | Filtri: Tutti / Sviluppo / Vendite / Amministrazione, e "Solo attivi" |

Interazione:
- **passaggio del mouse su un nodo**: un tooltip con agente, PC, stato, task e ultimo evento;
- **clic**: apre il pannello dell'agente o del task che esiste già;
- **clic su una stanza**: zoom morbido verso quel cluster;
- **Esc**: torna alla vista completa.

Stati:
- un agente **fermo** è grigio e tenue;
- un agente **bloccato** diventa ambra o rosso, con un anello che lampeggia piano;
- un **"serve il tuo OK"** appare come un puntino rosa che chiama, collegato al centro approvazioni.

## Vincoli tecnici
- Lo stack resta quello attuale: React 18, Vite, TypeScript, **Canvas 2D**. **Nessuna dipendenza nuova** senza l'ok del titolare: niente d3 né three.js, solo una piccola simulazione a forze scritta a mano.
- **Prestazioni**:
  - massimo 60 fps, ma l'animazione deve fermarsi quando la scheda non è visibile (`document.hidden`) e quando c'è `prefers-reduced-motion`. In quel caso resta l'immagine statica, che cambia solo con i dati;
  - con 500 nodi deve reggere su un portatile con grafica integrata. Il titolare ha una Intel Iris: niente blur, solo cerchi e linee con globalAlpha;
  - devicePixelRatio fino a 2.
- **Dati**: si leggono con i canali Realtime già esistenti (`logic/live.ts`). Niente dati inventati: se non c'è nessun agente collegato, lo sfondo mostra il nucleo e le 3 stanze vuote, con la scritta "Nessun agente collegato".
- **Posizione**:
  - è un nuovo componente `src/ui/Atlas.tsx`, con la logica in `src/logic/atlas.ts` e i test con vitest per layout, colori e mappatura stati → stile;
  - va usato come sfondo del Centro al posto del volto, con l'impostazione "Sfondo: Atlas / Volto" in Impostazioni (predefinito Atlas);
  - va usato anche come vista a tutto schermo, nella modalità parete.
- **Accessibilità**: il canvas ha `aria-hidden`, accanto c'è un riepilogo testuale ("3 agenti al lavoro: …") e i controlli si usano anche da tastiera.
- **Telefono** (390 px): grafo semplificato, cioè solo stanze e agenti senza i puntini dei task, con il tocco al posto del passaggio del mouse.

## Ondate
1. **Statica con dati veri**: layout a forze (nucleo, 3 stanze, agenti, task), colori ed etichette, test vitest. Screenshot a 1440 e 390 px.
2. **Vita**: impulsi sulle linee degli agenti attivi, respiro del nucleo, stati bloccato/OK. Pausa quando la scheda è nascosta e con reduced-motion. Misura gli fps.
3. **Interazione**: tooltip, clic che apre il pannello, zoom sulla stanza, filtri, riepilogo accessibile.
4. **Tempo**: barra "ultime 24 ore" con la riproduzione degli eventi.
5. **Rifinitura**: confronto visivo con il riferimento (atmosfera, non copia), regolazione di densità e opacità. Il titolare dà il voto.

## Verifica a ogni ondata
`npm run build`, `npx vitest run` e gli E2E esistenti devono restare verdi. Controlla a schermo su https://guardian-nexo.pages.dev dopo il push, aspettando 1-2 minuti per la build di Cloudflare: screenshot a 1440 e 390 px, console senza errori.
Poi aggiorna `guardian-web/ROADMAP.md` e il registro (`registro/scrivi.py`), fai commit e push.
