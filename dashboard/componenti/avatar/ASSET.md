# Volto Guardian

`volto.b64` contiene la porzione del volto adattata dalla mesh anatomica
`base.obj` di [MakeHuman](https://github.com/makehumancommunity/makehuman/blob/master/makehuman/data/3dobjs/base.obj),
pubblicata con licenza [CC0 1.0](https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md).
Attribuzione volontaria: Data Collection AB, Joel Palmius e Jonas Hauquier.

L'asset contiene 3.890 vertici con normali e 23.016 indici come Float32 e Uint16
little-endian. Guardian ritaglia la regione anatomica sopra la base del collo,
triangola la superficie, calcola normali morbide e adatta scala e origine.
Corazza, materiali, movimenti e deformazione mandibolare sono implementati
localmente in `modello.html`.

Riferimenti estetici e tecnici: [Electra, SideFX](https://www.sidefx.com/tutorials/titan-evo-electra-reskin/)
per corazza e articolazioni, [MetaHuman Animator, Epic](https://www.youtube.com/watch?v=doax4FU1-t0)
per l'animazione facciale da audio, [asset anatomici Blender](https://www.blender.org/download/demo-files/)
per una futura mesh con rig completo. La mandibola attuale segue l'attivazione della voce.

Il ritratto cinematografico è un asset originale creato con ImageGen per Guardian.
La vista predefinita lo anima con un lieve spostamento e luce al puntatore e
lo stato della voce. In Opzioni si può aprire il modello WebGL con articolazioni.
