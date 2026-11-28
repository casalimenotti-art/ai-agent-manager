# Design di Guardian HQ

## Visione
Guardian è un centro di comando personale immerso nello spazio profondo: fondo quasi nero, cervello vivo al centro, tre computer collegati e agenti visibili mentre lavorano. La scena è cinematica, scientifica e sobria; niente griglie, card SaaS o neon invadente. Una sola intelligenza, tre macchine, più agenti.

## Palette e controlli
Fondo `#000000` (massimo `#02030A`), luce stellare `#F2F6FF`; tinte stanza quasi bianche: Sviluppo `#CDEFFF`, Vendite `#FFE7C2`, Amministrazione `#E4DCFF`. In attesa `#FFD9A0`, errore `#FFB4A8`, offline `#8A93A6` al 35%. Percorsi `#DCEBFF`, particelle `#9FE8F5`. Mai comunicare stati solo col colore.

I pulsanti secondari sono pillole chiare e discrete (`rgba(242,246,255,.04)`, bordo bianco al 22%, testo `#F2F6FF`, alone lieve); i primari hanno fondo `rgba(242,246,255,.92)` e testo scuro. Focus evidente, transizioni brevi e contrasto AA. Testo ordinario almeno 14 px (mai sotto 12 px).

## Cervello 3D
Il nucleo Guardian è una geometria 3D reale con prospettiva, luce, guscio di punti, anelli, filamenti e particelle. Ruota e respira lentamente; trascinamento, zoom e reset da tastiera sono accessibili. I suoi stati derivano esclusivamente dallo stato reale di Guardian e della voce. Conservare l’Atlas Canvas 2D come fallback WebGL.

## Tre computer e percorsi
Mostrare i dispositivi registrati e il loro stato effettivo, mai dedurre la connessione senza heartbeat. Completare gli slot mancanti con nodi non collegati. Associare agenti usando le relazioni esistenti; esporre nome, stato e dettagli realmente disponibili. Percorsi tridimensionali collegano ogni computer al nucleo: flussi e marker cambiano solo in risposta a eventi e attività reali; niente metriche o traffico inventati.

## Agenti in movimento
Ogni agente attivo è raggiungibile anche tramite DOM/accessibile. Animazioni e traiettorie seguono stato agente, task ed eventi realtime; approvazione in attesa, completamento ed errore hanno stati leggibili oltre al colore. Nessun movimento casuale.

## Pannelli di vetro
Dettagli e sezioni si aprono sopra la scena in pannelli scuri traslucidi, leggibili e limitati al pannello; il nucleo resta visibile. Riutilizzare i pannelli esistenti. Supportare Esc, tastiera, focus contenuto e ritorno del focus; su telefono usare un foglio inferiore. Rispetta `prefers-reduced-motion`.

## Email
Finché non esiste un’integrazione, mostrare “Email non collegata” e uno stato vuoto esplicito per collegare Gmail. Non inventare messaggi né fingere invii. Tipizzare bozza, approvazione, invio, inviata ed errore; inviare richiede sempre approvazione.

## Dati, accessibilità e prestazioni
Numeri, macchine, stati e attività provengono dallo snapshot reale. Stelle e polvere sono decorative e dichiarate tali nel riepilogo accessibile; ogni informazione della scena è disponibile anche nei controlli DOM. Usare semantica, nomi accessibili, focus visibile, contrasto AA, target comodi, navigazione da tastiera e regioni live appropriate.

Usare un solo ciclo di rendering, sospenderlo a scheda nascosta, limitare DPR e qualità adattiva, evitare render React per frame, rilasciare risorse e caricare Three.js in modo lazy. Niente blur a schermo intero o nuovi loop di polling.

## Funzionalità e linee guida
Preservare autenticazione, dati Supabase, realtime, stanze, agenti, task, approvazioni, dispositivi, voce, navigazione e logica dei pannelli esistenti. Ogni modifica frontend deve applicare le Vercel Web Interface Guidelines e la skill `web-design-guidelines` quando disponibile.
