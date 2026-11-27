# Audit interfaccia dashboard (giro 11)

Metodo: web-design-guidelines su `dashboard/theme.py` (CSS, CSS_EXTRA, CSS_PLANCIA, HTML dei componenti) e `dashboard/app.py`.

## Problemi trovati e corretti
1. Tabelle (`.g-wrap`) e feed (`.g-feed`) scorrevoli non raggiungibili da tastiera. Ora hanno `tabindex=0`, `role=region` e `aria-label`, più un anello di focus rosa.
2. `transition:all` sui pulsanti del vecchio CSS. Ora elenca le proprietà.
3. Regola `td.msg` in conflitto: l'ellipsis nowrap del vecchio CSS contro il wrap del nuovo. Resta solo il wrap, con `overflow-wrap:anywhere`, così il testo non viene più tagliato.
4. Blocco duplicato della barra di navigazione in CSS_EXTRA (radius 0, colori fissi), sempre sovrascritto dal liquid glass. Rimosso, restano solo le dimensioni del testo.
5. Doppioni di pulsanti e focus in CSS_PLANCIA (regola `button:focus-visible` globale ripetuta, blocco `.stButton` superato dal vetro). Ridotti alla sola altezza minima di 40px.
6. Testi sotto i 10px (`.58rem` e `.6rem`) su tag e stato. Portati a `.64rem` e `.66rem`.
7. Mancavano `color-scheme:dark` (scrollbar e controlli nativi) e il colore dei placeholder, che ora usa `--p-mute`.
8. Con `prefers-reduced-motion` restavano gli spostamenti in hover sulla barra degli spazi e `:active` sui pulsanti. Ora sono disattivati.
9. (giro 12) `--p-r` unificato: `--r-sm/md/lg` e `--p-r:var(--r-md)` ora sono definiti una sola volta nel primo `:root`.
10. (giro 12) Potate le regole morte con classi non più emesse: `.g-bar .r/.pista/.riempi` (CSS_EXTRA e liquid glass) e `.g-ev a`. Le altre regole di `.g-tile`, `.g-agente`, `.g-feed` sono vive: le classi sono usate.
11. (giro 12) Fallback `@media (forced-colors: active)` per h1, h2 e h3 con gradiente: colore `CanvasText`.

## Cosa resta
- Il colore del testo `.g-ev .tag` (giallo, arancio) non è verificato con un misuratore di contrasto.
- Le icone SVG non hanno `title`, ma sono decorative (`aria-hidden`), quindi va bene.
- Manca un link "salta al contenuto": Streamlit non lo offre e servirebbe JS.

## Verifica
- pytest: 7 fallimenti noti (chat e skill, ambiente Python 3.15 e WinError). Gli altri 160 test passano.
- AppTest: 0 eccezioni su tutti i 7 spazi.
- `python -m graphify update .` eseguito.

## Audit 26/11 sera
Ambito: sidebar Catalogo, pop-up agenti/skill/conversazioni, galleria Siti demo, tabella "Chi lavora", feed, scheda agente.
- Contrasto: calcolato su #0e1420. Tutti i grigi di testo passano AA (min 6.3:1 con #8b97b3; #8FA3B5 7.1; tag giallo/rosa/ciano/arancio 7.6-15). Nessuna modifica.
- Focus: già coperto da `:focus-visible` globale e dalle regole di sidebar, X del pop-up, feed, tabelle e spazi. Nessuna modifica.
- Stati OK/FINITO/AL LAVORO: hanno sempre il testo oltre al colore e al puntino. Nessuna modifica.
- Target: sidebar 38px, X pop-up 36px, bottoni 40px (oltre i 24x24). Nessuna modifica.
- Movimento: pulsazione, feed nuovo, ingresso sezioni e pioggia hanno già `prefers-reduced-motion`. Nessuna modifica.
- Corretto: titoli "Catalogo", "Agenti", "Skill" della sidebar erano div senza semantica; ora `role=heading` (livelli 2 e 3), con ordine coerente.
- Corretto: intestazioni della tabella "Chi lavora" senza `scope='col'`; aggiunto.
- Corretto: i bottoni "Anteprima" della galleria Siti demo erano tutti uguali per un lettore di schermo; ora hanno `help` con il nome del cliente.
- Testi troncati: chip strumento, righe di tabella, feed e voci di sidebar hanno già `title`/`help`.
