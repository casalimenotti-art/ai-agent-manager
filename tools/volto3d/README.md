# NEXO Sentinel: il volto 3D di Guardian

Il robot è un design **originale** di NEXO: una testa da mech con un grande occhio-nucleo blu, la scritta «NEXO SRL»
consumata sulla fronte e la matricola «NX-7472». Non copia personaggi esistenti.
Lo script lo costruisce **da zero**: geometria, materiali consumati, luci e render.

## Rigenerarlo
Blender non serve installarlo: c'è come modulo Python su PyPI (`bpy`, Blender 5.3).
```bash
python3.13 -m venv .venv-blender && .venv-blender/bin/pip install bpy pillow
.venv-blender/bin/python tools/volto3d/costruisci.py --variante A --uscita tools/volto3d/concept --campioni 64 --larghezza 1280
```
- Varianti: `A` (massiccio scuro), `B` (grigio oliva).
- Uscita: `sentinel-<variante>.png`, il render, e `sentinel-<variante>.blend`, che si apre in Blender ma non va in git.
- Tempi: circa 5–10 minuti a 1280 px con 64 campioni su una CPU a 4 core. Con una GPU NVIDIA è molto più veloce.

## Strati per la dashboard (`strati.py`)
La dashboard non mostra un'immagine ferma: compone dal vivo gli **strati** renderizzati dalla stessa camera.
```bash
.venv-blender/bin/python tools/volto3d/strati.py --uscita guardian-web/public/volto --campioni 48 --larghezza 1920
.venv-blender/bin/python tools/volto3d/verifica_strati.py guardian-web/public/volto
```
Gli strati sono:
- `base`: tutto spento;
- `luce`: acceso − base, cioè il bagliore blu sulle piastre;
- `anelli`;
- `bocca`;
- `iride`: atlante di 8 aperture;
- `profondita`: serve alla parallasse, cioè ai micro-movimenti della testa;
- `meta.json`: posizione ed ellisse dell'occhio.

Escono in 1920×1080 e 960×540. In tutto circa 45–60 minuti su CPU. I render grezzi finiscono in `tools/volto3d/_tmp_strati/` (fuori da `public/`, non vanno in git).
L'inquadratura degli strati è più larga di quella dei concept: la testa è intera e spostata a destra, perché a sinistra vanno
i pannelli. Anche la parete è più scura.

## Com'è fatto il realismo (tutto procedurale, nessuna texture scaricata)
- **Vernice consumata**:
  - sugli spigoli, che il nodo AO "inside" riconosce, compare l'acciaio sotto;
  - chiazze di vernice saltata;
  - graffi direzionali;
  - sporco e ruggine nelle cavità, grazie al nodo AO normale.
- **Normali**: piccole ammaccature, bordo della vernice scheggiata, spigoli arrotondati con il nodo Bevel.
- **Stencil**: la vernice delle scritte è bucata, scagliata e rigata. Un Mix con Transparent la fa sembrare vecchia di anni.
- **Luce**: luce principale fredda, controluce calda, il blu dell'occhio che illumina davvero le piastre, alone sullo sfondo.
- **Resa**: Cycles, AgX con contrasto medio-alto, profondità di campo a fuoco sull'occhio. Un leggero alone (bloom) sui
  punti luminosi viene aggiunto dopo il render.

## Nomi (contratto per animarlo nella dashboard)
`Testa` (radice), `Occhio` (posizione dell'occhio), `Anello_1..3`, `Iride_0..9`, `Nucleo`, materiali `Mat_Occhio`,
`Mat_Nucleo` e `Bocca_Griglia` (emissivi). Un modello fatto da un artista con gli stessi nomi si sostituisce senza toccare il codice.

## Usura (variante A)
- **Geometria**:
  - ammaccature vere (suddivisione + Displace a bassa frequenza);
  - tre crateri d'impatto: vuoti `Impatto_*`, con vernice saltata, graffi a raggiera e annerimento.
- **Superficie**:
  - bruciature e colature d'olio;
  - due cordoni di saldatura;
  - vetro dell'occhio incrinato (Voronoi "distance to edge" su rugosità e normale);
  - stencil ancora più consumato.
- **Dettagli**: un bullone mancante, con il foro arrugginito.

## Strumenti open source valutati (27/11/2026)
| Strumento | Cosa fa | Si può usare? |
|---|---|---|
| **Blender (`bpy` da PyPI)** | modellazione, materiali e render da script | **Sì**: è quello usato qui, gratis (GPL) |
| **blender-mcp** (`ahujasid/blender-mcp`) | Claude comanda Blender aperto sul PC, in diretta | Sì, sul PC del titolare (serve Blender con interfaccia). Utile per ritocchi a mano guidati |
| **TRELLIS.2** (Microsoft) | da un'immagine a un modello 3D con texture PBR | Codice MIT, ma le librerie NVIDIA da cui dipende sono solo per uso non commerciale. Serve una GPU NVIDIA (circa 24 GB; forse 8 GB con versioni ottimizzate). Qui non c'è GPU |
| **Hunyuan3D 2.x** (Tencent) | come sopra, ottima qualità | **No in Italia**: la licenza esclude l'Unione Europea |
| **Open-Higgsfield** (vari repo) | interfaccia per generare immagini e video | Non fa modelli 3D, e per generare usa servizi a pagamento (chiavi API) |
