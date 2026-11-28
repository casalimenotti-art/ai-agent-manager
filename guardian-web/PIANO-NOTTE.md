# Piano "dashboard da paura" (prompt prompts/CLAUDE_NOTTE_DASHBOARD_DA_PAURA.md)

Stato al 28/11 mattina (eseguito da Claude su richiesta del titolare, settimana all'89%).

| Fase | Stato | Note |
|---|---|---|
| A. Cervello 3D | ✅ base fatta | `logic/atlas.ts` (conProfondita, proietta, polvere, angoloAuto) + `ui/Atlas.tsx`: rotazione 90 s/giro, prospettiva, nodi ordinati per z, sprite di luce precalcolati, polvere 900 (360 su telefono, dimezzata se < 22 fps), trascina = ruota, rotellina = zoom, Esc = vista completa. 30 fps misurati in locale (1440 e 390 px). |
| B. Tendine nascoste | 🟡 iniziata | Numeri del Centro in una tendina chiusa all'avvio (`guardian.pref.numeriAperti`). Da fare: barra laterale a icone che si allarga, pannelli a cassetto chiusi, riquadri stanze compatti. |
| C. Statistiche | ⏳ | Pagina Statistiche esistente da arricchire con §4 (dati veri, SVG a mano). |
| D. Vita | ⏳ | Cervello che reagisce alla voce (oggi solo `pensa`). |
| E. 3D avanzato, telefono, parete | 🟡 | Volo verso la stanza già c'è (2D zoom sul cluster); manca tocco a due dita e parete con rotazione. |
| F. Rifinitura | ⏳ | |

Verifica locale: `VITE_DEMO=1` in `guardian-web/.env.local` (ignorato da git), `npx vite --port 5179`, accesso con «menotti».
