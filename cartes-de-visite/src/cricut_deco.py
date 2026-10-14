#!/usr/bin/env python3
"""Carte verticale D1 (capitales) + petits décors géométriques, pour la Cricut.

Usage : python3 cricut_deco.py <dossier_sortie>

  E1_trace-regulateur : lignes de construction du monogramme (épure de logo)
  E2_relief           : ombre hachurée décalée, monogramme en trompe-l'œil
  E3_cube-necker      : cube en fil de fer (illusion d'optique) au centre du filet
  E4_rosace           : rosace de compas à six pétales au centre du filet
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_lib import GEL, Carte, arc_pts, render_png  # noqa: E402
from cricut_styles import nom_capitales, signature       # noqa: E402


def _mm(x0, y0, w):
    s = w / 100.0
    return s, (lambda x, y: (x0 + x * s, y0 + y * s))


def _pointilles_arc(c, layer, cx, cy, r, a0, a1, trait=9, vide=7):
    a = a0
    while a < a1:
        b = min(a + trait, a1)
        c.poly(layer, arc_pts(cx, cy, r, a, b, 6))
        a = b + vide


def _pointilles(c, layer, p0, p1, trait=0.9, vide=0.6):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    t = 0.0
    while t < L:
        b = min(t + trait, L)
        c.ligne(layer, (x0 + ux * t, y0 + uy * t), (x0 + ux * b, y0 + uy * b))
        t = b + vide


# ------------------------------------------------------------------ E1
def trace_regulateur(c, x0, y0, w):
    s, P = _mm(x0, y0, w)
    # cercle complet de la boucle du J (moitié haute en pointillés)
    cx, cy = P(25.4, 67.5)
    _pointilles_arc(c, "bleu", cx, cy, 25.4 * s, 180, 360)
    # les deux diagonales prolongées jusqu'aux coins bas : le monogramme s'inscrit dans un X
    jx, jy = P(50.8, 46.6)
    _pointilles(c, "bleu", (jx, jy), P(100, 93))
    _pointilles(c, "bleu", (jx, jy), P(0, 93))
    # cadre d'encombrement : croix de coin, comme le cadre de plan de la carte imprimée
    o = 1.6
    for (x, y) in ((0, 0), (100, 0), (0, 93), (100, 93)):
        px, py = P(x, y)
        sx = -1 if x == 0 else 1
        sy = -1 if y == 0 else 1
        c.ligne("bleu", (px + sx * o, py), (px + sx * 0.5, py))
        c.ligne("bleu", (px, py + sy * o), (px, py + sy * 0.5))
    # axe horizontal en trait mixte passant par la jonction
    xa, xb = P(0, 0)[0] - 3.0, P(100, 0)[0] + 3.0
    c.axe("bleu", (xa, jy), (P(0, 0)[0] - 0.6, jy), long_=1.6)
    c.axe("bleu", (P(100, 0)[0] + 0.6, jy), (xb, jy), long_=1.6)


# ------------------------------------------------------------------ E2
def relief(c, x0, y0, w, d=(0.95, 0.95), pas=0.95):
    """Ombre portée hachurée à 45° : le monogramme semble posé en relief sur la carte."""
    s, P = _mm(x0, y0, w)
    dx, dy = d
    for poly in Carte.mono_polys():
        pts = [P(*q) for q in poly]
        reste = 0.0
        dn = math.hypot(dx, dy)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            L = math.hypot(bx - ax, by - ay)
            # trait presque parallèle à l'ombre : ombre quasi nulle, et les hachures
            # recouvriraient le trait du monogramme -> pas de hachures
            if L < 1e-9:
                continue
            if abs((bx - ax) * dy - (by - ay) * dx) / (L * dn) < 0.35:
                reste = 0.0
                continue
            t = reste
            while t < L:
                px, py = ax + (bx - ax) * t / L, ay + (by - ay) * t / L
                c.ligne("bleu", (px + dx * 0.42, py + dy * 0.42), (px + dx, py + dy))
                t += pas
            reste = t - L


# ------------------------------------------------------------------ E3 / E4 (ornements)
def orn_necker(c, cx, cy, a=2.5, k=1.05):
    """Cube de Necker : deux carrés décalés reliés aux coins (on ne sait pas lequel est devant)."""
    fx, fy = cx - (a + k) / 2, cy - a / 2 + k / 2
    front = [(fx, fy), (fx + a, fy), (fx + a, fy + a), (fx, fy + a), (fx, fy)]
    back = [(x + k, y - k) for x, y in front]
    c.poly("bleu", front)
    c.poly("bleu", back)
    for (x, y) in front[:4]:
        c.ligne("bleu", (x, y), (x + k, y - k))
    return (a + k) / 2 + 1.1


def orn_rosace(c, cx, cy, R=2.55):
    """Rosace de compas : cercle + six pétales tracés au même rayon."""
    c.cercle("bleu", cx, cy, R, 40)
    for k in range(6):
        a = math.radians(60 * k)
        px, py = cx + R * math.cos(a), cy + R * math.sin(a)
        base = 60 * k + 180
        c.poly("bleu", arc_pts(px, py, R, base - 60, base + 60, 16))
    return R + 1.1


DECORS = [
    ("E1_trace-regulateur", dict(deco=trace_regulateur)),
    ("E2_relief", dict(deco=relief)),
    ("E3_cube-necker", dict(ornement=orn_necker)),
    ("E4_rosace", dict(ornement=orn_rosace)),
]

if __name__ == "__main__":
    OUT = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    cartes = []
    for name, kw in DECORS:
        c = signature(nom_capitales, **kw)
        c.check()
        (OUT / f"carte_cricut_{name}.svg").write_text(c.svg(), encoding="utf-8")
        cartes.append(c)
        print(name, {k: len(v) for k, v in c.layers.items()})
    render_png([[c.svg(paper="#FBFAF6", preview=True) for c in cartes],
                [c.svg(pens=GEL, paper="#1C1F24", preview=True) for c in cartes]],
               OUT / "apercu_E_decors.png", page_w=4 * 55 + 30, page_h=2 * 85 + 20)
