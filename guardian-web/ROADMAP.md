# Guardian HQ — roadmap a ondate

Memoria del ciclo continuo descritto in `prompts/GUARDIAN_HQ_MASTER_V3.md`. Ogni sessione aggiorna questo file.

| Ondata | Contenuto | Stato | Note / decisioni del titolare |
|---|---|---|---|
| 0 | Allineamento: inventario dei branch, passaggio di amico1, PR #2 | 🟡 in parte | Inventario fatto (27/11 sera). **Da decidere (titolare):** (a) cosa fare della PR #2 di Niko, cioè busto WebGL + plancia team: unirla o tenerla sul PC; (b) dare a Francesco (`salisfrancesco19-stack`) l'accesso al repo su GitHub, come chiede il passaggio `passaggi/20261127T1641-amico1.md` |
| 1 | **Tre stanze**: migrazione 005 `stanze` + `projects.stanza_id`, vista orbita, stanza espansa con nucleo compatto, kanban vero (trascina o "Sposta in…"), comandi "apri vendite"/"torna al centro", contesto della stanza in chat, palette, colori Accesa/Soft | ✅ fatto | Colori: **Accesa** (dal DB, predefinita) o **Soft** in Impostazioni; nomi dal DB (l'admin li cambia). E2E verdi, 4 larghezze |
| 2 | Conversazione vocale livello B (browser): modalità conversazione, VAD, frase per frase, barge-in, sottotitoli, comandi vocali, diagnostica | ⏭ prossima | Scelta della voce preferita |
| 3 | Voce livello A: servizio vocale locale del bridge (sherpa-onnx + Parakeet già sul PC) | da fare | Ok a far girare il servizio sul PC |
| 4 | Cervello sul PC (`guardian_richieste` / `guardian_risposte`, `claude -p` in sola risposta) | da fare | Ok all'uso dell'abbonamento Claude Code |
| 5 | Stanza Vendite completa (pipeline senza dati personali, bozze con approvazione) | da fare | Migrazione `vendite_pipeline` |
| 6 | Smistamento del lavoro alle IA dalla conversazione | da fare | Modello di minaccia |
| 7 | Stanza Amministrazione (scadenze, documenti, costi manuali, calendario) | da fare | Migrazione `costi`, connettore Calendar |
| 8 | Mappa operativa, Realtime incrementale, aggiornamenti ottimistici, presence | da fare | — |
| 9 | 3D e suoni (nucleo 3D o busto di Niko), modalità parete | da fare | Scelta del look 3D |
| 10 | PWA, notifiche push, briefing vocale del mattino | da fare | Ok alle notifiche |

## Idee (massimo 3 per sessione, concrete)
- Kanban: aggiornamento **ottimistico**. La scheda si sposta subito e torna indietro se il DB rifiuta; oggi aspetta la risposta.
- Stanza: filtro "solo miei" e ordinamento per priorità dentro le colonne.
- Nucleo compatto: piccolo indicatore di quanti agenti sono al lavoro **in quella stanza**, oltre al totale.

## Registro delle ondate
- **27/11 · Ondata 1**:
  - file: `supabase/migrations/005_stanze.sql`, `tests/pg/check_005.sql`, `guardian-web/src/logic/stanze.ts`,
    `guardian-web/src/ui/Stanze.tsx`, più modifiche a state, CommandCenter, Shell, intents, impostazioni e CSS;
  - test: vitest 7, E2E tutti verdi (16 nuovi controlli sulle stanze), `tests/pg/run.sh` CHECK 002–005 OK;
  - bundle: 79 KB gzip.
