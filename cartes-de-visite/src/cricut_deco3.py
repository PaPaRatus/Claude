#!/usr/bin/env python3
"""Carte D1 + monogramme en relief hachuré + 10 ornements de périphérie.

Usage : python3 cricut_deco3.py <dossier_sortie>
La structure de la carte ne change pas : les décors n'occupent que les marges.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_lib import GEL, Carte, arc_pts, render_png   # noqa: E402
from cricut_styles import nom_capitales, signature        # noqa: E402
from cricut_deco import relief                            # noqa: E402

W, H = 55.0, 85.0


# ------------------------------------------------------------------ outils
def rrect(x, y, w, h, r, n=12):
    if r <= 0:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    pts = []
    for (cx, cy, a0) in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0),
                         (x + r, y + h - r, 90), (x + r, y + r, 180)):
        pts += arc_pts(cx, cy, r, a0, a0 + 90, n)
    return pts + [pts[0]]


def cadre(c, i, r=1.6, layer="bleu"):
    c.poly(layer, rrect(i, i, W - 2 * i, H - 2 * i, r))


def hachurer(c, layer, polys, angle=45, pas=0.9):
    """Hachures parallèles remplissant des polygones fermés (règle pair-impair : les anneaux marchent)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    edges = [(p[i], p[i + 1]) for p in polys for i in range(len(p) - 1)]
    ks = [x * nx + y * ny for p in polys for x, y in p]
    k = min(ks) + pas / 2
    while k < max(ks):
        ts = []
        for (x1, y1), (x2, y2) in edges:
            d1, d2 = x1 * nx + y1 * ny - k, x2 * nx + y2 * ny - k
            if (d1 < 0) != (d2 < 0):
                lam = d1 / (d1 - d2)
                px, py = x1 + (x2 - x1) * lam, y1 + (y2 - y1) * lam
                ts.append(px * ux + py * uy)
        ts.sort()
        for t0, t1 in zip(ts[0::2], ts[1::2]):
            c.ligne(layer, (nx * k + ux * t0, ny * k + uy * t0), (nx * k + ux * t1, ny * k + uy * t1))
        k += pas


def texte_tourne(c, s, x, y, cap, layer, angle):
    """Texte centré sur (x, y) puis tourné de `angle` degrés autour de ce point."""
    tmp = Carte(W, H)
    tmp.texte(s, 0, cap / 2, cap, layer, anchor="middle")
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    for p in tmp.layers[layer]:
        c.poly(layer, [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in p])


def fleche(c, layer, tip, direction, L=1.2, ang=18):
    dx, dy = direction
    a0 = math.atan2(-dy, -dx)
    for da in (ang, -ang):
        a = a0 + math.radians(da)
        c.ligne(layer, tip, (tip[0] + L * math.cos(a), tip[1] + L * math.sin(a)))


def resample(poly, step):
    out, cum = [poly[0]], [0.0]
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        L = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(L / step))
        for i in range(1, n + 1):
            out.append((x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n))
            cum.append(cum[-1] + L / n)
    return out, cum


# ------------------------------------------------------------------ 10 ornements
def g01_coins_hachures(c):
    cadre(c, 3.0)
    L, o = 6.5, 3.9
    x0, y0, x1, y1 = o, o, W - o, H - o
    for tri, ang in (([(x0, y0), (x0 + L, y0), (x0, y0 + L)], 135),
                     ([(x1, y0), (x1, y0 + L), (x1 - L, y0)], 45),
                     ([(x1, y1), (x1 - L, y1), (x1, y1 - L)], 135),
                     ([(x0, y1), (x0, y1 - L), (x0 + L, y1)], 45)):
        c.poly("bleu", [tri[1], tri[2]])
        hachurer(c, "bleu", [tri + [tri[0]]], ang, 0.85)


def g02_bordure_hachuree(c):
    ext = rrect(2.7, 2.7, W - 5.4, H - 5.4, 2.0)
    inn = rrect(4.3, 4.3, W - 8.6, H - 8.6, 0.8)
    c.poly("bleu", ext)
    c.poly("bleu", inn)
    hachurer(c, "bleu", [ext, inn], 45, 1.05)


def g03_regle(c):
    i = 3.0
    c.ligne("bleu", (i, H - 8.0), (i, i), (W - 8.0, i))
    for k in range(4, int(H - 8.0 - i) + 1):
        L = 1.9 if k % 10 == 0 else (1.25 if k % 5 == 0 else 0.7)
        c.ligne("bleu", (i, i + k), (i + L, i + k))
    for k in range(4, int(W - 8.0 - i) + 1):
        L = 1.9 if k % 10 == 0 else (1.25 if k % 5 == 0 else 0.7)
        c.ligne("bleu", (i + k, i), (i + k, i + L))


def g04_cotations(c):
    # largeur 55 en haut, hauteur 85 à droite : les vraies cotes de la carte
    y, xa, xb = 4.4, 3.0, 52.0
    c.ligne("bleu", (xa, y - 1.1), (xa, y + 1.1))
    c.ligne("bleu", (xb, y - 1.1), (xb, y + 1.1))
    c.ligne("bleu", (xa, y), (W / 2 - 2.4, y))
    c.ligne("bleu", (W / 2 + 2.4, y), (xb, y))
    fleche(c, "bleu", (xa, y), (-1, 0))
    fleche(c, "bleu", (xb, y), (1, 0))
    c.texte("55", W / 2, y + 0.8, 1.6, "bleu", ls=0.2, anchor="middle")
    x, ya, yb = 51.2, 7.5, 82.0
    c.ligne("bleu", (x - 1.1, yb), (x + 1.1, yb))
    c.ligne("bleu", (x, ya), (x, H / 2 - 2.4))
    c.ligne("bleu", (x, H / 2 + 2.4), (x, yb))
    fleche(c, "bleu", (x, yb), (0, 1))
    fleche(c, "bleu", (x, ya), (0, -1))
    texte_tourne(c, "85", x, H / 2, 1.6, "bleu", -90)


def g05_eventails(c):
    for (cx, cy, a0) in ((3.0, 3.0, 0), (W - 3.0, 3.0, 90), (W - 3.0, H - 3.0, 180), (3.0, H - 3.0, 270)):
        for r in (1.6, 2.7, 3.8):
            c.poly("bleu", arc_pts(cx, cy, r, a0, a0 + 90, 12))
        for da in (30, 60):
            a = math.radians(a0 + da)
            c.ligne("bleu", (cx + 1.6 * math.cos(a), cy + 1.6 * math.sin(a)),
                    (cx + 3.8 * math.cos(a), cy + 3.8 * math.sin(a)))


def g06_grille_iso(c):
    L = 10.0
    for tri in ([(W - 3.0, 3.0), (W - 3.0 - L, 3.0), (W - 3.0, 3.0 + L)],
                [(3.0, H - 3.0), (3.0, H - 3.0 - L), (3.0 + L, H - 3.0)]):
        poly = tri + [tri[0]]
        c.poly("bleu", poly)
        for ang in (0, 60, 120):
            hachurer(c, "bleu", [poly], ang, 1.7)


def g07_guilloche(c):
    base = rrect(3.6, 3.6, W - 7.2, H - 7.2, 2.2, 24)
    pts, cum = resample(base, 0.2)
    P = cum[-1]
    lam = P / round(P / 3.2)
    A = 0.6
    for phase in (0, math.pi):
        out = []
        for i, (x, y) in enumerate(pts):
            j0, j1 = max(0, i - 1), min(len(pts) - 1, i + 1)
            tx, ty = pts[j1][0] - pts[j0][0], pts[j1][1] - pts[j0][1]
            n = math.hypot(tx, ty) or 1
            nx, ny = -ty / n, tx / n
            o = A * math.sin(2 * math.pi * cum[i] / lam + phase)
            out.append((x + nx * o, y + ny * o))
        c.poly("bleu", out)


def g08_rapporteur(c):
    """Arc gradué façon rapporteur, centré sous le monogramme (130° d'ouverture)."""
    cx, cy, r = 27.5, 30.0, 25.0
    c.poly("bleu", arc_pts(cx, cy, r, 205, 335, 80))
    for ang in range(205, 336, 5):
        d = ang - 270
        L = 1.5 if d % 30 == 0 else (1.0 if d % 10 == 0 else 0.55)
        a = math.radians(ang)
        c.ligne("bleu", (cx + r * math.cos(a), cy + r * math.sin(a)),
                (cx + (r + L) * math.cos(a), cy + (r + L) * math.sin(a)))


def g09_certificat(c):
    i, s = 4.2, 2.6
    h = s / 2
    centres = [(i, i), (W - i, i), (W - i, H - i), (i, H - i)]
    for (x, y) in centres:
        c.rect("bleu", x - h, y - h, s, s)
        c.poly("bleu", [(x, y - h + 0.45), (x + h - 0.45, y), (x, y + h - 0.45), (x - h + 0.45, y), (x, y - h + 0.45)])
    c.ligne("bleu", (i + h, i), (W - i - h, i))
    c.ligne("bleu", (i + h, H - i), (W - i - h, H - i))
    c.ligne("bleu", (i, i + h), (i, H - i - h))
    c.ligne("bleu", (W - i, i + h), (W - i, H - i - h))


def g10_plaque_vissee(c):
    cadre(c, 3.0)
    r, d = 1.25, 6.1
    for (x, y), ang in (((d, d), 25), ((W - d, d), 80), ((W - d, H - d), -35), ((d, H - d), 55)):
        c.cercle("bleu", x, y, r, 28)
        a = math.radians(ang)
        k = r - 0.25
        c.ligne("bleu", (x - k * math.cos(a), y - k * math.sin(a)), (x + k * math.cos(a), y + k * math.sin(a)))


ORNEMENTS = [
    ("G01_coins-hachures", g01_coins_hachures), ("G02_bordure-hachuree", g02_bordure_hachuree),
    ("G03_regle-graduee", g03_regle), ("G04_cotations", g04_cotations),
    ("G05_coins-eventail", g05_eventails), ("G06_grille-isometrique", g06_grille_iso),
    ("G07_lisere-guilloche", g07_guilloche), ("G08_rapporteur", g08_rapporteur),
    ("G09_cadre-certificat", g09_certificat), ("G10_plaque-vissee", g10_plaque_vissee),
]


def carte(fn):
    c = signature(nom_capitales, deco=relief)
    fn(c)
    return c


if __name__ == "__main__":
    OUT = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    cartes = []
    for name, fn in ORNEMENTS:
        c = carte(fn)
        c.check()
        (OUT / f"carte_cricut_{name}.svg").write_text(c.svg(), encoding="utf-8")
        cartes.append(c)
        print(name, len(c.layers["bleu"]), "tracés bleus")
    for suffix, kw in (("", dict(paper="#FBFAF6")), ("_papier-noir", dict(pens=GEL, paper="#1C1F24"))):
        render_png([[c.svg(preview=True, **kw) for c in cartes[:5]],
                    [c.svg(preview=True, **kw) for c in cartes[5:]]],
                   OUT / f"apercu_G_ornements{suffix}.png", page_w=5 * 55 + 4 * 6 + 16, page_h=2 * 85 + 22)
