# Stili HUD scuri ma accessibili - ricerca

Nota metodo: la skill ui-ux-pro-max NON e' stata eseguita (strumento Bash non disponibile). I rapporti di contrasto sono calcolati a mano con la formula WCAG (luminanza relativa sRGB), non con tool: ricontrollare con un checker prima del rilascio.

## Requisiti verificati (fonti lette)
- Testo normale >= 4.5:1; testo grande (>=18pt/24px o 14pt bold) >= 3:1; soglie rigide, niente arrotondamenti. [1]
- Il colore non deve essere l'unico segnale (WCAG 1.4.1, livello A): aggiungere testo, icona o pattern. [2]
- `prefers-reduced-motion: reduce` serve a ridurre/sostituire le animazioni (es. scala -> dissolvenza di opacita'). [3]
- Non verificato: font specifici da self-hostare (es. JetBrains Mono) e relative licenze; sotto, solo stack di sistema.

## Principi di stile
- HUD = linee sottili 1px, angoli smussati (clip-path), etichette MAIUSCOLO con letter-spacing; il glow solo su bordi/decorazioni, mai sul testo dati.
- Gerarchia: 3 livelli. (1) valore chiave grande mono 28-40px; (2) etichetta 12-13px muted maiuscola; (3) dettaglio 13-14px. Corpo min 14px.
- Densita': griglia a 8px, pannelli con padding 12-16px, max ~6-8 KPI per vista; il resto in tabelle comprimibili.
- Stati (colore + forma + testo): OK = cerchio pieno + "OK"; ATTENZIONE = triangolo + "ATTENZ."; CRITICO = ottagono/X + "CRITICO", bordo sinistro 4px tratteggiato/pieno diverso. Critico anche con `role="alert"`/aria-live, ATTENZIONE con `role="status"`.
- Animazioni: solo transform/opacity. Hover/focus 120-160ms ease-out; ingresso pannelli 240-320ms `cubic-bezier(.2,.8,.2,1)`; pulse critico 1.6s ease-in-out (opacity 1 -> .55), max 3 cicli o ferma al focus; scanline decorativa solo con transform, 8s linear. Con reduce: nessuna traslazione/pulse, solo dissolvenze brevi o niente.

## Tipografia (font di sistema, nessun download)
- Dati/etichette: `ui-monospace, "Cascadia Mono", Consolas, "SF Mono", monospace` + `font-variant-numeric: tabular-nums`.
- Testo: `system-ui, "Segoe UI", Roboto, sans-serif`. Scala: 12/14/16/20/28/40.

## Contrasti calcolati (a mano, testo su sfondo)
Variante A (bg #0B1118; pannello #121A24): testo #E6EDF3 16.0:1 (pannello 14.8); muted #8FA3B5 7.3 (6.7); accento #22D3EE 10.5 (9.7); OK #4ADE80 10.9 (10.1); WARN #FBBF24 11.4 (10.5); CRIT #FF6B6B 6.8 (6.3).
Variante B (bg #0C0A07; pannello #14110C non calcolato): testo #F2E8D5 16.3:1; muted #A39A86 7.1; accento #FFB000 10.8; OK #6EE7A0 12.8; WARN #FFD23F 13.7; CRIT #FF5C5C 6.5.
Tutti >= 4.5:1 su sfondo. Bordi/icone (UI non testuale) richiedono >= 3:1: i bordi decorativi sotto sono solo ornamento, lo stato e' nel testo/icona.

## Variante A - "Cyan Ops" (freddo, moderno)
```css
:root{
  --bg:#0B1118; --panel:#121A24; --line:#2A3A4D; --text:#E6EDF3; --muted:#8FA3B5;
  --accent:#22D3EE; --ok:#4ADE80; --warn:#FBBF24; --crit:#FF6B6B;
  --font-ui:system-ui,"Segoe UI",Roboto,sans-serif;
  --font-data:ui-monospace,"Cascadia Mono",Consolas,monospace;
  --fs-label:12px; --fs-body:14px; --fs-kpi:32px; --lh:1.45; --track-label:.08em;
  --sp:8px; --radius:2px; --cut:10px; --border:1px solid var(--line);
  --glow:0 0 0 1px color-mix(in srgb,var(--accent) 35%,transparent);
  --t-fast:140ms; --t-panel:280ms; --t-pulse:1.6s;
  --ease-out:cubic-bezier(.2,.8,.2,1); --ease-io:ease-in-out;
}
@media (prefers-reduced-motion:reduce){:root{--t-fast:1ms;--t-panel:1ms;--t-pulse:0s}}
```

## Variante B - "Amber Terminal" (caldo, retro, meno affaticante)
```css
:root{
  --bg:#0C0A07; --panel:#14110C; --line:#4A3F2A; --text:#F2E8D5; --muted:#A39A86;
  --accent:#FFB000; --ok:#6EE7A0; --warn:#FFD23F; --crit:#FF5C5C;
  --font-ui:"Segoe UI",system-ui,sans-serif;
  --font-data:ui-monospace,Consolas,"Courier New",monospace;
  --fs-label:12px; --fs-body:15px; --fs-kpi:36px; --lh:1.5; --track-label:.12em;
  --sp:8px; --radius:0; --cut:0; --border:1px solid var(--line);
  --glow:0 0 0 1px color-mix(in srgb,var(--accent) 30%,transparent);
  --t-fast:120ms; --t-panel:240ms; --t-pulse:2s;
  --ease-out:cubic-bezier(.25,.9,.3,1); --ease-io:ease-in-out;
}
@media (prefers-reduced-motion:reduce){:root{--t-fast:1ms;--t-panel:1ms;--t-pulse:0s}}
```
Attenzione in B: accento ambra e WARN giallo sono vicini; distinguerli con icona triangolo + testo (regola 1.4.1), e usare l'accento solo per cromature.

## Fonti
1. https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
2. https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html
3. https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion
