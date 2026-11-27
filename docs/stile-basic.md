# Guardian: stile "cyberpunk basic" (proposta, theme.py NON modificato)

Il CSS e' a strati sovrapposti: CSS (r.17), CSS_EXTRA (r.372), CSS_PLANCIA (r.548). Gli strati piu' recenti
(Cyan Ops r.629, Liquid glass r.733+) ridefiniscono quelli vecchi con `!important`: molte regole sono codice morto.

## 1. Diagnosi
- **backdrop-filter**: `blur(22px) saturate(170%)` su card, tessere, agenti, feed, form, expander, chat, bottoni
  (r.744, 792, 803, 808, 815, 878, 899), piu' `blur(14px)` (r.558) e `blur(10px)` (r.583). Decine di layer da
  ricomporre a ogni refresh: e' la voce piu' costosa, soprattutto sul telefono.
- **Animazioni continue**: particelle `.stApp::after` con `g-sale` 60s infinite + `will-change` (r.639-643);
  `g-pulsa` (r.604) e `g-pulse` (r.151) infinite; `rx-*` (r.682-685); entrata sezioni con `filter:blur(3px)` (r.377).
- **Pioggia di caratteri**: segnaposto `/*PIOGGIA*/` (r.738), iniettata a parte: canvas/JS a tutta pagina.
- **Ombre multiple**: `--sh` a 2 strati + inset x2 + glow neon su hover (r.737, 746, 750) e `text-shadow` sul logo (r.51).
- **Sfondo**: 2 radial + griglia + vignetta + scanline (r.26-36, 635-642, 739): 4-6 gradienti fissi.
- **Look**: gradiente su titoli (r.833), ciano + magenta + giallo + arancio insieme, tutto in monospace
  (r.25, 40): illeggibile nei testi lunghi. Nessun font esterno (bene).

## 2. Stile "basic"
Sfondo scuro piatto; un solo accento ciano; rosa solo per azione primaria e utente in chat; bordi 1px;
raggio 12px; zero backdrop-filter, zero blur; 1 sola animazione (pallino "al lavoro", 2s, opacita');
titoli e testi in Inter (stack di sistema se assente: nessun download), monospace solo per numeri/codice;
spazio piu' generoso (gap .9-1.2rem, padding card 1.1rem); tutto il testo >= 4.5:1.

## 3. Token (sostituiscono tutti i :root precedenti)
```css
:root{
 --bg:#0B1118; --surface:#121A24; --surface2:#17212D; --line:#2A3A4D;
 --ink:#E6EDF3; --ink2:#C3CFDA; --mute:#8FA3B5;      /* su --bg: 15.5 / 12 / 6.9 */
 --acc:#22D3EE; --acc-ink:#06222A;                    /* testo su bottone ciano 10:1 */
 --pink:#F472B6;                                      /* 7.9:1, solo primario/utente */
 --ok:#4ADE80; --warn:#FBBF24; --crit:#FF6B6B;
 --r:12px; --bd:1px solid var(--line); --gap:1rem; --pad:1.1rem;
 --sans:Inter,"Space Grotesk",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
 --mono:ui-monospace,"Cascadia Code",Consolas,Menlo,monospace;
}
```
Alias per non rompere le regole vecchie: `--p-bg:var(--bg); --p-acc:var(--acc); --p-line:var(--line);
--p-line2:var(--line); --p-ink:var(--ink); --p-ink2:var(--ink2); --p-mute:var(--mute); --cy:var(--acc);
--cy2:var(--acc); --mg:var(--pink); --pk:var(--pink); --pk2:var(--pink); --p-r:var(--r); --r-sm:8px; --r-md:var(--r); --r-lg:var(--r)`.

## 4. Modifiche a theme.py (in ordine)
1. **Togliere** il blocco "Liquid glass" (r.733-752, 788-793, 803-815, 878-899): ogni `backdrop-filter`,
   `-webkit-backdrop-filter`, `--glass*`, `--blur`, `--sh*`, `--glass-hi`. Dove serve fondo, usare `background:var(--surface)`.
2. **Togliere** la pioggia (segnaposto `/*PIOGGIA*/` e il codice Python che la inietta), `.stApp::after` (r.35, 639-643) con
   `g-sale`, `.stApp::before` vignetta+griglia (r.635), `g-boot` (r.148-149), `rx-*` (r.682-685) se non usati da widget vivi.
3. **Semplificare lo sfondo**: `.stApp{background:var(--bg) !important}` e basta (r.26-34, 739).
4. **Unica regola superficie** al posto di r.741-747:
   `.g-card,.g-tile,.g-wrap,.g-agente,.g-feed,[data-testid="stForm"],[data-testid="stExpander"],[class*="st-key-plancia_guardian"],[class*="st-key-plancia_utilizzo"],[data-testid="stChatMessage"],div[role="dialog"]{background:var(--surface) !important;border:var(--bd) !important;border-radius:var(--r) !important;box-shadow:none !important}`.
   Dentro `[data-baseweb="popover"] > div` solo bordo e fondo, senza blur.
5. **Hover** (r.750, 389, 785): `transform:none; border-color:var(--acc)`; niente glow, niente rosa. Transizione solo `border-color .15s`.
6. **Cornici d'angolo** `.g-card::before/::after`, `.g-tile::before` (r.72-74, 388): gia' nascoste, cancellare le regole.
7. **Testo**: `html,body,.stApp,h1,h2,h3,h4,p,span,label,div{font-family:var(--sans)}`; `--mono` solo su `.g-value,.g-tile .v,.num,code,.ora,.g-bar .v,.g-table td.num`. Togliere `h3::before "// "` (r.43), `text-shadow` (r.51, 64, 77), gradiente titoli (r.833); titoli maiuscoli con `letter-spacing:.08em` (non .18-.32em).
8. **Bottoni/campi** (r.103-122, 710-717, 848-859): `border-radius:var(--r)` (pillole 999px -> 12px), bordo `var(--bd)`, hover `border-color:var(--acc)`. Primario (`button[kind="primary"]`, `primaryFormSubmit`): fondo `var(--acc)`, testo `var(--acc-ink)`, niente rosa pieno. Focus: `:focus-visible{outline:2px solid var(--acc);outline-offset:2px}` (gia' presente).
9. **Segmented bar** `[data-testid="stButtonGroup"]` (r.583): togliere blur, fondo `var(--bg)` opaco, tenere `position:sticky`.
10. **Animazioni**: lasciare solo `g-pulsa`/`g-pulse` sul pallino `.g-dot`; l'entrata `g-entra` (r.376-378) diventa solo `opacity` .2s oppure si toglie. Tenere i blocchi `prefers-reduced-motion`.
11. **Chat**: bolle `border-radius:var(--r)`; assistente bordo sinistro `var(--acc)`, utente `var(--pink)`; sfondo `var(--surface2)`. Selettori esistenti `[class*="st-key-chat_storico"] [data-testid="stChatMessage"]` (r.865-871).
12. **Colori dati**: tag (r.401-403) ridotti a 3: ciano, `--mute`, `--warn`; il magenta/giallo `#fcee0a` va via. Grafici Altair (SERIE_TOT/SERIE_CLAUDE) invariati.
13. **Spazio**: `.block-container{padding-top:2rem}`, `[data-testid="stHorizontalBlock"]{gap:var(--gap)}`, `.g-card{margin-bottom:var(--gap);padding:var(--pad)}`.
14. **Bottoni con help**: sono avvolti da `stTooltipHoverTarget`, quindi usare selettori discendenti
    `[class*="st-key-X"] button` (la classe `st-key-<key>` in 1.67 sta sul blocco stesso), mai `> button` o `.st-key-X > .stButton`.

## 5. NON toccare (risolvono bug)
- Altezze card: r.82, 387, 593, 617, 648-657, 768-775, 784-786 (`height:100%`, `flex`, `:has()` su `st-key-skc_/scp_/agc_`, `min-height` delle tessere).
- `[data-testid="stHeader"]{pointer-events:none}` (r.646) e il ripristino `stHeader button,a,[role=button]{pointer-events:auto}` (r.663).
- Chat `column-reverse` (r.861-868): regola su `[class*="st-key-chat_storico"][data-testid="stVerticalBlock"]`, `flex-shrink:0`, `pre-wrap`.
- Layout mobile (r.617-624, 661, 905-906), `.g-wrap` `overflow-x:auto`, `[class*="st-key-sez_"]{min-height:62vh}` (r.591).
- Regole "fix: sfondi widget" (r.126-137): cambiare solo i colori con i token, non i selettori.

Verifica da fare dopo l'applicazione: riavvio, screenshot desktop e telefono, chat con messaggi lunghi, dialog, popover.
