"""Strati del volto NEXO Sentinel per la dashboard ("2.5D fotografico").

Dalla stessa camera di costruisci.py renderizza gli strati che lo shader della dashboard compone dal vivo:
  base.webp        tutto spento (occhio, anelli, nucleo, bocca, luce dell'occhio)
  luce.webp        (acceso − base): bagliore e riflessi blu dell'occhio sulle piastre, da sommare
  anelli.webp      solo gli anelli emissivi su nero
  bocca.webp       solo la griglia emissiva (acceso − base)
  iride.webp       atlante 4×2 di 8 ritagli dell'occhio acceso, iride da chiusa (0) ad aperta (7)
  profondita.webp  distanza dalla camera (vicino = chiaro), per la parallasse
  meta.json        dimensioni, centro ed ellisse dell'occhio, rettangolo del ritaglio dell'iride (in pixel)
Uscita: <uscita>/ (1920×1080) e <uscita>/960/ (960×540).

Uso:  python tools/volto3d/strati.py --uscita guardian-web/public/volto [--campioni 64] [--larghezza 1920]
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import costruisci as C  # noqa: E402  (importa anche bpy)
import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

EMISSIVI_OCCHIO = ("Mat_Nucleo", "Mat_Led_-1", "Mat_Led_1")


def argomenti():
    p = argparse.ArgumentParser()
    p.add_argument("--uscita", default="guardian-web/public/volto")
    p.add_argument("--campioni", type=int, default=64)
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--solo", default="", help="elenco di strati da rifare, es. base,luce")
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])


def forza_emissione(nome, valore):
    m = bpy.data.materials.get(nome)
    if not m:
        return
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Emission Strength"].default_value = valore


class Scena:
    def __init__(self):
        self.sc = C.costruisci("A")
        self.orig = {}
        for nome in ("Mat_Occhio", "Mat_Nucleo", "Bocca_Griglia", "Mat_Led_-1", "Mat_Led_1"):
            m = bpy.data.materials.get(nome)
            if m:
                b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                self.orig[nome] = b.inputs["Emission Strength"].default_value
        # inquadratura da sfondo della dashboard: testa intera, spostata a destra (a sinistra vanno i pannelli)
        cam = self.sc.camera.data
        cam.lens, cam.shift_x, cam.shift_y = 46, -0.17, 0.02
        # sfondo molto scuro: la parete resta in penombra, il volto prende la luce
        for nome, f in (("Radente_lato", 0.0), ("Radente_parete", 0.45), ("Chiave", 0.85), ("Schiarita", 0.6)):
            o = bpy.data.objects.get(nome)
            if o:
                o.data.energy *= f
        self.luce = bpy.data.objects["Luce_occhio"]
        self.energia = self.luce.data.energy

    def imposta(self, occhio=0.0, anelli=0.0, bocca=0.0):
        for nome in EMISSIVI_OCCHIO:
            if nome in self.orig:
                forza_emissione(nome, self.orig[nome] * occhio)
        forza_emissione("Mat_Occhio", self.orig["Mat_Occhio"] * anelli)
        forza_emissione("Bocca_Griglia", self.orig["Bocca_Griglia"] * bocca)
        self.luce.data.energy = self.energia * occhio

    def holdout(self, tieni):
        """Tutto ciò che non inizia con uno dei prefissi in `tieni` diventa holdout (buco nero trasparente)."""
        for o in bpy.data.objects:
            if o.type in ("MESH", "CURVE", "FONT"):
                o.is_holdout = not any(o.name.startswith(t) for t in tieni)

    def niente_holdout(self):
        for o in bpy.data.objects:
            if o.type in ("MESH", "CURVE", "FONT"):
                o.is_holdout = False

    def iride(self, apertura):
        """Lamelle dall'interno (r=0.10, chiusa) al bordo della ghiera (r=0.30, aperta)."""
        E = Vector((0, -0.70, 0.10))
        r = 0.10 + 0.20 * apertura
        for i in range(10):
            o = bpy.data.objects.get(f"Iride_{i}")
            ang = 2 * math.pi * i / 10
            o.location = E + Vector((r * math.cos(ang), -0.01, r * math.sin(ang)))
            o.rotation_euler = (0, math.radians(-math.degrees(ang) - 70 + 35 * (1 - apertura)), 0)
            o.scale = (1.35, 1, 1.7)  # lamelle abbastanza grandi da chiudere l'occhio


def leggi(file):
    from PIL import Image
    return Image.open(file).convert("RGB")


def differenza(acceso, base):
    import numpy as np
    from PIL import Image
    a = np.asarray(acceso, dtype=np.int16)
    b = np.asarray(base, dtype=np.int16)
    return Image.fromarray(np.clip(a - b, 0, 255).astype("uint8"))


def salva(im, cartella, nome, qualita=86, mezza=False):
    from PIL import Image
    os.makedirs(os.path.join(cartella, "960"), exist_ok=True)
    w, h = im.size
    grande = im.resize((w // 2, h // 2), Image.LANCZOS) if mezza else im
    grande.save(os.path.join(cartella, f"{nome}.webp"), "WEBP", quality=qualita, method=6)
    im.resize((960, int(960 * h / w)), Image.LANCZOS).save(os.path.join(cartella, "960", f"{nome}.webp"), "WEBP", quality=qualita - 4, method=6)


def proietta(sc, p):
    cam = sc.camera
    v = world_to_camera_view(sc, cam, p)
    return (v.x * sc.render.resolution_x, (1 - v.y) * sc.render.resolution_y)


def main():
    a = argomenti()
    solo = set(filter(None, a.solo.split(",")))
    fai = lambda nome: not solo or nome in solo  # noqa: E731
    out = os.path.abspath(a.uscita)
    tmp = os.path.join(out, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    S = Scena()
    sc = S.sc
    W, H = a.larghezza, int(a.larghezza * 0.5625)
    rend = lambda file, campioni, trasparente=False: (setattr(sc.render, "film_transparent", trasparente),  # noqa: E731
                                                      C.renderizza(sc, file, campioni, W, post=False))

    # geometria dell'occhio proiettata (per lo shader): prima fissa la risoluzione, la proiezione la usa
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    bpy.context.view_layer.update()
    occhio = bpy.data.objects["Occhio"]
    M = occhio.matrix_world
    c = proietta(sc, M.translation)
    asse_x = proietta(sc, M @ Vector((0.30, 0, 0)))
    asse_y = proietta(sc, M @ Vector((0, 0, 0.30)))
    bordo = [proietta(sc, M @ Vector((0.44 * math.cos(t), 0, 0.44 * math.sin(t)))) for t in [i * math.pi / 18 for i in range(36)]]
    x0, x1 = int(min(p[0] for p in bordo)), int(max(p[0] for p in bordo)) + 1
    y0, y1 = int(min(p[1] for p in bordo)), int(max(p[1] for p in bordo)) + 1
    meta = {"larghezza": W, "altezza": H, "occhio": {"centro": c, "asse_x": [asse_x[0] - c[0], asse_x[1] - c[1]],
            "asse_y": [asse_y[0] - c[0], asse_y[1] - c[1]], "raggio_mondo": 0.30},
            "iride": {"rettangolo": [x0, y0, x1 - x0, y1 - y0], "fotogrammi": 8, "colonne": 4, "righe": 2},
            "generato_da": "tools/volto3d/strati.py (NEXO Sentinel, variante A, seme 7472)"}

    if fai("base") or fai("luce"):
        S.imposta(0, 0, 0)
        rend(os.path.join(tmp, "base.png"), a.campioni)
        salva(leggi(os.path.join(tmp, "base.png")), out, "base", 88)
    if fai("luce"):
        S.imposta(occhio=1, anelli=0, bocca=0)
        rend(os.path.join(tmp, "acceso.png"), a.campioni)
        salva(differenza(leggi(os.path.join(tmp, "acceso.png")), leggi(os.path.join(tmp, "base.png"))), out, "luce", 84, mezza=True)
    if fai("anelli"):
        S.imposta(0, anelli=1, bocca=0)
        S.holdout(("Anello_",))
        nascosti = [o for o in bpy.data.objects if o.name.startswith(("Vetro_occhio", "Iride_", "Nucleo"))]
        for o in nascosti:  # vetro, lamelle e nucleo davanti non devono "bucare" gli anelli
            o.hide_render = True
        rend(os.path.join(tmp, "anelli.png"), max(16, a.campioni // 4), trasparente=True)
        S.niente_holdout()
        for o in nascosti:
            o.hide_render = False
        salva(leggi(os.path.join(tmp, "anelli.png")), out, "anelli", 84)
    if fai("bocca"):
        S.imposta(0, 0, bocca=1)
        S.holdout(("Bocca_", "Griglia_"))
        rend(os.path.join(tmp, "bocca.png"), max(16, a.campioni // 4), trasparente=True)
        S.niente_holdout()
        salva(leggi(os.path.join(tmp, "bocca.png")), out, "bocca", 84)
    if fai("iride"):
        from PIL import Image
        S.imposta(occhio=1, anelli=0, bocca=0)
        r = sc.render
        r.use_border, r.use_crop_to_border = True, True
        r.border_min_x, r.border_max_x = x0 / W, x1 / W
        r.border_min_y, r.border_max_y = 1 - y1 / H, 1 - y0 / H
        atlante = None
        for k in range(8):
            S.iride(k / 7)
            f = os.path.join(tmp, f"iride_{k}.png")
            rend(f, max(24, a.campioni // 2))
            im = leggi(f)
            if atlante is None:
                atlante = Image.new("RGB", (im.width * 4, im.height * 2))
            atlante.paste(im, ((k % 4) * im.width, (k // 4) * im.height))
        r.use_border = False
        S.iride(0.45)
        meta["iride"]["fotogramma"] = [atlante.width // 4, atlante.height // 2]
        salva(atlante, out, "iride", 84)
    if fai("profondita"):
        # distanza dalla camera come emissione in scala di grigi (vicino = chiaro), 1 campione, vista "Standard"
        prof = bpy.data.materials.new("Mat_Profondita")
        N = C.Nodi(prof)
        cam = N.n("ShaderNodeCameraData")
        mp = N.n("ShaderNodeMapRange")
        mp.inputs["From Min"].default_value, mp.inputs["From Max"].default_value = 2.0, 12.0
        mp.inputs["To Min"].default_value, mp.inputs["To Max"].default_value = 1.0, 0.0
        N.l(cam.outputs["View Z Depth"], mp.inputs["Value"])
        em = N.n("ShaderNodeEmission")
        N.l(mp.outputs["Result"], em.inputs["Strength"])
        N.l(em.outputs[0], N.out.inputs[0])
        bpy.context.view_layer.material_override = prof
        vt = sc.view_settings.view_transform
        sc.view_settings.view_transform = "Standard"
        sc.render.engine, sc.cycles.device = "CYCLES", "CPU"  # EEVEE vorrebbe una GPU
        sc.cycles.use_denoising = False
        sc.render.film_transparent = False
        sc.cycles.samples = 2
        sc.render.resolution_x, sc.render.resolution_y = W, H
        sc.render.filepath = os.path.join(tmp, "profondita.png")
        bpy.ops.render.render(write_still=True)
        bpy.context.view_layer.material_override = None
        sc.view_settings.view_transform = vt
        from PIL import ImageFilter
        import numpy as np
        from PIL import Image
        z = np.asarray(leggi(os.path.join(tmp, "profondita.png")).convert("L"), dtype=np.float32)
        lo, hi = np.percentile(z, 2), np.percentile(z, 99.5)  # stira tra il fondo (parete) e il punto più vicino
        z = np.clip((z - lo) / max(1.0, hi - lo), 0, 1) * 255
        salva(Image.fromarray(z.astype("uint8")).filter(ImageFilter.GaussianBlur(3)).convert("RGB"), out, "profondita", 80, mezza=True)
    with open(os.path.join(out, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("STRATI FATTI", out)


if __name__ == "__main__":
    main()
