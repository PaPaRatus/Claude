#!/usr/bin/env python3
"""Carte D1 (capitales) : ornements à la place du losange, cadres, version paysage.

Usage : python3 cricut_deco2.py <dossier_sortie>
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_lib import GEL, Carte, arc_pts, render_png       # noqa: E402
from cricut_styles import MAIL, TEL, nom_capitales, orn_losange, signature  # noqa: E402
from cricut_deco import orn_necker, orn_rosace                # noqa: E402


# ------------------------------------------------------------------ ornements
def orn_cube(c, cx, cy, R=1.95):
    """Cube isométrique vu de dessus : hexagone + Y."""
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
           for a in (-90, -30, 30, 90, 150, 210, 270)]
    c.poly("bleu", pts)
    for a in (90, 210, 330):
        c.ligne("bleu", (cx, cy), (cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))))
    return R * math.cos(math.radians(30)) + 1.1


def orn_ecrou(c, cx, cy, R=2.3):
    """Écrou vu de dessus : hexagone à plats horizontaux + alésage."""
    c.poly("bleu", [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
                    for a in range(0, 361, 60)])
    c.cercle("bleu", cx, cy, 0.95, 24)
    return R + 0.9


def orn_mire(c, cx, cy, r=1.55):
    """Repère de centre (perçage) : cercle, croix centrale, axes qui débordent."""
    c.cercle("bleu", cx, cy, r, 36)
    c.ligne("bleu", (cx - 0.7, cy), (cx + 0.7, cy))
    c.ligne("bleu", (cx, cy - 0.7), (cx, cy + 0.7))
    c.ligne("bleu", (cx, cy - r - 0.45), (cx, cy - r - 0.95))
    c.ligne("bleu", (cx, cy + r + 0.45), (cx, cy + r + 0.95))
    return r + 0.5


def orn_projection(c, cx, cy):
    """Symbole de projection européenne (1er dièdre) : vue de face du tronc de cône, vue de gauche à droite."""
    L, h1, h2, gap, = 3.0, 0.8, 1.5, 1.7
    x0 = cx - (L + gap + 2 * h2) / 2
    c.poly("bleu", [(x0, cy - h1), (x0 + L, cy - h2), (x0 + L, cy + h2), (x0, cy + h1), (x0, cy - h1)])
    ccx = x0 + L + gap + h2
    c.cercle("bleu", ccx, cy, h2, 36)
    c.cercle("bleu", ccx, cy, h1, 24)
    c.ligne("bleu", (ccx, cy - h2 - 0.6), (ccx, cy + h2 + 0.6))
    # axe commun (petits traits) entre les deux vues
    c.ligne("bleu", (x0 + L + 0.4, cy), (x0 + L + gap - 0.4, cy))
    return (L + gap + 2 * h2) / 2 + 0.9


# ------------------------------------------------------------------ cadres
def _rrect(x, y, w, h, r, n=10):
    pts = []
    for (cx, cy, a0) in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0),
                         (x + r, y + h - r, 90), (x + r, y + r, 180)):
        pts += arc_pts(cx, cy, r, a0, a0 + 90, n)
    return pts + [pts[0]]


def cadre_simple(c, i=3.0, r=1.6, layer="bleu"):
    c.poly(layer, _rrect(i, i, c.w - 2 * i, c.h - 2 * i, r))


def cadre_double(c):
    cadre_simple(c, 2.7, 1.9)
    cadre_simple(c, 3.6, 1.1)


def cadre_deco(c, i=3.0, r=2.2):
    """Coins rentrants (quart de cercle concave), esprit Art déco."""
    x0, y0, x1, y1 = i, i, c.w - i, c.h - i
    pts = []
    for (cx, cy, a0) in ((x1, y0, 180), (x1, y1, 270), (x0, y1, 0), (x0, y0, 90)):
        # arc concave centré sur le coin, parcouru dans le sens inverse
        pts += arc_pts(cx, cy, r, a0, a0 - 90, 10)
    c.poly("bleu", pts + [pts[0]])


def cadre_equerres(c, i=3.0, L=6.0, r=1.6):
    """Équerres de coin seules : le cadre est suggéré."""
    x0, y0, x1, y1 = i, i, c.w - i, c.h - i
    coins = [  # (bras vertical, centre de l'arc, angles, bras horizontal)
        ((x0, y0 + L), (x0 + r, y0 + r), 180, 270, (x0 + L, y0)),
        ((x1 - L, y0), (x1 - r, y0 + r), 270, 360, (x1, y0 + L)),
        ((x1, y1 - L), (x1 - r, y1 - r), 0, 90, (x1 - L, y1)),
        ((x0 + L, y1), (x0 + r, y1 - r), 90, 180, (x0, y1 - L)),
    ]
    for start, (cx, cy), a0, a1, end in coins:
        c.poly("bleu", [start] + arc_pts(cx, cy, r, a0, a1, 8) + [end])


def avec_cadre(fn_cadre, ornement=orn_losange):
    c = signature(nom_capitales, ornement=ornement)
    fn_cadre(c)
    return c


# ------------------------------------------------------------------ paysage
def paysage(ornement=orn_necker):
    c = Carte(85, 55)
    cadre_simple(c)
    cxl = 19.5
    mw = 18.5
    c.monogramme("accent", cxl - mw / 2, 9.6, mw)
    c.texte("MARTIN", cxl, 35.4, 3.5, "noir", ls=1.35, anchor="middle")
    c.texte("JULIEN", cxl, 39.9, 2.0, "bleu", ls=1.4, anchor="middle")
    # filet vertical avec l'ornement au centre
    xf, ym = 36.0, 27.5
    demi = ornement(c, xf, ym)
    c.ligne("bleu", (xf, 10.0), (xf, ym - demi))
    c.ligne("bleu", (xf, ym + demi), (xf, 45.0))
    X = 40.0
    for k, t in enumerate(("Bureau d’études TopSolid’Wood", "Impression 3D",
                           "Signalétique vinyle adhésif")):
        w = c.texte(t, X, 14.2 + k * 4.2, 1.95, "noir", ls=0.04, sx=0.88)
        assert X + w <= 81, (t, X + w)
    c.ligne("accent", (X, 26.6), (X + 4.0, 26.6))
    c.texte(TEL, X, 33.0, 2.4, "noir", ls=0.14)
    c.texte(MAIL, X, 37.6, 1.95, "noir", ls=0.03, sx=0.88)
    c.texte("MICRO-ENTREPRISE", X, 43.2, 1.45, "bleu", ls=0.55)
    return c


VARIANTES = [
    ("F01_orn-cube-necker", lambda: signature(nom_capitales, ornement=orn_necker)),
    ("F02_orn-rosace", lambda: signature(nom_capitales, ornement=orn_rosace)),
    ("F03_orn-cube-isometrique", lambda: signature(nom_capitales, ornement=orn_cube)),
    ("F04_orn-ecrou", lambda: signature(nom_capitales, ornement=orn_ecrou)),
    ("F05_orn-centre-percage", lambda: signature(nom_capitales, ornement=orn_mire)),
    ("F06_orn-symbole-projection", lambda: signature(nom_capitales, ornement=orn_projection)),
    ("F07_cadre-simple", lambda: avec_cadre(cadre_simple)),
    ("F08_cadre-double", lambda: avec_cadre(cadre_double)),
    ("F09_cadre-art-deco", lambda: avec_cadre(cadre_deco)),
    ("F10_cadre-equerres", lambda: avec_cadre(cadre_equerres)),
    ("F11_paysage-cadre-necker", paysage),
]

if __name__ == "__main__":
    OUT = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    cartes = []
    for name, fn in VARIANTES:
        c = fn()
        c.check()
        (OUT / f"carte_cricut_{name}.svg").write_text(c.svg(), encoding="utf-8")
        cartes.append(c)
    pv = lambda c, **k: c.svg(paper="#FBFAF6", preview=True, **k)
    render_png([[pv(c) for c in cartes[:6]], [pv(c) for c in cartes[6:]]],
               OUT / "apercu_F_propositions.png", page_w=6 * 55 + 5 * 6 + 16, page_h=2 * 85 + 22)
    render_png([[c.svg(pens=GEL, paper="#1C1F24", preview=True) for c in cartes[:6]],
                [c.svg(pens=GEL, paper="#1C1F24", preview=True) for c in cartes[6:]]],
               OUT / "apercu_F_propositions_papier-noir.png", page_w=6 * 55 + 5 * 6 + 16,
               page_h=2 * 85 + 22)
    print(len(cartes), "cartes")
