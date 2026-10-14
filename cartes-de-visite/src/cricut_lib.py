"""Outils communs aux cartes Cricut tracées au stylo.

Une Carte contient des calques de stylo (polylignes en mm, y vers le bas) et une
découpe (rectangle à coins arrondis). Le texte utilise les polices Hershey à
trait unique ; chaque trait est exporté en aller-retour pour que Design Space ne
referme pas les tracés ouverts.
"""
import math
import subprocess
from pathlib import Path

from HersheyFonts import HersheyFonts

COUL = {"noir": "#1A1A1A", "bleu": "#1F5FBF", "accent": "#C9A227", "decoupe": "#E0301E"}
NOMS = {"noir": "1_STYLO_noir", "bleu": "2_STYLO_bleu", "accent": "3_STYLO_accent_or",
        "decoupe": "4_DECOUPE_contour"}
GEL = {"noir": "#F4F1EA", "bleu": "#A9B4C2", "accent": "#D8B44A"}   # stylos gel sur papier noir

ACCENTS = {"é": ("e", "aigu"), "è": ("e", "grave"), "É": ("E", "aigu"), "’": ("'", None)}
ETROIT = {" ": 0.55, "-": 0.65}
_FONTS = {}


def _font(name):
    if name not in _FONTS:
        f = HersheyFonts()
        f.load_default_font(name)
        _FONTS[name] = f
    return _FONTS[name]


def arc_pts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


class Carte:
    def __init__(self, w=85.0, h=55.0, r=3.5):
        self.w, self.h, self.r = w, h, r
        self.layers = {k: [] for k in ("noir", "bleu", "accent")}

    # -------------------------------------------------------------- primitives
    def ligne(self, layer, *pts):
        self.layers[layer].append(list(pts))

    def poly(self, layer, pts):
        self.layers[layer].append(list(pts))

    def rect(self, layer, x, y, w, h):
        self.ligne(layer, (x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y))

    def cercle(self, layer, cx, cy, r, n=None):
        self.poly(layer, arc_pts(cx, cy, r, 0, 360, n or max(24, int(r * 12))))

    def axe(self, layer, p0, p1, long_=2.6, court=0.5, vide=0.7):
        """Trait mixte de dessin technique."""
        (x0, y0), (x1, y1) = p0, p1
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        t = 0.0
        while t < L:
            for seg in (long_, court):
                a, b = t, min(t + seg, L)
                if b > a:
                    self.ligne(layer, (x0 + ux * a, y0 + uy * a), (x0 + ux * b, y0 + uy * b))
                t = b + vide
                if t >= L:
                    break

    def texte(self, s, x, y, cap, layer, ls=0.0, sx=1.0, anchor="start", font="futural"):
        """Texte en trait unique : ligne de base y, hauteur de capitale `cap` mm. Renvoie la largeur."""
        F = _font(font)
        items, cur = [], 0.0
        for ch in s:
            base, acc = ACCENTS.get(ch, (ch, None))
            g = next(iter(F.glyphs_for_text(base)))
            k = cap / (g.base_line - g.cap_line)
            f = ETROIT.get(base, 1.0)
            items.append((cur, g, acc, f, k))
            cur += g.char_width * k * sx * f + ls
        width = cur - ls
        x -= {"start": 0, "middle": width / 2, "end": width}[anchor]
        for ox, g, acc, f, k in items:
            def P(gx, gy, g=g, ox=ox, f=f, k=k):
                return (x + ox + (gx - g.left_offset) * k * sx * f, y + (gy - g.base_line) * k)
            for st in g.strokes:
                self.poly(layer, [P(*p) for p in st])
            if acc:
                (x0, top), (x1, _) = g.draw_box[0], g.draw_box[1]
                cx = (x0 + x1) / 2
                sgn = 1 if acc == "aigu" else -1
                self.ligne(layer, P(cx - 2 * sgn, top - 3), P(cx + 3 * sgn, top - 7.5))
        return width

    def largeur(self, s, cap, ls=0.0, sx=1.0, font="futural"):
        save = self.layers
        self.layers = {k: [] for k in save}
        w = self.texte(s, 0, 0, cap, "noir", ls, sx, font=font)
        self.layers = save
        return w

    # -------------------------------------------------------------- monogramme
    MONO_W, MONO_H = 100.0, 93.0
    MONO_JONCTION = (50.8, 46.6)

    @staticmethod
    def mono_polys():
        """Monogramme JM dans son repère 100 x 93 (deux polylignes)."""
        j = [(0, 0), (50.8, 0), (50.8, 67.5)]
        j += [(25.4 + 25.4 * math.cos(math.radians(a)), 67.5 + 25.4 * math.sin(math.radians(a)))
              for a in range(0, 181, 6)]
        m = [(0, 0), (50.8, 46.6), (100, 0), (100, 93)]
        return [j, m]

    def monogramme(self, layer, x0, y0, width):
        s = width / 100.0
        for p in self.mono_polys():
            self.poly(layer, [(x0 + x * s, y0 + y * s) for x, y in p])
        jx, jy = self.MONO_JONCTION
        return (x0 + jx * s, y0 + jy * s)

    # -------------------------------------------------------------- export
    def cut_d(self):
        W, H, R = self.w, self.h, self.r
        return (f"M{R} 0H{W-R}A{R} {R} 0 0 1 {W} {R}V{H-R}A{R} {R} 0 0 1 {W-R} {H}"
                f"H{R}A{R} {R} 0 0 1 0 {H-R}V{R}A{R} {R} 0 0 1 {R} 0Z")

    @staticmethod
    def _d(polys):
        out = []
        for p in polys:
            pts = p + p[-2::-1]
            out.append("M" + "L".join(f"{x:.3f} {y:.3f}" for x, y in pts))
        return "".join(out)

    def svg(self, pens=None, paper=None, preview=False):
        pens = pens or COUL
        sw = 0.38 if preview else 0.3
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" '
               f'viewBox="0 0 {self.w} {self.h}">']
        if paper:
            out.append(f'<path d="{self.cut_d()}" fill="{paper}"/>')
        for k in ("noir", "bleu", "accent"):
            if self.layers[k]:
                out.append(f'<path id="{NOMS[k]}" d="{self._d(self.layers[k])}" fill="none" '
                           f'stroke="{pens[k]}" stroke-width="{sw}" stroke-linecap="round" '
                           f'stroke-linejoin="round"/>')
        if not preview:
            out.append(f'<path id="{NOMS["decoupe"]}" d="{self.cut_d()}" fill="none" '
                       f'stroke="{COUL["decoupe"]}" stroke-width="0.25"/>')
        out.append("</svg>")
        return "".join(out)

    def check(self, marge=2.5):
        """Vérifie que tous les tracés restent à `marge` mm du bord de découpe."""
        for k, polys in self.layers.items():
            for p in polys:
                for x, y in p:
                    assert marge <= x <= self.w - marge and marge <= y <= self.h - marge, \
                        f"{k} : point ({x:.1f}, {y:.1f}) trop près du bord"


def render_png(svgs, out_png, page_w, page_h, bg="#E9E4DA", gap=6):
    """Rend une ou plusieurs cartes (liste de lignes de SVG) en PNG 400 dpi."""
    out_png = Path(out_png)
    rows = "".join(f'<div class="r">{"".join(row)}</div>' for row in svgs)
    html = out_png.with_suffix(".html")
    pdf = out_png.with_suffix(".pdf")
    html.write_text(f'''<!doctype html><meta charset="utf-8"><style>
@page {{ size: {page_w}mm {page_h}mm; margin: 0 }} html,body {{ margin:0; background:{bg} }}
body {{ width:{page_w}mm; height:{page_h}mm; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:{gap}mm }}
.r {{ display:flex; gap:{gap}mm; align-items:center }}
svg {{ filter: drop-shadow(0 0.4mm 0.5mm rgba(0,0,0,.25)) }}</style>{rows}''', encoding="utf-8")
    subprocess.run(["/opt/pw-browsers/chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf}", f"file://{html}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", str(pdf),
                    str(out_png.with_suffix(""))], check=True)
    html.unlink()
    pdf.unlink()
