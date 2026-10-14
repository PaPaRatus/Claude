#!/usr/bin/env python3
"""Trois styles supplémentaires de carte Cricut (stylos + découpe coins arrondis).

Usage : python3 cricut_styles.py <dossier_sortie>

  B_vue-en-coupe   : monogramme au centre d'une coupe hachurée, axes, « COUPE A-A »
  C_filaire-3D     : monogramme extrudé en filaire posé sur un plateau d'impression 3D
  D_signature      : format portrait, monogramme or, nom en écriture cursive
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_lib import GEL, Carte, render_png  # noqa: E402


TEL = "06 23 35 95 60"
MAIL = "martinjulien.be@gmail.com"


def icones(c, x, y_tel, y_mail):
    """Smartphone et enveloppe au trait ; y = ligne de base du texte associé."""
    c.rect("bleu", x + 0.5, y_tel - 2.65, 1.6, 2.65)
    c.ligne("bleu", (x + 1.05, y_tel - 0.55), (x + 1.55, y_tel - 0.55))
    c.rect("bleu", x, y_mail - 1.8, 2.7, 1.8)
    c.ligne("bleu", (x, y_mail - 1.8), (x + 1.35, y_mail - 0.75), (x + 2.7, y_mail - 1.8))


# ====================================================================== B
def vue_en_coupe():
    c = Carte(85, 55)
    cx, cy, ro, ri = 21.5, 25.5, 14.0, 9.6
    # hachures de coupe à 45° dans l'anneau (stylo or)
    sp = 1.15
    n = int(ro / sp)
    for i in range(-n, n + 1):
        off = i * sp
        if abs(off) >= ro:
            continue
        to = math.sqrt(ro * ro - off * off)
        bx, by = cx + off / math.sqrt(2), cy + off / math.sqrt(2)      # normale (1,1)
        ux, uy = 1 / math.sqrt(2), -1 / math.sqrt(2)                   # direction (1,-1)
        P = lambda t: (bx + ux * t, by + uy * t)
        if abs(off) < ri:
            ti = math.sqrt(ri * ri - off * off)
            c.ligne("accent", P(-to), P(-ti))
            c.ligne("accent", P(ti), P(to))
        else:
            c.ligne("accent", P(-to), P(to))
    c.cercle("noir", cx, cy, ro)
    c.cercle("noir", cx, cy, ri)
    # axes en trait mixte, interrompus dans l'alésage pour laisser respirer le monogramme
    e = ro + 3.0
    for sgn in (-1, 1):
        c.axe("bleu", (cx + sgn * (ri - 0.8), cy), (cx + sgn * e, cy), long_=2.2)
        c.axe("bleu", (cx, cy + sgn * (ri - 0.8)), (cx, cy + sgn * e), long_=2.2)
    # monogramme centré sur l'axe (sa jonction tombe au centre de la coupe)
    mw = 12.6
    s = mw / 100
    c.monogramme("noir", cx - 50.8 * s, cy - 46.6 * s, mw)
    c.texte("COUPE A-A", cx, cy + ro + 6.8, 1.6, "bleu", ls=0.55, anchor="middle")

    X, XR = 40.5, 81.0
    c.texte("JULIEN", X, 11.6, 1.9, "bleu", ls=0.9)
    c.texte("MARTIN", X, 18.0, 4.3, "noir", ls=1.05)
    c.texte("micro-entreprise", X, 21.9, 1.7, "bleu", ls=0.05, sx=0.92)
    c.ligne("noir", (X, 24.6), (XR, 24.6))
    for k, t in enumerate(("Bureau d’études TopSolid’Wood", "Impression 3D",
                           "Signalétique vinyle adhésif")):
        y = 29.0 + k * 3.9
        c.ligne("accent", (X, y - 0.75), (X + 1.4, y - 0.75))
        w = c.texte(t, X + 2.6, y, 1.85, "noir", ls=0.03, sx=0.86)
        assert X + 2.6 + w <= XR, t
    c.ligne("noir", (X, 40.0), (XR, 40.0))
    icones(c, X, 44.3, 48.6)
    c.texte(TEL, X + 4.4, 44.3, 2.2, "noir", ls=0.12)
    w = c.texte(MAIL, X + 4.4, 48.6, 1.9, "noir", ls=0.03, sx=0.86)
    assert X + 4.4 + w <= XR + 0.5, w
    return c


# ====================================================================== C
def filaire_3d():
    c = Carte(85, 55)
    mx, my, mw = 9.0, 10.8, 24.0
    s = mw / 100
    dx, dy = 3.0, -2.2                      # direction d'extrusion (profondeur)
    F = lambda x, y: (mx + x * s, my + y * s)
    B = lambda x, y: (mx + x * s + dx, my + y * s + dy)

    # plateau d'impression 3D (plan du sol) avec sa grille, derrière et devant le monogramme
    yb = my + 93 * s
    u0, u1, v0, v1 = mx - 1.0, mx + mw + 1.0, -1.5, 1.6
    Q = lambda u, v: (u + v * dx, yb + v * dy)
    c.poly("bleu", [Q(u0, v0), Q(u1, v0), Q(u1, v1), Q(u0, v1), Q(u0, v0)])
    # grille seulement devant les lettres (v <= 0) : l'arrière est masqué par le monogramme
    nu = 7
    for i in range(1, nu):
        u = u0 + (u1 - u0) * i / nu
        c.ligne("bleu", Q(u, v0), Q(u, 0))
    for j in (1, 2):
        v = v0 * j / 3
        c.ligne("bleu", Q(u0, v), Q(u1, v))
    c.ligne("bleu", Q(u0, 0), Q(u1, 0))

    # monogramme : face avant (noir), face arrière et arêtes de profondeur (bleu)
    for p in Carte.mono_polys():
        c.poly("bleu", [B(*q) for q in p])
    for x, y in ((0, 0), (50.8, 0), (50.8, 67.5), (0, 67.5), (50.8, 46.6), (100, 0), (100, 93)):
        c.ligne("bleu", F(x, y), B(x, y))
    phi = math.atan2(-dx, dy)               # point de la boucle où l'arête est tangente
    phi = phi if 0 <= phi <= math.pi else phi + math.pi
    sx_, sy_ = 25.4 + 25.4 * math.cos(phi), 67.5 + 25.4 * math.sin(phi)
    c.ligne("bleu", F(sx_, sy_), B(sx_, sy_))
    for p in Carte.mono_polys():
        c.poly("noir", [F(*q) for q in p])

    # trièdre XYZ façon CAO (or), coin haut droit
    ox, oy, L = 75.5, 11.0, 4.2
    def fleche(x1, y1, lab, lx, ly):
        c.ligne("accent", (ox, oy), (x1, y1))
        a = math.atan2(y1 - oy, x1 - ox)
        for da in (2.6, -2.6):
            c.ligne("accent", (x1, y1), (x1 - 1.0 * math.cos(a + da / 6), y1 - 1.0 * math.sin(a + da / 6)))
        c.texte(lab, lx, ly, 1.45, "accent", anchor="middle")
    fleche(ox + L, oy, "X", ox + L + 1.6, oy + 0.7)
    fleche(ox, oy - L, "Z", ox, oy - L - 1.0)
    fleche(ox - 0.75 * dx, oy - 0.75 * dy, "Y", ox - 0.75 * dx - 1.4, oy - 0.75 * dy + 1.9)

    cxl = mx + mw / 2 + 1.0
    c.texte("MARTIN", cxl, 44.2, 3.2, "noir", ls=1.0, anchor="middle")
    c.texte("JULIEN", cxl, 48.6, 1.95, "bleu", ls=1.05, anchor="middle")

    X, XR = 44.5, 80.0
    def cube(x, y, a=1.15):
        """Petit cube isométrique (puce or), y = ligne de base."""
        t = (x, y - 2.0)
        r = (x + a, y - 2.0 + a * 0.5)
        l = (x - a, y - 2.0 + a * 0.5)
        b = (x, y - 2.0 + a)
        c.poly("accent", [t, r, (r[0], r[1] + a), (b[0], b[1] + a), (l[0], l[1] + a), l, t])
        c.poly("accent", [l, b, r])
        c.ligne("accent", b, (b[0], b[1] + a))
    items = [("Bureau d’études", "TopSolid’Wood"), ("Impression 3D", None),
             ("Signalétique", "vinyle adhésif")]
    y = 17.6
    for t1, t2 in items:
        cube(X + 1.1, y)
        c.texte(t1, X + 3.6, y, 2.2, "noir", ls=0.06)
        if t2:
            c.texte(t2, X + 3.6, y + 3.0, 1.7, "bleu", ls=0.08)
            y += 3.0
        y += 4.9
    c.ligne("bleu", (X, 36.4), (XR, 36.4))
    icones(c, X, 40.8, 45.0)
    c.texte(TEL, X + 4.4, 40.8, 2.25, "noir", ls=0.12)
    w = c.texte(MAIL, X + 4.4, 45.0, 1.85, "noir", ls=0.03, sx=0.86)
    assert X + 4.4 + w <= XR + 1.0, w
    c.texte("micro-entreprise", X + 4.4, 49.2, 1.65, "bleu", ls=0.05, sx=0.92)
    return c


# ====================================================================== D
def _nom_ajuste(c, txt, cx, y, cap, font, ls, layer="noir", wmax=44.0):
    w = c.largeur(txt, cap, ls=ls, font=font)
    if w > wmax:
        cap *= wmax / w
    c.texte(txt, cx, y, cap, layer, ls=ls, anchor="middle", font=font)


def nom_cursive(c, cx):
    _nom_ajuste(c, "Julien Martin", cx, 41.0, 5.2, "scripts", 0.15)


def nom_capitales(c, cx):
    _nom_ajuste(c, "MARTIN", cx, 38.2, 4.4, "futural", 1.7)
    _nom_ajuste(c, "JULIEN", cx, 42.6, 2.4, "futural", 1.75, layer="bleu")


def nom_romain(c, cx):
    _nom_ajuste(c, "Julien Martin", cx, 40.8, 4.8, "timesr", 0.25)


def nom_romain_capitales(c, cx):
    _nom_ajuste(c, "JULIEN MARTIN", cx, 40.6, 3.7, "timesr", 0.8)


def nom_baton_double(c, cx):
    _nom_ajuste(c, "Julien Martin", cx, 40.8, 4.8, "rowmand", 0.2)


def orn_losange(c, cx, cy):
    """Ornement central du filet ; renvoie sa demi-largeur (pour couper le filet)."""
    c.poly("bleu", [(cx, cy - 1.1), (cx + 1.1, cy), (cx, cy + 1.1), (cx - 1.1, cy), (cx, cy - 1.1)])
    return 2.3


def signature(nom=nom_cursive, ornement=orn_losange, deco=None, mono_dx=0.0, filet_y=46.0,
              point=True):
    c = Carte(55, 85)
    cx = 27.5
    mw = 21.0
    mono = (cx - mw / 2 + mono_dx, 9.0, mw)
    if deco:
        deco(c, *mono)          # décor sous le monogramme (tracé avant lui)
    c.monogramme("accent", *mono)
    nom(c, cx)
    # filet avec ornement central
    demi = ornement(c, cx, filet_y)
    c.ligne("bleu", (12.0, filet_y), (cx - demi, filet_y))
    c.ligne("bleu", (cx + demi, filet_y), (43.0, filet_y))
    for k, t in enumerate(("Bureau d’études TopSolid’Wood", "Impression 3D",
                           "Signalétique vinyle adhésif")):
        w = c.texte(t, cx, 52.2 + k * 4.2, 1.95, "noir", ls=0.04, sx=0.88, anchor="middle")
        assert w <= 47, (t, w)
    if point:
        c.cercle("accent", cx, 63.6, 0.35, 12)
    c.texte(TEL, cx, 69.6, 2.4, "noir", ls=0.14, anchor="middle")
    w = c.texte(MAIL, cx, 74.2, 1.95, "noir", ls=0.03, sx=0.88, anchor="middle")
    assert w <= 46, w
    c.texte("MICRO-ENTREPRISE", cx, 78.6, 1.45, "bleu", ls=0.55, anchor="middle")
    return c


# ====================================================================== export
if __name__ == "__main__":
    OUT = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    STYLES = [("B_vue-en-coupe", vue_en_coupe()), ("C_filaire-3D", filaire_3d()),
              ("D_signature", signature())]

    # variantes du nom pour la carte verticale : une planche de comparaison
    VARIANTES = [("D1_capitales", nom_capitales), ("D2_romain", nom_romain),
                 ("D3_romain-capitales", nom_romain_capitales), ("D4_baton-double", nom_baton_double)]
    cartes = []
    for name, fn in VARIANTES:
        c = signature(fn)
        c.check()
        (OUT / f"carte_cricut_{name}.svg").write_text(c.svg(), encoding="utf-8")
        cartes.append(c)
    render_png([[c.svg(paper="#FBFAF6", preview=True) for c in cartes],
                [c.svg(pens=GEL, paper="#1C1F24", preview=True) for c in cartes]],
               OUT / "apercu_D_variantes-nom.png", page_w=4 * 55 + 30, page_h=2 * 85 + 20)
    for name, c in STYLES:
        c.check()
        (OUT / f"carte_cricut_{name}.svg").write_text(c.svg(), encoding="utf-8")
        render_png([[c.svg(paper="#FBFAF6", preview=True)],
                    [c.svg(pens=GEL, paper="#1C1F24", preview=True)]],
                   OUT / f"apercu_{name}.png",
                   page_w=c.w + 12, page_h=2 * c.h + 20)
        print(name, {k: len(v) for k, v in c.layers.items()})
