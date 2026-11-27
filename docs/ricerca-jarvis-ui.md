# Ricerca UI "Jarvis" / HUD per assistenti AI (rapporto del 2026-11-26)
Solo idee e pattern; nessun asset copiato. Costi prestazioni = mie stime, non misurate. Dribbble/Behance non letti: "non verificato".

## Fonti lette (URL aperti davvero)
- https://github.com/cam-hm/jarvis : reattore ad arco 3D (Three.js), "pulsa e ruota in sync con l'audio", neon viola/ciano + glassmorphism, frontend in un solo index.html, risposte in streaming frase per frase via WebSocket. MIT (file LICENSE non confermato). Voce Piper non per uso commerciale.
- https://github.com/PanPenek/JarvisAi : HUD web a file singolo (MIT) con chat, indicatore arc reactor a 4 stati, pannello esecuzione tool, feed eventi, azioni rapide, impostazioni.
- https://github.com/chevgan/react-ai-voice-visualizer : canvas + requestAnimationFrame, stati idle/listening/thinking/speaking, AnalyserNode FFT 256 (bande bassi/medi/acuti, volume RMS), smoothing con delta-time, DPR. MIT. Non documenta reduced-motion né ARIA.
- https://protolabsai.github.io/protoVoice/reference/orb-visualizer.html : macchina a stati con crossfade 600 ms, inseguitori d'inviluppo (attacco rapido, rilascio lento), isteresi e tempi minimi per evitare sfarfallio, "respiro" idle con due sinusoidi lente (~3% di scala), delta frame limitato a 1/30 s.
- https://dev.to/uianimation/building-a-smart-orb-animation-for-ai-assistants-in-rive-3off : listening = più glow e onde; thinking = rotazione costante, colore che vira, niente moto caotico; speaking = scala guidata da audioLevel; audioLevel interpolato.
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion : `reduce` va usato per sostituire (es. pulse di scala -> dissolvenza di opacità) i movimenti ampi.
- https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html : AA = 4.5:1 testo normale, 3:1 testo grande; componenti UI ~3:1 (SC 1.4.11, rinvio).
- https://docs.streamlit.io/develop/api-reference/utilities/st.html : st.html supporta CSS; JS ignorato salvo unsafe_allow_javascript=True; sanitizzato con DOMPurify; non in iframe; SVG non menzionato (non verificato). components.html non confrontato (non verificato).
Nota: il riassunto dei risultati di ricerca (non pagine lette) cita anche KofTwentyTwo/Jarvis (particelle R3F) e adewaskar/jarvis (hologram + wake word): non verificati.

## Pattern realizzabili
1. Anello/reattore SVG pulsante. Più cerchi/archi SVG concentrici (stroke-dasharray) che ruotano con CSS `transform` e pulsano con `opacity`/`scale`. Funziona: riconoscibile e leggibile, ispirato ai reattori degli HUD letti. Costo: molto basso (compositor, GPU). Reduced-motion: stop rotazione, pulse sostituito da dissolvenza lenta di opacità (esempio MDN). AA: tratti ciano su fondo scuro >=3:1 (elemento grafico); non usare il colore come unico segnale.
2. Macchina a 4 stati (idle/listening/thinking/speaking) via attributo `data-state` sul contenitore; ogni stato = variabili CSS (colore, scala, velocità, glow). Funziona: stati distinguibili per moto E colore E testo. Costo: trascurabile. Transizioni 400-600 ms. Reduced-motion: stati distinti solo da colore/forma/etichetta, senza movimento. AA: etichetta testuale >=4.5:1.
3. Transizioni dello stato stabili: isteresi, tempo minimo per stato, inviluppo attacco rapido/rilascio lento (protoVoice). In Streamlit lo stato arriva a scatti dal rerun: interpolare lato client, non scattare. Costo: nullo.
4. Respiro idle: due oscillazioni lente non sincrone, ampiezza ~3%. Costo: CSS con due animazioni a durata diversa (es. 9 s e 27 s). Reduced-motion: disattivare.
5. Reattività al parlato. Senza audio reale: livello simulato (rumore liscio) mentre `speaking`; con audio reale: AnalyserNode FFT 256, RMS -> scala (chevgan). Costo: basso (1 canvas piccolo, ~30 fps bastano). Limite Streamlit: servono iframe/components e gesto utente per AudioContext. Reduced-motion: livello mostrato come barra statica o variazione di opacità.
6. Sfondo a griglia: SVG `<pattern>` o `linear-gradient` ripetuto, con lento scorrimento via `background-position` o prospettiva statica. Costo: basso se statico, medio se grande e animato. Reduced-motion: statico. AA: linee decorative a bassa opacità, mai sotto il testo senza scrim.
7. Particelle: canvas 2D, 40-80 punti, moto browniano lento (stile "brownian/swirl" di chevgan); in `thinking` vortice lento. Costo: medio-basso; limitare DPR a 1-2, delta capped a 1/30 s (protoVoice), pausa con `document.hidden`. Reduced-motion: non avviare il canvas, disegnare un frame fisso.
8. Pannelli HUD (PanPenek): chat, pannello tool-call in corso, feed eventi, azioni rapide. Cornici con angoli tagliati (`clip-path`/bordo SVG), sfondo semitrasparente scuro (scrim) per leggibilità. Costo: basso; evitare `backdrop-filter` esteso (più pesante). AA: testo >=4.5:1 sullo sfondo reale più chiaro, non su quello nominale.
9. Tipografia: monospace/tecnica per etichette e dati (maiuscolo, tracking ampio), sans leggibile per il corpo della chat; dimensioni >=14 px; evitare testo ciano sottile sotto i 14 px. Font di sistema o un solo webfont con `font-display: swap`.
10. Suono/voce: TTS con frase per frase in streaming (cam-hm); suoni UI brevi opzionali (clic, "ascolto"), disattivati di default, con interruttore; mai audio automatico (policy browser: gesto utente). Sempre trascrizione testuale. Reduced-motion non riguarda l'audio, ma offrire muto.
11. Accessibilità dello stato: contenitore `role="status"` / `aria-live="polite"` che annuncia "In ascolto / Sto pensando / Sto parlando" (consiglio emerso da risultati di ricerca, fonte non letta); animazioni `aria-hidden`.

## Integrazione in Streamlit
- `st.html` accetta CSS e SVG inline (SVG non confermato dalla doc) ma ignora JS: bastano pattern 1-4, 6, 8 in CSS puro, con `data-state` aggiornato a ogni rerun.
- Canvas/audio (5, 7) richiedono JS: `unsafe_allow_javascript=True` in st.html (non iniettare input non fidati) oppure un componente iframe (non verificato qui).
- Reduced-motion: preferire `@media (prefers-reduced-motion: reduce)`; in JS `matchMedia('(prefers-reduced-motion: reduce)')` + listener `change` (esempio dal contesto, non dal testo MDN).
- Budget consigliato: una sola animazione di canvas, il resto transform/opacity; pausa se scheda nascosta.

## Non verificato
Dribbble/Behance, video-tutorial, prestazioni misurate, contrasto effettivo dei colori scelti (da calcolare sui token reali), supporto SVG in st.html.
