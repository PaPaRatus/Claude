#!/usr/bin/env python3
"""Carte de visite « fait main » pour Cricut : tracé aux stylos + découpe coins arrondis.

Usage : python3 cricut.py <dossier_sortie>

Produit :
  - carte_cricut.svg : fichier à importer dans Design Space (85 x 55 mm)
      4 calques : 1 stylo noir, 2 stylo bleu, 3 stylo accent (or), 4 découpe
  - apercus PNG (carte blanche + variante papier noir / stylos gel)

Texte en police à trait unique (Hershey « futural ») : le stylo trace une seule
ligne par trait, pas le contour des lettres. Chaque trait est tracé en aller-retour
pour que Design Space ne referme pas les tracés ouverts par une ligne parasite.
Dépendance : pip install Hershey-Fonts ; rendu des aperçus : chromium + pdftoppm.
"""
import math
import subprocess
import sys
from pathlib import Path

from HersheyFonts import HersheyFonts

OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(parents=True, exist_ok=True)

W, H, R = 85.0, 55.0, 3.5          # format et rayon des coins

# couleurs d'affichage des calques (le vrai rendu dépend des stylos choisis)
COUL = {
    "noir": "#1A1A1A",
    "bleu": "#1F5FBF",
    "accent": "#C9A227",
    "decoupe": "#E0301E",
}

FONT = HersheyFonts()
FONT.load_default_font("futural")
GLYPH_CAP, GLYPH_BASE = -12, 9      # repère des glyphes Hershey (y vers le bas)
ACCENTS = {"é": ("e", "aigu"), "è": ("e", "grave"), "É": ("E", "aigu"), "’": ("'", None)}
ETROIT = {" ": 0.55, "-": 0.65}     # chasse réduite : les espaces Hershey sont très larges

layers = {k: [] for k in COUL}      # listes de polylignes [(x, y), ...]


def glyph(c):
    return next(iter(FONT.glyphs_for_text(c)))


def texte(s, x, y, cap, layer, ls=0.0, sx=1.0, anchor="start"):
    """Écrit `s` en trait unique, ligne de base y, hauteur de capitale `cap` (mm)."""
    k = cap / (GLYPH_BASE - GLYPH_CAP)
    items, cur = [], 0.0
    for ch in s:
        base, acc = ACCENTS.get(ch, (ch, None))
        g = glyph(base)
        f = ETROIT.get(base, 1.0)
        items.append((cur, g, acc, f))
        cur += g.char_width * k * sx * f + ls
    width = cur - ls
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    for ox, g, acc, f in items:
        def P(gx, gy):
            return (x + ox + (gx - g.left_offset) * k * sx * f, y + (gy - GLYPH_BASE) * k)
        for st in g.strokes:
            layers[layer].append([P(*p) for p in st])
        if acc:
            (x0, top), (x1, _) = g.draw_box[0], g.draw_box[1]
            cx = (x0 + x1) / 2
            if acc == "aigu":
                layers[layer].append([P(cx - 2, top - 3), P(cx + 3, top - 7.5)])
            else:
                layers[layer].append([P(cx + 2, top - 3), P(cx - 3, top - 7.5)])
    return width


def ligne(layer, *pts):
    layers[layer].append(list(pts))


def axe(layer, p0, p1, long_=2.6, court=0.5, vide=0.7):
    """Trait mixte (axe de dessin technique) : long, vide, point, vide..."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    t = 0.0
    while t < L:
        for seg in (long_, court):
            a, b = t, min(t + seg, L)
            if b > a:
                ligne(layer, (x0 + ux * a, y0 + uy * a), (x0 + ux * b, y0 + uy * b))
            t = b + vide
            if t >= L:
                break


def arc_pts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def monogramme(x0, y0, width):
    """Monogramme JM (repère 100 x 93) ; renvoie le point de jonction en mm."""
    s = width / 100.0
    P = lambda x, y: (x0 + x * s, y0 + y * s)
    # triangle haut + jambage du J + boucle (centre 25.4 ; 67.5, r 25.4, de 0° à 180°)
    j = [P(0, 0), P(50.8, 0), P(50.8, 67.5)]
    j += [P(25.4 + 25.4 * math.cos(math.radians(a)), 67.5 + 25.4 * math.sin(math.radians(a)))
          for a in range(0, 181, 6)]
    layers["noir"].append(j)
    layers["noir"].append([P(0, 0), P(50.8, 46.6), P(100, 0), P(100, 93)])
    return P(50.8, 46.6), P(0, 0), P(100, 93)


# ------------------------------------------------------------------ dessin
# cadre de plan avec filets qui dépassent aux coins (bleu)
i, o = 4.5, 2.0
ligne("bleu", (i - o, i), (W - i + o, i))
ligne("bleu", (i - o, H - i), (W - i + o, H - i))
ligne("bleu", (i, i - o), (i, H - i + o))
ligne("bleu", (W - i, i - o), (W - i, H - i + o))

# colonne gauche : monogramme, point de jonction repéré comme un centre de cercle
MX, MY, MW = 9.6, 9.2, 18.0
(jx, jy), (mx0, my0), (mx1, my1) = monogramme(MX, MY, MW)
layers["accent"].append(arc_pts(jx, jy, 1.15, 0, 360, 32))
layers["accent"].append(arc_pts(jx, jy, 0.55, 0, 360, 20))
ligne("bleu", (jx - 2.6, jy), (jx - 1.5, jy))
ligne("bleu", (jx + 1.5, jy), (jx + 2.6, jy))

cxL = MX + MW / 2
texte("MARTIN", cxL, 32.2, 2.7, "noir", ls=0.95, anchor="middle")
texte("JULIEN", cxL, 36.4, 1.85, "noir", ls=1.05, anchor="middle")
texte("micro-entreprise", cxL, 44.6, 1.75, "bleu", ls=0.05, sx=0.92, anchor="middle")

# séparation : axe en trait mixte
axe("bleu", (32.0, 8.5), (32.0, 46.8))

# colonne droite
X = 35.0
XR = 79.0
wh = texte("ACTIVITÉS", X, 11.4, 1.7, "bleu", ls=0.55)
ligne("bleu", (X + wh + 1.6, 10.55), (XR, 10.55))

def item(num, y, l1, l2=None):
    texte(num, X, y, 1.9, "accent", ls=0.15)
    texte(l1, X + 4.6, y, 2.35, "noir", ls=0.08)
    if l2:
        texte(l2, X + 4.6, y + 3.1, 1.75, "bleu", ls=0.1)

item("01", 16.7, "Bureau d’études", "TopSolid’Wood")
item("02", 24.6, "Impression 3D")
item("03", 30.0, "Signalétique", "vinyle adhésif")

ligne("bleu", (X, 36.4), (XR, 36.4))
# icône téléphone (smartphone) et enveloppe, au trait
def rect(layer, x, y, w, h):
    ligne(layer, (x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y))
rect("bleu", X + 0.5, 38.25, 1.6, 2.65)
ligne("bleu", (X + 1.05, 40.35), (X + 1.55, 40.35))
rect("bleu", X, 43.4, 2.7, 1.8)
ligne("bleu", (X, 43.4), (X + 1.35, 44.45), (X + 2.7, 43.4))
texte("06 23 35 95 60", X + 4.6, 40.9, 2.35, "noir", ls=0.12)
we = texte("martinjulien.be@gmail.com", X + 4.6, 45.2, 2.1, "noir", ls=0.03, sx=0.9)
assert X + 4.6 + we <= XR, f"e-mail trop long : {X + 4.6 + we:.1f} mm"

# découpe : rectangle à coins arrondis
CUT = (f"M{R} 0H{W-R}A{R} {R} 0 0 1 {W} {R}V{H-R}A{R} {R} 0 0 1 {W-R} {H}"
       f"H{R}A{R} {R} 0 0 1 0 {H-R}V{R}A{R} {R} 0 0 1 {R} 0Z")


# ------------------------------------------------------------------ export
def d_allerretour(polys):
    out = []
    for p in polys:
        pts = p + p[-2::-1]                    # aller puis retour : fermeture de longueur nulle
        out.append("M" + "L".join(f"{x:.3f} {y:.3f}" for x, y in pts))
    return "".join(out)


NOMS = {"noir": "1_STYLO_noir", "bleu": "2_STYLO_bleu", "accent": "3_STYLO_accent_or",
        "decoupe": "4_DECOUPE_contour"}


def svg(pens=None, paper=None, preview=False):
    pens = pens or COUL
    sw = 0.38 if preview else 0.3
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
             f'viewBox="0 0 {W} {H}">']
    if paper:
        parts.append(f'<path d="{CUT}" fill="{paper}"/>')
    for k in ("noir", "bleu", "accent"):
        parts.append(f'<path id="{NOMS[k]}" d="{d_allerretour(layers[k])}" fill="none" '
                     f'stroke="{pens[k]}" stroke-width="{sw}" stroke-linecap="round" '
                     f'stroke-linejoin="round"/>')
    if not preview:
        parts.append(f'<path id="{NOMS["decoupe"]}" d="{CUT}" fill="none" '
                     f'stroke="{COUL["decoupe"]}" stroke-width="0.25"/>')
    parts.append("</svg>")
    return "".join(parts)


(OUT / "carte_cricut.svg").write_text(svg(), encoding="utf-8")


def png(svgtxt, name, bg="#E9E4DA"):
    html = OUT / f"_{name}.html"
    pdf = OUT / f"_{name}.pdf"
    html.write_text(f'''<!doctype html><meta charset="utf-8"><style>
@page {{ size: 95mm 65mm; margin: 0 }} html,body {{ margin:0; background:{bg} }}
div {{ width:95mm; height:65mm; display:flex; align-items:center; justify-content:center }}
svg {{ filter: drop-shadow(0 0.4mm 0.5mm rgba(0,0,0,.25)) }}</style><div>{svgtxt}</div>''',
                    encoding="utf-8")
    subprocess.run(["/opt/pw-browsers/chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf}", f"file://{html}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pdftoppm", "-r", "400", "-png", "-singlefile", str(pdf), str(OUT / name)],
                   check=True)
    html.unlink()
    pdf.unlink()


png(svg(paper="#FBFAF6", preview=True), "apercu_cricut_papier-blanc")
png(svg(pens={"noir": "#F4F1EA", "bleu": "#A9B4C2", "accent": "#D8B44A"},
        paper="#1C1F24", preview=True), "apercu_cricut_papier-noir")
n = {k: len(v) for k, v in layers.items()}
print("ok", n)
