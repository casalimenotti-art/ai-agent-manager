# Stile dell'HQ con il volto di NEXO Sentinel

Piano di stile scritto con la skill `frontend-design` prima del codice.

## Soggetto
È un centro di comando per tre persone di una piccola azienda (NEXO SRL).
Il soggetto è una **macchina vecchia e affidabile, al lavoro di notte in officina**: lamiera, ruggine, un solo occhio blu acceso.
Il lavoro principale della pagina è far capire subito *cosa sta facendo Guardian*. Il volto lo dice senza parole, i numeri lo confermano.

## Colori (5)
| Nome | Esadecimale | Ruolo |
|---|---|---|
| Lamiera di notte | `#05070a` | fondo; il volto si dissolve qui ai bordi |
| Grafite | `rgba(9, 12, 16, 0.62)` | vetro dei pannelli sopra il volto |
| Acciaio | `#8d99a8` | testo secondario, bordi tenui |
| Blu nucleo | `#3fb8ff` | unico accento: è la luce dell'occhio, quindi azioni e focus |
| Ambra segnale | `#fbbf24` | solo per ciò che aspetta una persona (approvazioni) |

I colori di stato (ok, attenzione, errore) restano quelli dei token, sempre accompagnati da icona e testo.

## Caratteri
- **Barlow Condensed 600** per i titoli e i numeri grandi. È stretto, da targhetta industriale, ed è coerente con lo stencil «NEXO SRL». Cifre tabellari.
- Testo corrente nel sans di sistema già in uso, per non appesantire.
- Il monospazio solo dove serve davvero (ID, log), non come decorazione delle etichette.

## Layout (desktop)
```
┌ header (vetro) ───────────────────────────────────────────────────────────┐
│rail│ ┌ colonna di vetro ┐                                                 │
│    │ │ Guardian          │                 ◉  ← occhio del volto           │
│    │ │ stato in parole   │                    (circa 60% x, 42% y)         │
│    │ │ [Conversazione]   │                                                 │
│    │ │ 4 numeri          │                                                 │
│    │ └──────────────────┘                                                 │
│    │ stanze · prossime azioni · task · attività (scorrendo, pannelli scuri) │
└────┴ dock della chat (vetro) ─────────────────────────────────────────────┘
```
Il testo è allineato a sinistra. La metà destra della prima schermata resta libera per il volto.

## Principi
1. **Una sola cosa luminosa.** L'occhio. Niente glow su testi, card o pulsanti; il blu dell'accento è la stessa luce dell'occhio.
2. **Il vetro solo dove copre il volto** (header, rail, colonna dello stato, dock, pannelli laterali): al massimo 5 superfici
   sfocate. Le card più in basso sono lamiera scura semi-opaca, senza sfocatura.
3. **Il movimento risponde a qualcosa di reale.** Il volto si anima per richieste, voce ed eventi. L'interfaccia non ha
   animazioni decorative in più.
4. **Leggibilità prima dell'atmosfera.** Dietro ogni testo c'è un velo scuro sufficiente per il contrasto AA. Con la
   trasparenza ridotta o il vetro spento, i pannelli diventano opachi.

## Revisione contro la skill
- Evitato il "nero con un solo accento acido": il blu non è un colore scelto a caso, è la luce del soggetto, e il fondo non è
  piatto (è il volto).
- Evitate le etichette tutte maiuscole in monospazio come decorazione. Restano i titoli di sezione esistenti, in Barlow.
- Evitate le card tutte uguali con la stessa ombra: la gerarchia è vetro (sopra il volto) e lamiera (sotto).
