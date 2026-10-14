#!/usr/bin/env python3
"""Version finale affinée (H2 corrigée) + easter egg : une tentacule de poulpe sortant d'une équerre.

Usage : python3 cricut_poulpe.py <dossier_sortie>

  I1_finale              : H2 corrigée (monogramme recentré optiquement, marges équilibrées,
                           filet recentré, point superflu retiré), bicolore noir + bleu
  I2_finale_poulpe-bas   : I1 + tentacule enroulée dans le coin bas droit
  I3_finale_poulpe-haut  : I1 + tentacule enroulée dans le coin haut droit
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_lib import render_png                       # noqa: E402
from cricut_styles import nom_capitales, signature      # noqa: E402
from cricut_deco import relief                          # noqa: E402
from cricut_deco2 import cadre_equerres, orn_cube       # noqa: E402

DECALAGE_Y = -1.5      # remonte tout le contenu : marges haut / bas équilibrées (7,5 / 7,9 mm)
MONO_DX = -0.45        # l'ombre alourdit la droite du monogramme : recentrage optique


def finale():
    c = signature(nom_capitales, ornement=orn_cube, deco=relief, mono_dx=MONO_DX,
                  filet_y=46.4, point=False)
    c.layers["noir"] += c.layers["accent"]          # bicolore : monogramme au stylo noir
    c.layers["accent"] = []
    for polys in c.layers.values():
        for p in polys:
            p[:] = [(x, y + DECALAGE_Y) for x, y in p]
    cadre_equerres(c)                                # les équerres restent calées sur la découpe
    return c


def tentacule(c, base, cap, L=8.0, k0=0.05, k1=1.9, w0=1.4, sens=1, n=160, layer="bleu"):
    """Tentacule effilée qui s'enroule (courbure croissante), ventouses côté intérieur.
    La base reste ouverte : posée sous une équerre, la tentacule semble passer derrière."""
    x, y = base
    th = math.radians(cap)
    ds = L / n
    centre, normales, largeurs = [], [], []
    for i in range(n + 1):
        s = i * ds
        centre.append((x, y))
        normales.append((-math.sin(th), math.cos(th)))
        largeurs.append(w0 * (1 - s / L) ** 0.85 + 0.06)
        k = k0 + (k1 - k0) * (s / L) ** 2
        th += sens * k * ds
        x += math.cos(th) * ds
        y += math.sin(th) * ds
    gauche = [(px + nx * w / 2, py + ny * w / 2) for (px, py), (nx, ny), w in zip(centre, normales, largeurs)]
    droite = [(px - nx * w / 2, py - ny * w / 2) for (px, py), (nx, ny), w in zip(centre, normales, largeurs)]
    c.poly(layer, gauche + droite[::-1])
    # ventouses : petits cercles le long du bord intérieur de l'enroulement
    cote = sens
    s = 0.9
    while s < 0.78 * L:
        i = int(s / ds)
        (px, py), (nx, ny), w = centre[i], normales[i], largeurs[i]
        r = max(0.14, min(0.24, w * 0.17))
        off = cote * (w / 2 - r - 0.12)
        c.cercle(layer, px + nx * off, py + ny * off, r, 10)
        s += 0.95 if w > 0.7 else 0.75
    return gauche + droite


def poulpe_bas(c):
    """Sort du bras vertical de l'équerre bas droite et s'enroule vers le haut, dans le coin libre."""
    tentacule(c, (52.0, 78.2), 195, L=11.0, k0=0.10, k1=1.45, w0=1.5, sens=1)


def poulpe_haut(c):
    """Même tentacule, en miroir, sortant de l'équerre haut droite."""
    tentacule(c, (52.0, 6.6), 165, L=11.0, k0=0.10, k1=1.45, w0=1.5, sens=-1)


CARTES = [
    ("I1_finale", lambda: finale()),
    ("I2_finale_poulpe-bas", lambda: (lambda c: (poulpe_bas(c), c)[1])(finale())),
    ("I3_finale_poulpe-haut", lambda: (lambda c: (poulpe_haut(c), c)[1])(finale())),
]

if __name__ == "__main__":
    OUT = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    cartes = []
    for name, fn in CARTES:
        c = fn()
        c.check()
        (OUT / f"carte_cricut_{name}.svg").write_text(c.svg(), encoding="utf-8")
        cartes.append(c)
        print(name, {k: len(v) for k, v in c.layers.items()})
    render_png([[c.svg(paper="#FBFAF6", preview=True) for c in cartes]],
               OUT / "apercu_I_finale.png", page_w=3 * 55 + 2 * 6 + 16, page_h=85 + 14)
