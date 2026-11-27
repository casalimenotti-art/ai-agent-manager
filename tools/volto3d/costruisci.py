"""NEXO Sentinel — volto di robot originale, costruito interamente da script (Blender 5.x, modulo bpy).

Uso:  python tools/volto3d/costruisci.py --variante A --uscita tools/volto3d/concept/ [--campioni 96] [--larghezza 1600]
Produce: <uscita>/sentinel-<variante>.png (render Cycles) e <uscita>/sentinel-<variante>.blend.

Design originale di NEXO: testa da mech con un grande occhio-nucleo blu al centro, piastre di metallo verniciato e consumato,
stencil «NEXO SRL» sulla fronte e matricola «NX-7472». Non riproduce personaggi esistenti.
Nomi degli oggetti secondo tools/volto3d/CONTRATTO.md (Testa, Occhio, Anello_1..3, Iride_*, Bocca_Griglia, Mat_Occhio).
"""
import argparse
import math
import sys

import bpy  # deve venire prima di bmesh e mathutils
import bmesh
from mathutils import Euler, Vector

VARIANTI = {
    # vernice, acciaio, colore del testo
    "A": dict(vernice=(0.022, 0.025, 0.027), vernice2=(0.034, 0.036, 0.034), testo=(0.80, 0.78, 0.70), nome="massiccio scuro"),
    "B": dict(vernice=(0.075, 0.082, 0.060), vernice2=(0.10, 0.105, 0.08), testo=(0.85, 0.82, 0.72), nome="grigio oliva"),
}
BLU = (0.02, 0.32, 1.0)
CIANO = (0.10, 0.70, 1.0)


def argomenti():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--variante", default="A", choices=VARIANTI)
    p.add_argument("--uscita", default="tools/volto3d/concept/")
    p.add_argument("--campioni", type=int, default=96)
    p.add_argument("--larghezza", type=int, default=1600)
    return p.parse_args(a)


# ------------------------------------------------------------------ nodi
def presa(nodo, ident):
    for s in list(nodo.inputs) + list(nodo.outputs):
        if s.identifier == ident or s.name == ident:
            return s
    raise KeyError(ident)


class Nodi:
    def __init__(self, mat):
        mat.use_nodes = True
        self.t = mat.node_tree
        self.t.nodes.clear()
        self.out = self.n("ShaderNodeOutputMaterial")

    def n(self, tipo, **prop):
        nodo = self.t.nodes.new(tipo)
        for k, v in prop.items():
            setattr(nodo, k, v)
        return nodo

    def l(self, a, b):
        self.t.links.new(a, b)

    def rampa(self, ingresso, p0, p1, c0=(0, 0, 0, 1), c1=(1, 1, 1, 1)):
        r = self.n("ShaderNodeValToRGB")
        e = r.color_ramp.elements
        e[0].position, e[0].color = p0, c0
        e[1].position, e[1].color = p1, c1
        self.l(ingresso, r.inputs[0])
        return r.outputs[0]

    def rumore(self, scala, dettaglio=8.0, rugosita=0.6, vettore=None):
        x = self.n("ShaderNodeTexNoise")
        x.inputs["Scale"].default_value = scala
        x.inputs["Detail"].default_value = dettaglio
        x.inputs["Roughness"].default_value = rugosita
        if vettore is not None:
            self.l(vettore, x.inputs["Vector"])
        return x.outputs["Fac"]

    def mat(self, op, a, b=None, val=None):
        m = self.n("ShaderNodeMath", operation=op)
        m.use_clamp = True
        self.l(a, m.inputs[0]) if not isinstance(a, (int, float)) else setattr(m.inputs[0], "default_value", a)
        if b is not None:
            self.l(b, m.inputs[1]) if not isinstance(b, (int, float)) else setattr(m.inputs[1], "default_value", b)
        return m.outputs[0]

    def mix(self, fac, a, b):
        m = self.n("ShaderNodeMix", data_type="RGBA")
        self.l(fac, presa(m, "Factor_Float"))
        for ident, v in (("A_Color", a), ("B_Color", b)):
            s = presa(m, ident)
            if isinstance(v, tuple):
                s.default_value = (*v, 1) if len(v) == 3 else v
            else:
                self.l(v, s)
        return presa(m, "Result_Color")


def materiale_vernice(nome, colore, colore2, ruggine=True, forza_ruggine=1.4, colate=False, ao=True, crateri=(), segni=False):
    """Vernice su acciaio: usura sugli spigoli (AO interno), graffi, sporco e ruggine nelle cavità, ammaccature nella normale."""
    m = bpy.data.materials.new(nome)
    N = Nodi(m)
    bsdf = N.n("ShaderNodeBsdfPrincipled")
    N.l(bsdf.outputs[0], N.out.inputs[0])
    coord = N.n("ShaderNodeTexCoord").outputs["Object"]
    # spigoli convessi: AO "inside" bassa sugli spigoli
    if ao:
        ao_in = N.n("ShaderNodeAmbientOcclusion", inside=True, only_local=True)
        ao_in.inputs["Distance"].default_value = 0.04
        spigoli = N.mat("SUBTRACT", 1.0, ao_in.outputs["AO"])
    else:  # versione veloce per superfici grandi (parete): niente raggi AO, usura dal rumore
        spigoli = N.mat("MULTIPLY", N.rumore(12.0, 8, 0.7, coord), 0.32)
    rotto = N.rumore(9.0, 12, 0.7, coord)
    usura = N.rampa(N.mat("MULTIPLY", N.mat("ADD", spigoli, N.mat("MULTIPLY", rotto, 0.55)), 1.5), 0.66, 0.70)
    # graffi: rumore stirato in una direzione
    stira = N.n("ShaderNodeMapping")
    stira.inputs["Scale"].default_value = (2.0, 2.0, 70.0)
    stira.inputs["Rotation"].default_value = (0.4, 0.9, 0.2)
    N.l(coord, stira.inputs["Vector"])
    graffi = N.rampa(N.rumore(14.0, 4, 0.5, stira.outputs[0]), 0.685, 0.715)
    chiazze = N.rampa(N.mat("MULTIPLY", N.rumore(4.0, 14, 0.8, coord), N.mat("ADD", spigoli, 0.6)), 0.47, 0.51)
    scoperto = N.mat("MAXIMUM", N.mat("MAXIMUM", usura, chiazze), N.mat("MULTIPLY", graffi, 0.6))
    fuliggini = []
    # crateri d'impatto: attorno a ogni vuoto "Impatto" la vernice è saltata, con graffi radiali
    for vuoto in crateri:
        tc = N.n("ShaderNodeTexCoord", object=vuoto)
        dist = N.n("ShaderNodeVectorMath", operation="LENGTH")
        N.l(tc.outputs["Object"], dist.inputs[0])
        anello = N.rampa(dist.outputs["Value"], 0.55, 1.45, (1, 1, 1, 1), (0, 0, 0, 1))
        sfr = N.n("ShaderNodeVectorMath", operation="NORMALIZE")
        N.l(tc.outputs["Object"], sfr.inputs[0])
        raggi = N.rampa(N.rumore(9.0, 3, 0.5, sfr.outputs[0]), 0.52, 0.58)
        nucleo_c = N.rampa(N.mat("ADD", dist.outputs["Value"], N.mat("MULTIPLY", rotto, 0.35)), 0.45, 0.62, (1, 1, 1, 1), (0, 0, 0, 1))
        cratere = N.mat("MAXIMUM", nucleo_c, N.mat("MULTIPLY", anello, N.mat("MULTIPLY", raggi, 1.3)))
        scoperto = N.mat("MAXIMUM", scoperto, cratere)
        fuliggini.append(N.rampa(N.mat("ADD", dist.outputs["Value"], N.mat("MULTIPLY", rotto, 0.6)), 0.5, 2.0, (1, 1, 1, 1), (0, 0, 0, 1)))
    # cavità: AO normale → sporco e ruggine
    if ao:
        ao_n = N.n("ShaderNodeAmbientOcclusion")
        ao_n.inputs["Distance"].default_value = 0.25
        cavita = N.rampa(ao_n.outputs["AO"], 0.35, 0.85, (1, 1, 1, 1), (0, 0, 0, 1))
    else:
        cavita = N.rampa(N.rumore(6.0, 10, 0.7, coord), 0.40, 0.65)
    macchie = N.rampa(N.rumore(5.0, 10, 0.75, coord), 0.45, 0.70)
    # vernice irregolare (due toni + sbiaditura)
    variaz = N.rumore(2.5, 6, 0.5, coord)
    tinta = N.mix(variaz, colore, colore2)
    acciaio = N.mix(N.rumore(30.0, 6, 0.6, coord), *(((0.30, 0.30, 0.31), (0.50, 0.50, 0.51)) if ao else ((0.10, 0.10, 0.10), (0.20, 0.19, 0.18))))
    colore_f = N.mix(scoperto, tinta, acciaio)
    sporco = N.mat("MULTIPLY", cavita, 0.75)
    colore_f = N.mix(sporco, colore_f, (0.025, 0.02, 0.015))
    if ruggine:
        rug = N.mat("MULTIPLY", N.mat("MULTIPLY", cavita, macchie), forza_ruggine)
        if colate:  # colature di ruggine verso il basso e chiazze sparse: lamiera esposta per anni
            giu = N.n("ShaderNodeMapping")
            giu.inputs["Scale"].default_value = (28.0, 28.0, 1.2)
            N.l(coord, giu.inputs["Vector"])
            col = N.rampa(N.rumore(3.0, 6, 0.6, giu.outputs[0]), 0.55, 0.75)
            sparse = N.rampa(N.rumore(1.6, 12, 0.75, coord), 0.50, 0.68)
            rug = N.mat("MAXIMUM", rug, N.mat("MAXIMUM", N.mat("MULTIPLY", col, 0.8), N.mat("MULTIPLY", sparse, 0.9)))
        colore_f = N.mix(rug, colore_f, N.mix(N.rumore(40.0), (0.18, 0.06, 0.02), (0.32, 0.12, 0.04)))
    for f in fuliggini:  # annerimento attorno al colpo
        colore_f = N.mix(N.mat("MULTIPLY", f, 0.85), colore_f, (0.008, 0.006, 0.005))
    if segni:  # bruciature e colature d'olio: anni di servizio
        pos = N.n("ShaderNodeNewGeometry").outputs["Position"]
        giu = N.n("ShaderNodeMapping")
        giu.inputs["Scale"].default_value = (22.0, 22.0, 0.9)
        N.l(pos, giu.inputs["Vector"])
        olio = N.mat("MULTIPLY", N.rampa(N.rumore(2.2, 5, 0.55, giu.outputs[0]), 0.58, 0.72), N.rampa(N.rumore(1.1, 3, 0.4, pos), 0.42, 0.62))
        colore_f = N.mix(N.mat("MULTIPLY", olio, 0.85), colore_f, (0.006, 0.005, 0.004))
        brucia = N.rampa(N.rumore(1.4, 10, 0.72, pos), 0.60, 0.74)
        colore_f = N.mix(N.mat("MULTIPLY", brucia, 0.8), colore_f, N.mix(N.rumore(25.0, 6, 0.7, pos), (0.012, 0.009, 0.007), (0.06, 0.035, 0.02)))
    N.l(colore_f, bsdf.inputs["Base Color"])
    N.l(scoperto, bsdf.inputs["Metallic"])
    rough = N.mat("ADD", N.mat("MULTIPLY", N.rumore(18.0), 0.25), N.mat("MULTIPLY", scoperto, -0.25))
    N.l(N.mat("ADD", rough, 0.42), bsdf.inputs["Roughness"])
    # ammaccature e bordo della vernice scheggiata nella normale
    altezza = N.mat("ADD", N.mat("MULTIPLY", N.rumore(3.0, 4, 0.4, coord), 0.6), N.mat("MULTIPLY", usura, -0.25))
    altezza = N.mat("ADD", altezza, N.mat("MULTIPLY", graffi, -0.35))
    bump = N.n("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.01
    N.l(altezza, bump.inputs["Height"])
    bev = N.n("ShaderNodeBevel")
    bev.inputs["Radius"].default_value = 0.006
    N.l(bev.outputs[0], bump.inputs["Normal"])
    N.l(bump.outputs[0], bsdf.inputs["Normal"])
    return m


def materiale_semplice(nome, colore, metallo=0.0, rugo=0.5, emissione=None, forza=0.0, vetro=False):
    m = bpy.data.materials.new(nome)
    N = Nodi(m)
    b = N.n("ShaderNodeBsdfPrincipled")
    N.l(b.outputs[0], N.out.inputs[0])
    b.inputs["Base Color"].default_value = (*colore, 1)
    b.inputs["Metallic"].default_value = metallo
    b.inputs["Roughness"].default_value = rugo
    if emissione:
        b.inputs["Emission Color"].default_value = (*emissione, 1)
        b.inputs["Emission Strength"].default_value = forza
    if vetro:
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["IOR"].default_value = 1.5
        # vetro graffiato: rugosità variabile
        crepe_v = N.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE")
        crepe_v.inputs["Scale"].default_value = 4.0
        crepe = N.rampa(crepe_v.outputs["Distance"], 0.0, 0.01, (1, 1, 1, 1), (0, 0, 0, 1))
        crepe = N.mat("MULTIPLY", crepe, N.rampa(N.rumore(2.0, 4, 0.5), 0.55, 0.7))
        N.l(N.mat("ADD", N.mat("ADD", N.mat("MULTIPLY", N.rampa(N.rumore(80.0, 2), 0.6, 0.66), 0.25), 0.14), N.mat("MULTIPLY", crepe, 0.35)), b.inputs["Roughness"])
        bump = N.n("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.25
        N.l(crepe, bump.inputs["Height"])
        N.l(bump.outputs[0], b.inputs["Normal"])
    return m


def materiale_stencil(nome, colore):
    """Vernice dello stencil molto consumata: buchi, scaglie e sbiaditura (Mix con trasparente)."""
    m = bpy.data.materials.new(nome)
    m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    N = Nodi(m)
    b = N.n("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*colore, 1)
    b.inputs["Roughness"].default_value = 0.75
    tr = N.n("ShaderNodeBsdfTransparent")
    mixs = N.n("ShaderNodeMixShader")
    coord = N.n("ShaderNodeTexCoord").outputs["Object"]
    buchi = N.rampa(N.rumore(22.0, 12, 0.75, coord), 0.44, 0.52)
    scaglie = N.rampa(N.rumore(70.0, 4, 0.6, coord), 0.55, 0.60)
    stira = N.n("ShaderNodeMapping")
    stira.inputs["Scale"].default_value = (90.0, 3.0, 3.0)
    N.l(coord, stira.inputs["Vector"])
    righe = N.rampa(N.rumore(6.0, 3, 0.5, stira.outputs[0]), 0.64, 0.68)
    via = N.mat("MAXIMUM", N.mat("MAXIMUM", buchi, scaglie), righe)  # 1 = vernice andata
    N.l(via, mixs.inputs[0])
    N.l(b.outputs[0], mixs.inputs[1])
    N.l(tr.outputs[0], mixs.inputs[2])
    N.l(mixs.outputs[0], N.out.inputs[0])
    # la vernice rimasta è sporca e sbiadita
    N.l(N.mix(N.rumore(8.0), colore, tuple(c * 0.55 for c in colore)), b.inputs["Base Color"])
    return m


# ------------------------------------------------------------------ geometria
def oggetto(nome, mesh, mat=None, genitore=None):
    o = bpy.data.objects.new(nome, mesh)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    if genitore:
        o.parent = genitore
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def smussa(o, larghezza=0.025, segmenti=3):
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width, b.segments, b.limit_method = larghezza, segmenti, "ANGLE"
    b.harden_normals = True
    w = o.modifiers.new("Normali", "WEIGHTED_NORMAL")
    w.keep_sharp = True
    return o


def scatola(nome, centro, dim, rot=(0, 0, 0), mat=None, gen=None, bevel=0.025, rastrema=None):
    """Piastra: cubo scalato; rastrema=(fattore_x_alto, fattore_x_davanti) la rende più stretta in alto/davanti."""
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        x, y, z = v.co
        if rastrema:
            fz, fy = rastrema
            k = (1 + (fz - 1) * (z + 0.5)) * (1 + (fy - 1) * (0.5 - (y + 0.5)))
            x *= k
        v.co = Vector((x * dim[0], y * dim[1], z * dim[2]))
    bm.to_mesh(me)
    bm.free()
    o = oggetto(nome, me, mat, gen)
    o.location = centro
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    if bevel:
        smussa(o, bevel)
    return o


def cilindro(nome, centro, raggio, prof, asse="Y", mat=None, gen=None, lati=48, bevel=0.01, rot_extra=(0, 0, 0)):
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lati, radius1=raggio, radius2=raggio, depth=prof)
    bm.to_mesh(me)
    bm.free()
    o = oggetto(nome, me, mat, gen)
    o.location = centro
    r = {"X": (0, 90, 0), "Y": (90, 0, 0), "Z": (0, 0, 0)}[asse]
    o.rotation_euler = Euler([math.radians(a + b) for a, b in zip(r, rot_extra)])
    if bevel:
        smussa(o, bevel, 2)
    return o


def toro(nome, centro, maggiore, minore, mat, gen=None):
    me = bpy.data.meshes.new(nome)
    bm = bmesh.new()
    seg, ring = 96, 16
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        riga = []
        for j in range(ring):
            b = 2 * math.pi * j / ring
            r = maggiore + minore * math.cos(b)
            riga.append(bm.verts.new((r * math.cos(a), minore * math.sin(b), r * math.sin(a))))
        verts.append(riga)
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((verts[i][j], verts[(i + 1) % seg][j], verts[(i + 1) % seg][(j + 1) % ring], verts[i][(j + 1) % ring]))
    bm.to_mesh(me)
    bm.free()
    o = oggetto(nome, me, mat, gen)
    o.location = centro
    return o


def buca(o, taglio, solver="EXACT"):
    m = o.modifiers.new("Buca", "BOOLEAN")
    m.operation, m.object, m.solver = "DIFFERENCE", taglio, solver
    o.modifiers.move(len(o.modifiers) - 1, 0)  # prima del bevel
    taglio.hide_render = True
    taglio.hide_viewport = True


def bullone(centro, normale_rot, mat, gen, r=0.02):
    return cilindro("Bullone", centro, r, 0.022, "Y", mat, gen, lati=6, bevel=0.004, rot_extra=normale_rot)


def testo(nome, frase, centro, rot, misura, mat, gen):
    cu = bpy.data.curves.new(nome, "FONT")
    cu.body = frase
    cu.size = misura
    cu.extrude = 0.0008
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.space_character = 1.12
    o = bpy.data.objects.new(nome, cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    o.parent = gen
    o.location = centro
    o.rotation_euler = Euler([math.radians(a) for a in rot])
    return o


def parete(sc, mat, mat_rivetti):
    """Parete di lamiere d'acciaio chiodate, leggermente sfalsate, dietro la testa (niente fondo nero)."""
    import random
    random.seed(7472)
    W, H, Y = 1.55, 1.15, 1.75
    # un rivetto modello (semisfera schiacciata), copiato in blocco: molto più veloce di migliaia di operazioni bmesh
    tv, tf = [], []
    for j in range(5):
        fi = (math.pi / 2) * j / 4
        for i in range(10):
            th = 2 * math.pi * i / 10
            tv.append((0.024 * math.cos(fi) * math.cos(th), -0.013 * math.sin(fi), 0.024 * math.cos(fi) * math.sin(th)))
    for j in range(4):
        for i in range(10):
            tf.append((j * 10 + i, j * 10 + (i + 1) % 10, (j + 1) * 10 + (i + 1) % 10, (j + 1) * 10 + i))
    centri = []
    for i in range(-4, 5):
        for j in range(-3, 4):
            cx, cz = i * W, 0.1 + j * H
            dy = random.uniform(-0.012, 0.012)
            scatola(f"Lamiera_{i}_{j}", (cx, Y + dy, cz), (W - 0.012, 0.05, H - 0.012),
                    rot=(random.uniform(-0.4, 0.4), random.uniform(-0.25, 0.25), random.uniform(-0.3, 0.3)), mat=mat, bevel=0.012)
            for k in range(13):
                for zz in (cz - H / 2 + 0.07, cz + H / 2 - 0.07):
                    centri.append((cx - W / 2 + 0.07 + k * (W - 0.14) / 12, Y - 0.025 + dy, zz))
            for k in range(1, 9):
                for xx in (cx - W / 2 + 0.07, cx + W / 2 - 0.07):
                    centri.append((xx, Y - 0.025 + dy, cz - H / 2 + 0.07 + k * (H - 0.14) / 9))
    verts, facce = [], []
    for c in centri:
        base = len(verts)
        verts += [(c[0] + x, c[1] + y, c[2] + z) for x, y, z in tv]
        facce += [tuple(base + q for q in f) for f in tf]
    me = bpy.data.meshes.new("Rivetti")
    me.from_pydata(verts, [], facce)
    oggetto("Rivetti", me, mat_rivetti)
    # una lamiera rattoppata e una trave orizzontale per spezzare la griglia
    scatola("Toppa", (-2.6, Y - 0.04, 0.85), (0.7, 0.03, 0.5), rot=(0, 0, 3), mat=mat, bevel=0.01)
    scatola("Trave", (0, Y - 0.08, -0.95), (14, 0.14, 0.22), mat=mat, bevel=0.02)


def ammacca(o, livelli=2, forza=0.006, crateri=()):
    """Ammaccature vere: suddivisione semplice + Displace a bassa frequenza + crateri sferici (vuoti 'Impatto')."""
    sd = o.modifiers.new("Densita", "SUBSURF")
    sd.subdivision_type, sd.levels, sd.render_levels = "SIMPLE", livelli, livelli
    tx = bpy.data.textures.new(f"Bozze_{o.name}", "CLOUDS")
    tx.noise_scale, tx.noise_depth = 0.35, 2
    d = o.modifiers.new("Bozze", "DISPLACE")
    d.texture, d.strength, d.mid_level, d.texture_coords = tx, forza, 0.5, "GLOBAL"
    for vuoto in crateri:
        t = bpy.data.textures.get("Cratere") or bpy.data.textures.new("Cratere", "BLEND")
        t.progression = "SPHERICAL"
        c = o.modifiers.new(f"Cratere_{vuoto.name}", "DISPLACE")
        c.texture, c.strength, c.mid_level = t, -0.07, 0.0
        c.texture_coords, c.texture_coords_object = "OBJECT", vuoto
    o.modifiers.move(o.modifiers.find("Normali"), len(o.modifiers) - 1)


def impatto(nome, pos, raggio, gen):
    e = bpy.data.objects.new(nome, None)
    bpy.context.scene.collection.objects.link(e)
    e.parent, e.location, e.scale = gen, pos, (raggio, raggio, raggio)
    return e


# ------------------------------------------------------------------ scena
def costruisci(v):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    V = VARIANTI[v]
    testa = bpy.data.objects.new("Testa", None)
    sc.collection.objects.link(testa)
    testa.rotation_euler = Euler((math.radians(4), 0, math.radians(-7)))
    imp = [impatto("Impatto_fronte", (-0.52, -0.80, 0.66), 0.09, testa),
           impatto("Impatto_guancia", (0.80, -0.80, 0.14), 0.075, testa),
           impatto("Impatto_mascella", (0.28, -0.79, -0.47), 0.07, testa)]
    vern = materiale_vernice("Mat_Corazza", V["vernice"], V["vernice2"], crateri=imp, segni=True)
    vern_chiara = materiale_vernice("Mat_Corazza_2", tuple(c * 1.35 for c in V["vernice"]), tuple(c * 1.35 for c in V["vernice2"]), crateri=imp, segni=True)
    acciaio = materiale_vernice("Mat_Acciaio", (0.07, 0.072, 0.075), (0.10, 0.10, 0.105), ruggine=True)
    scuro = materiale_semplice("Mat_Interni", (0.015, 0.015, 0.017), 0.6, 0.55)
    gomma = materiale_semplice("Mat_Cavi", (0.01, 0.01, 0.01), 0.0, 0.7)
    occhio = materiale_semplice("Mat_Occhio", (0.0, 0.0, 0.0), 0, 0.3, BLU, 7.0)
    nucleo = materiale_semplice("Mat_Nucleo", (0, 0, 0), 0, 0.3, CIANO, 6.0)
    bocca = materiale_semplice("Bocca_Griglia", (0, 0, 0), 0, 0.5, BLU, 2.5)
    vetro = materiale_semplice("Mat_Vetro", (0.9, 0.95, 1.0), 0, 0.03, vetro=True)
    stencil = materiale_stencil("Mat_Stencil", V["testo"])

    # massa del cranio e piastre principali
    ammacca(scatola("Cranio", (0, 0.25, 0.22), (1.62, 1.45, 1.0), mat=vern, gen=testa, bevel=0.06, rastrema=(0.86, 0.92)), forza=0.01)
    fronte = scatola("Fronte", (0, -0.58, 0.64), (1.78, 0.42, 0.40), rot=(14, 0, 0), mat=vern_chiara, gen=testa, bevel=0.035, rastrema=(0.9, 0.95))
    scatola("Cresta", (0, 0.05, 0.86), (0.34, 1.35, 0.14), mat=vern, gen=testa, bevel=0.03)
    faccia = scatola("Faccia", (0, -0.66, 0.08), (1.16, 0.26, 0.78), mat=vern, gen=testa, bevel=0.03)
    ammacca(fronte, livelli=3, crateri=imp[:1])
    ammacca(faccia)
    guance = []
    scatola("Visiera", (0, -0.86, 0.43), (1.24, 0.42, 0.10), rot=(-12, 0, 0), mat=vern, gen=testa, bevel=0.02, rastrema=(1.0, 0.8))
    for s in (-1, 1):
        guance.append(scatola(f"Guancia_{'L' if s < 0 else 'R'}", (s * 0.80, -0.50, 0.02), (0.46, 0.62, 0.76), rot=(0, s * -4, s * 28),
                mat=vern_chiara, gen=testa, bevel=0.03, rastrema=(0.9, 0.85)))
        ammacca(guance[-1], livelli=3, crateri=imp[1:2] if s > 0 else ())
        scatola(f"Zigomo_{'L' if s < 0 else 'R'}", (s * 0.40, -0.82, -0.25), (0.42, 0.16, 0.13), rot=(0, s * 14, s * 14),
                mat=vern, gen=testa, bevel=0.02)
        cilindro(f"Capsula_{'L' if s < 0 else 'R'}", (s * 0.93, 0.25, 0.22), 0.34, 0.26, "X", acciaio, testa, bevel=0.02)
        cilindro(f"Capsula_anello_{'L' if s < 0 else 'R'}", (s * 1.07, 0.25, 0.22), 0.22, 0.05, "X", scuro, testa, bevel=0.008)
        for i in range(5):  # feritoie laterali
            scatola(f"Feritoia_{s}_{i}", (s * 1.005, -0.42, 0.24 - i * 0.085), (0.04, 0.42, 0.035), rot=(0, 0, s * 20), mat=scuro, gen=testa, bevel=0.006)
    scatola("Solco_fronte", (0, -0.79, 0.86), (0.025, 0.06, 0.12), rot=(14, 0, 0), mat=scuro, gen=testa, bevel=0.004)
    for s in (-1, 1):
        scatola(f"Solco_guancia_{s}", (s * 0.86, -0.72, -0.05), (0.30, 0.02, 0.018), rot=(0, 0, s * 28), mat=scuro, gen=testa, bevel=0.003)
        scatola(f"Piastrina_{s}", (s * 0.62, -0.79, 0.62), (0.28, 0.05, 0.16), rot=(14, 0, s * 6), mat=vern, gen=testa, bevel=0.012)
        cilindro(f"Sensore_{s}", (s * 0.60, -0.86, 0.43), 0.035, 0.05, "Y", acciaio, testa, bevel=0.005)
        cilindro(f"Sensore_luce_{s}", (s * 0.60, -0.888, 0.43), 0.018, 0.01, "Y", materiale_semplice(f"Mat_Led_{s}", (0, 0, 0), 0, 0.3, (1.0, 0.25, 0.05), 4.0), testa, bevel=0)
    scatola("Antenna", (-0.93, 0.32, 0.62), (0.035, 0.035, 0.55), rot=(0, -8, 0), mat=acciaio, gen=testa, bevel=0.008)
    ammacca(scatola("Mascella", (0, -0.47, -0.47), (1.02, 0.6, 0.34), rot=(-8, 0, 0), mat=vern_chiara, gen=testa, bevel=0.035, rastrema=(1.08, 0.88)), livelli=3, crateri=imp[2:])
    scatola("Bocca_fondo", (0, -0.74, -0.46), (0.56, 0.03, 0.2), mat=bocca, gen=testa, bevel=0)
    for i in range(6):
        scatola(f"Griglia_{i}", (0, -0.79, -0.385 - i * 0.032), (0.62, 0.05, 0.016), mat=acciaio, gen=testa, bevel=0.004)
    # collo: cilindro, pistoni, cavi
    cilindro("Collo", (0, 0.35, -0.78), 0.42, 0.55, "Z", scuro, testa, bevel=0.01)
    for s in (-1, 1):
        cilindro(f"Pistone_{s}", (s * 0.42, 0.0, -0.78), 0.05, 0.6, "Z", acciaio, testa, bevel=0.006, rot_extra=(12, 0, 0))
        cilindro(f"Pistone_canna_{s}", (s * 0.42, 0.06, -0.98), 0.075, 0.32, "Z", scuro, testa, bevel=0.006, rot_extra=(12, 0, 0))
    for i, x in enumerate((-0.22, -0.08, 0.1, 0.24)):
        cu = bpy.data.curves.new(f"Cavo_{i}", "CURVE")
        cu.dimensions, cu.bevel_depth, cu.bevel_resolution = "3D", 0.028, 4
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for p, co in zip(sp.bezier_points, ((x, -0.15, -0.55), (x * 1.3, -0.25, -0.85), (x * 0.9, 0.05, -1.15))):
            p.co, p.handle_left_type, p.handle_right_type = co, "AUTO", "AUTO"
        oc = bpy.data.objects.new(f"Cavo_{i}", cu)
        sc.collection.objects.link(oc)
        oc.data.materials.append(gomma)
        oc.parent = testa

    # occhio: buca nella faccia e nella fronte, ghiera, anelli, lamelle, nucleo, vetro
    E = Vector((0, -0.70, 0.10))
    taglio = cilindro("Taglio_occhio", E, 0.335, 0.8, "Y", None, testa, bevel=0)
    buca(faccia, taglio)
    buca(fronte, taglio)
    oc = bpy.data.objects.new("Occhio", None)
    sc.collection.objects.link(oc)
    oc.parent, oc.location = testa, E
    ghiera = cilindro("Ghiera", E + Vector((0, -0.04, 0)), 0.40, 0.16, "Y", acciaio, testa, lati=64, bevel=0.012)
    taglio2 = cilindro("Taglio_ghiera", E, 0.305, 0.6, "Y", None, testa, bevel=0)
    buca(ghiera, taglio2)
    cilindro("Fondo_occhio", E + Vector((0, 0.16, 0)), 0.31, 0.04, "Y", scuro, testa, bevel=0)
    for k, (R, dy) in enumerate(((0.27, 0.10), (0.20, 0.07), (0.13, 0.04)), 1):
        a = toro(f"Anello_{k}", E + Vector((0, dy, 0)), R, 0.010 if k > 1 else 0.014, occhio, testa)
        a.rotation_euler = Euler((0, math.radians(k * 17), 0))
    for i in range(10):  # iride a lamelle, socchiusa
        ang = 2 * math.pi * i / 10
        bl = scatola(f"Iride_{i}", E + Vector((0.20 * math.cos(ang), -0.01, 0.20 * math.sin(ang))), (0.17, 0.008, 0.07),
                     rot=(0, -math.degrees(ang) - 70, 0), mat=scuro, gen=testa, bevel=0.003)
    sfera = bpy.data.meshes.new("Nucleo")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.065)
    bm.to_mesh(sfera)
    bm.free()
    no = oggetto("Nucleo", sfera, nucleo, testa)
    no.location = E + Vector((0, 0.05, 0))
    cilindro("Vetro_occhio", E + Vector((0, -0.10, 0)), 0.31, 0.012, "Y", vetro, testa, lati=64, bevel=0.003)
    for i in range(8):
        ang = 2 * math.pi * (i + 0.5) / 8
        bullone(E + Vector((0.355 * math.cos(ang), -0.125, 0.355 * math.sin(ang))), (0, 0, 0), acciaio, testa, r=0.022)
    for s in (-1, 1):
        for j in range(3):
            bullone((s * 0.86, -0.76, 0.28 - j * 0.24), (0, 0, s * 20), acciaio, testa)
    for x in (-0.72, -0.38, 0.38):
        bullone((x, -0.80, 0.56), (14, 0, 0), acciaio, testa, r=0.024)
    # bullone mancante: resta il foro filettato, scuro e arrugginito
    foro = materiale_semplice("Mat_Foro", (0.05, 0.018, 0.006), 0.2, 0.9)
    cilindro("Foro_bullone", (0.72, -0.787, 0.56), 0.016, 0.03, "Y", foro, testa, lati=16, bevel=0, rot_extra=(14, 0, 0))
    saldatura = materiale_vernice("Mat_Saldatura", (0.05, 0.045, 0.04), (0.09, 0.07, 0.05), forza_ruggine=2.0, ao=False)
    for nome, punti in (("Saldatura_L", [(-0.575, -0.80, -0.28), (-0.58, -0.81, 0.05), (-0.575, -0.80, 0.36)]),
                        ("Saldatura_M", [(-0.42, -0.775, -0.305), (0.0, -0.785, -0.31), (0.42, -0.775, -0.305)])):
        cu = bpy.data.curves.new(nome, "CURVE")
        cu.dimensions, cu.bevel_depth, cu.bevel_resolution = "3D", 0.011, 3
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(punti) - 1)
        for p, co in zip(sp.bezier_points, punti):
            p.co, p.handle_left_type, p.handle_right_type = co, "AUTO", "AUTO"
        os_ = bpy.data.objects.new(nome, cu)
        sc.collection.objects.link(os_)
        os_.data.materials.append(saldatura)
        os_.parent = testa
        cu.resolution_u = 64  # il cordone irregolare lo fa la normale del materiale

    # scritte consumate (sulla fronte e sulla guancia)
    testo("Stencil_NEXO", "NEXO SRL", (0, -0.2125, 0.06), (90, 0, 0), 0.15, stencil, fronte)
    testo("Stencil_NX", "NX-7472", (0.0, -0.3125, -0.24), (90, 0, 0), 0.065, stencil, guance[1])
    testo("Stencil_CAL", "CAL.07", (0.0, -0.3125, -0.24), (90, 0, 0), 0.05, stencil, guance[0])

    # luce: chiave fredda, controluce calda, schiarita debole, il blu dell'occhio, pannelli di riflesso
    def luce(nome, tipo, pos, energia, colore, misura=1.0, mira=(0, -0.4, 0.1)):
        L = bpy.data.lights.new(nome, tipo)
        L.energy, L.color = energia, colore
        if tipo == "AREA":
            L.size = misura
        o = bpy.data.objects.new(nome, L)
        o.visible_camera = False  # le luci non devono comparire nell'immagine
        sc.collection.objects.link(o)
        o.location = pos
        d = Vector(mira) - Vector(pos)
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return o
    luce("Chiave", "AREA", (-3.2, -4.2, 3.6), 300, (0.85, 0.92, 1.0), 2.0)
    luce("Controluce", "AREA", (3.6, 2.4, 1.6), 520, (1.0, 0.80, 0.62), 0.8)
    luce("Schiarita", "AREA", (3.5, -3.5, -0.6), 35, (0.7, 0.8, 1.0), 3.0)
    luce("Bordo_alto", "AREA", (0, 1.5, 3.8), 260, (0.8, 0.88, 1.0), 2.0)
    luce("Luce_occhio", "POINT", (0, -1.05, 0.10), 24, BLU).data.shadow_soft_size = 0.2

    w = bpy.data.worlds.new("Mondo")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.004, 0.006, 0.009, 1)
    bg.inputs[1].default_value = 1.0
    # pavimento appena visibile per un po' di profondità
    luce("Radente_parete", "AREA", (0.0, 1.0, 3.0), 170, (0.95, 0.9, 0.85), 4.0, mira=(0, 1.6, -0.6))
    luce("Radente_lato", "AREA", (-4.0, 1.2, 0.3), 120, (0.75, 0.85, 1.0), 2.0, mira=(0, 1.6, 0.3))

    parete(sc, materiale_vernice("Mat_Parete", (0.016, 0.017, 0.018), (0.026, 0.024, 0.021), forza_ruggine=2.2, colate=True, ao=False),
           materiale_vernice("Mat_Rivetti", (0.06, 0.058, 0.055), (0.08, 0.075, 0.07), forza_ruggine=2.0, ao=False))
    if False:  # vecchio fondale scuro, sostituito dalla parete
        pass
    # alone freddo dietro la testa (sfondo da studio, non piatto)
    fondo = materiale_semplice("Mat_Fondo", (0, 0, 0), 0, 1, (0.03, 0.07, 0.12), 1.0)
    N = Nodi(fondo)
    em = N.n("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.05, 0.11, 0.2, 1)
    grad = N.n("ShaderNodeTexGradient", gradient_type="SPHERICAL")
    mp = N.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.16, 0.16, 0.16)
    N.l(N.n("ShaderNodeTexCoord").outputs["Object"], mp.inputs["Vector"])
    N.l(mp.outputs[0], grad.inputs["Vector"])
    N.l(N.mat("POWER", grad.outputs["Fac"], 2.2), em.inputs["Strength"])
    N.l(em.outputs[0], N.out.inputs[0])

    cam = bpy.data.cameras.new("Camera")
    cam.lens = 70
    cam.dof.use_dof = True
    cam.dof.aperture_fstop = 5.6
    co = bpy.data.objects.new("Camera", cam)
    sc.collection.objects.link(co)
    co.location = (1.55, -5.55, -0.05)
    bersaglio = Vector((0.08, -0.5, 0.06))
    co.rotation_euler = (bersaglio - co.location).to_track_quat("-Z", "Y").to_euler()
    cam.dof.focus_object = oc
    sc.camera = co
    return sc


def renderizza(sc, file, campioni, larghezza, post=True):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = campioni
    sc.cycles.adaptive_threshold = 0.04
    sc.cycles.max_bounces, sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces = 6, 2, 3
    sc.cycles.transmission_bounces, sc.cycles.transparent_max_bounces = 4, 8
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.render.resolution_x = larghezza
    sc.render.resolution_y = int(larghezza * 0.5625)  # 16:9, come uno schermo
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = file
    bpy.ops.render.render(write_still=True)
    if not post:  # strati per la dashboard: alone, vignettatura e grana li fa lo shader
        return
    try:  # alone sui punti luminosi, come il "glare" del compositore
        from PIL import Image, ImageChops, ImageFilter
        im = Image.open(file).convert("RGB")
        luce = im.point(lambda v: 0 if v < 205 else min(255, (v - 205) * 5))
        alone = luce.filter(ImageFilter.GaussianBlur(larghezza / 60)).point(lambda v: int(v * 0.85))
        im = ImageChops.add(im, alone)
        # vignettatura: bordi più scuri, come un obiettivo vero
        w, h = im.size
        mask = Image.radial_gradient("L").resize((w, h)).point(lambda v: int(255 - min(255, max(0, (v - 120) * 1.6))))
        nero = Image.new("RGB", (w, h), (0, 0, 0))
        Image.composite(im, nero, mask.filter(ImageFilter.GaussianBlur(w / 20))).save(file)
    except ImportError:
        pass


if __name__ == "__main__":
    a = argomenti()
    import os
    os.makedirs(a.uscita, exist_ok=True)
    sc = costruisci(a.variante)
    base = os.path.join(a.uscita, f"sentinel-{a.variante}")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(base + ".blend"))
    renderizza(sc, os.path.abspath(base + ".png"), a.campioni, a.larghezza)
    print("FATTO", base + ".png")
