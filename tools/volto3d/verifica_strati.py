"""Verifica degli strati del volto per la dashboard (vedi strati.py).

Uso:  python tools/volto3d/verifica_strati.py [guardian-web/public/volto]
Controlla: file presenti, dimensioni coerenti con meta.json, pesi nel budget (≤ 2,5 MB desktop, ≤ 0,8 MB telefono),
meta valido e, se c'è il render acceso in _tmp/, che base + luce lo ricomponga (errore medio < 3%).
"""
import json
import os
import sys

from PIL import Image

STRATI = ["base", "luce", "anelli", "bocca", "iride", "profondita"]


def main(cartella):
    errori = []
    ok = lambda c, m: print(("OK   " if c else "FAIL ") + m) or (None if c else errori.append(m))  # noqa: E731
    meta = json.load(open(os.path.join(cartella, "meta.json")))
    W, H = meta["larghezza"], meta["altezza"]
    for sotto, budget in (("", 2.5), ("960", 0.8)):
        dir_ = os.path.join(cartella, sotto)
        mancanti = [s for s in STRATI if not os.path.exists(os.path.join(dir_, f"{s}.webp"))]
        ok(not mancanti, f"strati {'desktop' if not sotto else 'telefono'} presenti {mancanti or ''}")
        if mancanti:
            continue
        peso = sum(os.path.getsize(os.path.join(dir_, f"{s}.webp")) for s in STRATI) / 1e6
        ok(peso <= budget, f"peso {'desktop' if not sotto else 'telefono'} {peso:.2f} MB (budget {budget} MB)")
        b = Image.open(os.path.join(dir_, "base.webp"))
        atteso = (W, H) if not sotto else (960, round(960 * H / W))
        ok(abs(b.width - atteso[0]) <= 1 and abs(b.height - atteso[1]) <= 1, f"base {b.size} = {atteso}")
    c = meta["occhio"]["centro"]
    ok(0 < c[0] < W and 0 < c[1] < H, f"occhio dentro l'immagine {[round(v) for v in c]}")
    x, y, w, h = meta["iride"]["rettangolo"]
    ok(0 <= x and 0 <= y and x + w <= W and y + h <= H and w > 50, "rettangolo dell'iride valido")
    acceso = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_strati", "acceso.png")
    if os.path.exists(acceso):
        import numpy as np
        a = np.asarray(Image.open(acceso).convert("RGB"), dtype=np.float32)
        base = np.asarray(Image.open(os.path.join(cartella, "base.webp")).convert("RGB"), dtype=np.float32)
        luce = np.asarray(Image.open(os.path.join(cartella, "luce.webp")).convert("RGB").resize((W, H)), dtype=np.float32)
        err = float(np.mean(np.abs(np.clip(base + luce, 0, 255) - a)) / 255)
        ok(err < 0.03, f"base + luce ricompone il volto acceso (errore medio {err * 100:.1f}%)")
    print("FALLITI: " + "; ".join(errori) if errori else "Strati: tutti i controlli superati")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "guardian-web/public/volto"))
