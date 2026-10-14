"""cricut_stylo — dessin au stylo pour Cricut (Design Space), en Python pur.

Un `Dessin` contient des calques de stylo (polylignes en mm, origine en haut à gauche,
y vers le bas) et une découpe. L'export SVG produit un <path> par calque :
  1_STYLO_<nom>, 2_STYLO_<nom>, ... puis DECOUPE_contour.

Règles appliquées automatiquement :
- texte en police Hershey à trait unique (le stylo trace une ligne, pas un contour) ;
- chaque trait est exporté en aller-retour : Design Space referme les tracés ouverts,
  la fermeture devient alors de longueur nulle (pas de trait parasite) ;
- accents français composés à la main (les polices Hershey n'en ont pas).

Dépendances : pip install Hershey-Fonts ; aperçus PNG : chromium + pdftoppm
(ou rsvg-convert, ou cairosvg). Sans eux, le SVG reste valide, seul l'aperçu manque.
"""
import math
import os
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path

try:
    from HersheyFonts import HersheyFonts
except ImportError as e:  # pragma: no cover
    raise SystemExit("Installer la police à trait unique : pip install Hershey-Fonts") from e

# couleurs d'affichage des stylos (le rendu réel dépend du stylo inséré dans la machine)
STYLOS = {
    "noir": "#1A1A1A", "bleu": "#1F5FBF", "or": "#C9A227", "argent": "#9AA3AD",
    "rouge": "#C0392B", "vert": "#2E7D4F", "blanc": "#F4F1EA",
}
COUL_DECOUPE = "#E0301E"
PAPIER_BLANC = "#FBFAF6"

# ----------------------------------------------------------------------------- texte
_ACC = {
    "é": ("e", "aigu"), "è": ("e", "grave"), "ê": ("e", "circ"), "ë": ("e", "trema"),
    "à": ("a", "grave"), "â": ("a", "circ"), "ä": ("a", "trema"),
    "î": ("i", "circ"), "ï": ("i", "trema"), "ô": ("o", "circ"), "ö": ("o", "trema"),
    "ù": ("u", "grave"), "û": ("u", "circ"), "ü": ("u", "trema"), "ÿ": ("y", "trema"),
    "ç": ("c", "cedille"),
    "É": ("E", "aigu"), "È": ("E", "grave"), "Ê": ("E", "circ"), "Ë": ("E", "trema"),
    "À": ("A", "grave"), "Â": ("A", "circ"), "Î": ("I", "circ"), "Ï": ("I", "trema"),
    "Ô": ("O", "circ"), "Ù": ("U", "grave"), "Û": ("U", "circ"), "Ü": ("U", "trema"),
    "Ç": ("C", "cedille"),
    "’": ("'", None), "‘": ("'", None), "´": ("'", None), " ": (" ", None),
    " ": (" ", None), "–": ("-", None), "—": ("-", None), "×": ("x", None),
}
_EXPAND = {"œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE", "…": "...", "«": "<<", "»": ">>"}
_ETROIT = {" ": 0.55, "-": 0.65}          # les espaces Hershey sont très larges
_FONTS = {}


def police(nom="futural"):
    """Polices utiles : futural (bâton), rowmand (bâton double), timesr (à empattements),
    scripts (cursive). Liste complète : HersheyFonts().default_font_names."""
    if nom not in _FONTS:
        f = HersheyFonts()
        f.load_default_font(nom)
        _FONTS[nom] = f
    return _FONTS[nom]


def _glyphe(nom, ch):
    """Glyphe Hershey, ou None si le caractère n'existe pas dans la police."""
    return next(iter(police(nom).glyphs_for_text(ch)), None)


def _accent(P, acc, cx, top):
    """Traits d'accent dans le repère du glyphe (y vers le bas, ligne de base 9)."""
    if acc == "aigu":
        return [[P(cx - 2, top - 3), P(cx + 3, top - 7.5)]]
    if acc == "grave":
        return [[P(cx + 2, top - 3), P(cx - 3, top - 7.5)]]
    if acc == "circ":
        return [[P(cx - 3.5, top - 3), P(cx, top - 7), P(cx + 3.5, top - 3)]]
    if acc == "trema":
        return [[P(cx - 2.5, top - 3.5), P(cx - 2.5, top - 5)], [P(cx + 2.5, top - 3.5), P(cx + 2.5, top - 5)]]
    if acc == "cedille":
        return [[P(cx, 9), P(cx, 11), P(cx + 2, 12), P(cx, 14), P(cx - 2, 13.5)]]
    return []


def texte_polylignes(s, x, y, cap, ls=0.0, sx=1.0, ancre="start", nom_police="futural"):
    """Polylignes d'un texte (ligne de base y, hauteur de capitale `cap` mm) et sa largeur."""
    for a, b in _EXPAND.items():
        s = s.replace(a, b)
    items, cur = [], 0.0
    for ch in s:
        if ch in "°·•":                            # absents des polices Hershey : dessinés à la main
            items.append((cur, None, {"°": "degre", "·": "median", "•": "puce"}[ch], 1.0, cap / 21.0, ch))
            cur += (0.55 if ch == "°" else 0.6) * cap + ls
            continue
        base, acc = _ACC.get(ch, (ch, None))
        g = _glyphe(nom_police, base)
        if g is None:
            warnings.warn(f"caractère {ch!r} absent de la police {nom_police} : remplacé par un espace")
            base, acc, g = " ", None, _glyphe(nom_police, " ")
        k = cap / (g.base_line - g.cap_line)
        f = _ETROIT.get(base, 1.0)
        items.append((cur, g, acc, f, k, base))
        cur += g.char_width * k * sx * f + ls
    largeur = max(0.0, cur - ls)
    x -= {"start": 0.0, "middle": largeur / 2, "end": largeur}[ancre]
    out = []
    for ox, g, acc, f, k, base in items:
        if acc in ("degre", "median", "puce"):
            r = {"degre": 0.17, "median": 0.07, "puce": 0.13}[acc] * cap
            cy_ = y - cap + r if acc == "degre" else y - 0.38 * cap
            out.append(arc_pts(x + ox + 0.3 * cap if acc != "degre" else x + ox + r + 0.05 * cap,
                               cy_, r, 0, 360, 14))
            continue

        def P(gx, gy, g=g, ox=ox, f=f, k=k):
            return (x + ox + (gx - g.left_offset) * k * sx * f, y + (gy - g.base_line) * k)
        strokes = list(g.strokes)
        if acc and base in "ij":             # i/j accentués : on retire le point
            strokes = [st for st in strokes if max(p[1] for p in st) > -7]
        for st in strokes:
            out.append([P(*p) for p in st])
        if acc:
            ys = [p[1] for st in strokes for p in st] or [g.cap_line]
            xs = [p[0] for st in strokes for p in st] or [0]
            out += _accent(P, acc, (min(xs) + max(xs)) / 2, min(ys))
    return out, largeur


def arc_pts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def rrect_pts(x, y, w, h, r, n=12):
    if r <= 0:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    pts = []
    for (cx, cy, a0) in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0),
                         (x + r, y + h - r, 90), (x + r, y + r, 180)):
        pts += arc_pts(cx, cy, r, a0, a0 + 90, n)
    return pts + [pts[0]]


# ----------------------------------------------------------------------------- dessin
class Dessin:
    """Format w x h mm. decoupe : 'rrect' (coins arrondis r), 'rect', 'cercle' (ellipse
    inscrite), 'aucune', ou un chemin SVG (attribut d) en mm passé tel quel."""

    def __init__(self, w=85.0, h=55.0, decoupe="rrect", r=3.5, couches=("noir", "bleu"), couleurs=None):
        self.w, self.h, self.r, self.decoupe = float(w), float(h), float(r), decoupe
        self.couleurs = dict(STYLOS)
        self.couleurs.update(couleurs or {})
        self.couches = {c: [] for c in couches}

    # -------------------------------------------------------------- primitives
    def _c(self, couche):
        if couche not in self.couches:
            self.couches[couche] = []
        return self.couches[couche]

    def poly(self, couche, pts):
        if len(pts) >= 2:
            self._c(couche).append([tuple(p) for p in pts])

    def ligne(self, couche, *pts):
        self.poly(couche, list(pts))

    def rect(self, couche, x, y, w, h, r=0.0):
        self.poly(couche, rrect_pts(x, y, w, h, r))

    def cercle(self, couche, cx, cy, r, n=None):
        self.poly(couche, arc_pts(cx, cy, r, 0, 360, n or max(16, int(r * 12))))

    def arc(self, couche, cx, cy, r, a0, a1, n=None):
        self.poly(couche, arc_pts(cx, cy, r, a0, a1, n or max(6, int(abs(a1 - a0) / 6))))

    def pointilles(self, couche, p0, p1, trait=0.9, vide=0.6):
        (x0, y0), (x1, y1) = p0, p1
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        t = 0.0
        while t < L:
            b = min(t + trait, L)
            self.ligne(couche, (x0 + ux * t, y0 + uy * t), (x0 + ux * b, y0 + uy * b))
            t = b + vide

    def axe(self, couche, p0, p1, long_=2.6, court=0.5, vide=0.7):
        """Trait mixte de dessin technique (long, vide, point, vide...)."""
        (x0, y0), (x1, y1) = p0, p1
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        t = 0.0
        while t < L:
            for seg in (long_, court):
                a, b = t, min(t + seg, L)
                if b > a:
                    self.ligne(couche, (x0 + ux * a, y0 + uy * a), (x0 + ux * b, y0 + uy * b))
                t = b + vide
                if t >= L:
                    break

    def fleche(self, couche, pointe, direction, L=1.2, ang=18):
        dx, dy = direction
        a0 = math.atan2(-dy, -dx)
        for da in (ang, -ang):
            a = a0 + math.radians(da)
            self.ligne(couche, pointe, (pointe[0] + L * math.cos(a), pointe[1] + L * math.sin(a)))

    def hachurer(self, couche, polys, angle=45, pas=0.9):
        """Remplit des polygones fermés par des hachures (règle pair-impair : anneaux et trous OK).
        Un stylo ne remplit pas : c'est la façon d'obtenir une surface. pas >= 2 x largeur du stylo."""
        a = math.radians(angle)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        aretes = [(p[i], p[i + 1]) for p in polys for i in range(len(p) - 1)]
        ks = [x * nx + y * ny for p in polys for x, y in p]
        k = min(ks) + pas / 2
        while k < max(ks):
            ts = []
            for (x1, y1), (x2, y2) in aretes:
                d1, d2 = x1 * nx + y1 * ny - k, x2 * nx + y2 * ny - k
                if (d1 < 0) != (d2 < 0):
                    lam = d1 / (d1 - d2)
                    ts.append((x1 + (x2 - x1) * lam) * ux + (y1 + (y2 - y1) * lam) * uy)
            ts.sort()
            for t0, t1 in zip(ts[0::2], ts[1::2]):
                self.ligne(couche, (nx * k + ux * t0, ny * k + uy * t0), (nx * k + ux * t1, ny * k + uy * t1))
            k += pas

    def texte(self, s, x, y, cap, couche, ls=0.0, sx=1.0, ancre="start", police="futural"):
        polys, w = texte_polylignes(s, x, y, cap, ls, sx, ancre, police)
        for p in polys:
            self.poly(couche, p)
        return w

    @staticmethod
    def largeur(s, cap, ls=0.0, sx=1.0, police="futural"):
        return texte_polylignes(s, 0, 0, cap, ls, sx, "start", police)[1]

    def texte_ajuste(self, s, x, y, cap, couche, wmax, ls=0.0, sx=1.0, ancre="start",
                     police="futural", cap_min=1.6, sx_min=0.82):
        """Écrit en réduisant d'abord la condensation (sx) puis la taille pour tenir dans wmax.
        Renvoie (largeur, cap, sx) ; lève ValueError si impossible au-dessus de cap_min."""
        w = self.largeur(s, cap, ls, sx, police)
        while w > wmax and sx > sx_min + 1e-9:
            sx = max(sx_min, sx - 0.02)
            w = self.largeur(s, cap, ls, sx, police)
        if w > wmax:
            cap2 = cap * wmax / w
            if cap2 < cap_min:
                raise ValueError(f"« {s} » trop long : {w:.1f} mm pour {wmax:.1f} mm disponibles")
            cap = cap2
        return self.texte(s, x, y, cap, couche, ls, sx, ancre, police), cap, sx

    def texte_tourne(self, s, x, y, cap, couche, angle, police="futural"):
        """Texte centré sur (x, y) puis tourné de `angle` degrés."""
        polys, _ = texte_polylignes(s, 0, cap / 2, cap, ancre="middle", nom_police=police)
        a = math.radians(angle)
        ca, sa = math.cos(a), math.sin(a)
        for p in polys:
            self.poly(couche, [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in p])

    def motif(self, couche, polys, x0, y0, largeur, boite=(100.0, 100.0)):
        """Place des polylignes définies dans un repère `boite` (ex. un logo 100 x 93)."""
        s = largeur / boite[0]
        out = [[(x0 + x * s, y0 + y * s) for x, y in p] for p in polys]
        for p in out:
            self.poly(couche, p)
        return out

    def ombre_hachuree(self, couche, polys, d=(0.95, 0.95), pas=0.95, depart=0.42, seuil=0.35):
        """Ombre portée en hachures (effet relief / gravure) sous des traits déjà placés.
        Ne hachure pas les traits presque parallèles à l'ombre (ils seraient recouverts) et
        démarre à distance du trait pour que les deux encres ne se touchent pas."""
        dx, dy = d
        dn = math.hypot(dx, dy)
        for pts in polys:
            reste = 0.0
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                L = math.hypot(bx - ax, by - ay)
                if L < 1e-9:
                    continue
                if abs((bx - ax) * dy - (by - ay) * dx) / (L * dn) < seuil:
                    reste = 0.0
                    continue
                t = reste
                while t < L:
                    px, py = ax + (bx - ax) * t / L, ay + (by - ay) * t / L
                    self.ligne(couche, (px + dx * depart, py + dy * depart), (px + dx, py + dy))
                    t += pas
                reste = t - L

    def deplacer(self, dx=0.0, dy=0.0, couches=None):
        for nom in couches or list(self.couches):
            for p in self.couches[nom]:
                p[:] = [(x + dx, y + dy) for x, y in p]

    def boite(self, couches=None):
        pts = [q for nom in (couches or self.couches) for p in self.couches.get(nom, []) for q in p]
        if not pts:
            return None
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    # -------------------------------------------------------------- contrôles
    def verifier(self, marge=2.5):
        """Vérifie que tout reste à `marge` mm du bord de découpe (décalage tracé/découpe
        possible d'environ 0,5 mm). Renvoie la liste des points fautifs (vide = OK)."""
        fautes = []
        for nom, polys in self.couches.items():
            for p in polys:
                for x, y in p:
                    if self.decoupe == "cercle":
                        rx, ry = self.w / 2 - marge, self.h / 2 - marge
                        ok = ((x - self.w / 2) / rx) ** 2 + ((y - self.h / 2) / ry) ** 2 <= 1
                    else:
                        ok = marge <= x <= self.w - marge and marge <= y <= self.h - marge
                    if not ok:
                        fautes.append((nom, round(x, 2), round(y, 2)))
        return fautes

    # -------------------------------------------------------------- export
    def decoupe_d(self):
        W, H, R = self.w, self.h, self.r
        if self.decoupe == "aucune":
            return None
        if self.decoupe == "rect":
            return f"M0 0H{W}V{H}H0Z"
        if self.decoupe == "cercle":
            rx, ry = W / 2, H / 2
            return f"M0 {ry}A{rx} {ry} 0 1 0 {W} {ry}A{rx} {ry} 0 1 0 0 {ry}Z"
        if self.decoupe == "rrect":
            return (f"M{R} 0H{W-R}A{R} {R} 0 0 1 {W} {R}V{H-R}A{R} {R} 0 0 1 {W-R} {H}"
                    f"H{R}A{R} {R} 0 0 1 0 {H-R}V{R}A{R} {R} 0 0 1 {R} 0Z")
        return self.decoupe                      # chemin SVG fourni

    @staticmethod
    def _d(polys):
        out = []
        for p in polys:
            pts = p + p[-2::-1]                  # aller puis retour
            out.append("M" + "L".join(f"{x:.3f} {y:.3f}" for x, y in pts))
        return "".join(out)

    def svg(self, couleurs=None, papier=None, apercu=False, epaisseur=None):
        """apercu=True : rendu réaliste (trait de stylo 0,38 mm, papier, sans la découpe)."""
        coul = dict(self.couleurs)
        coul.update(couleurs or {})
        sw = epaisseur or (0.38 if apercu else 0.3)
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:g}mm" height="{self.h:g}mm" '
               f'viewBox="0 0 {self.w:g} {self.h:g}">']
        d_cut = self.decoupe_d()
        if papier:
            if d_cut:
                out.append(f'<path d="{d_cut}" fill="{papier}"/>')
            else:
                out.append(f'<rect width="{self.w:g}" height="{self.h:g}" fill="{papier}"/>')
        i = 0
        for nom, polys in self.couches.items():
            if not polys:
                continue
            i += 1
            out.append(f'<path id="{i}_STYLO_{nom}" d="{self._d(polys)}" fill="none" '
                       f'stroke="{coul.get(nom, "#333")}" stroke-width="{sw}" stroke-linecap="round" '
                       f'stroke-linejoin="round"/>')
        if d_cut and not apercu:
            out.append(f'<path id="{i + 1}_DECOUPE_contour" d="{d_cut}" fill="none" '
                       f'stroke="{COUL_DECOUPE}" stroke-width="0.25"/>')
        out.append("</svg>")
        return "".join(out)

    def enregistrer(self, chemin):
        Path(chemin).write_text(self.svg(), encoding="utf-8")
        return Path(chemin)

    def apercu_png(self, chemin, papier=PAPIER_BLANC, couleurs=None, dpi=300):
        return planche([[self.svg(couleurs, papier, apercu=True)]], chemin, self.w + 12, self.h + 12, dpi=dpi)

    def resume(self):
        return {nom: len(p) for nom, p in self.couches.items() if p}


# ----------------------------------------------------------------------------- aperçus
def _chromium():
    for c in (os.environ.get("CRICUT_CHROMIUM"), "/opt/pw-browsers/chromium",
              shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("google-chrome")):
        if c and Path(c).exists():
            return c
    return None


def planche(lignes_svg, chemin_png, page_w, page_h, fond="#E9E4DA", gap=6, dpi=300):
    """Rend une grille de SVG (liste de lignes) en PNG. Renvoie le chemin, ou None si aucun
    moteur de rendu n'est disponible (le SVG reste utilisable)."""
    chemin_png = Path(chemin_png).resolve()
    rows = "".join(f'<div class="r">{"".join(row)}</div>' for row in lignes_svg)
    html = (f'<!doctype html><meta charset="utf-8"><style>@page{{size:{page_w}mm {page_h}mm;margin:0}}'
            f'html,body{{margin:0;background:{fond}}}body{{width:{page_w}mm;height:{page_h}mm;display:flex;'
            f'flex-direction:column;align-items:center;justify-content:center;gap:{gap}mm}}'
            f'.r{{display:flex;gap:{gap}mm;align-items:center}}'
            f'svg{{filter:drop-shadow(0 .4mm .5mm rgba(0,0,0,.25))}}</style>{rows}')
    chrome = _chromium()
    with tempfile.TemporaryDirectory() as tmp:
        h = Path(tmp) / "p.html"
        pdf = Path(tmp) / "p.pdf"
        h.write_text(html, encoding="utf-8")
        if chrome and shutil.which("pdftoppm"):
            subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                            f"--print-to-pdf={pdf}", f"file://{h}"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", str(pdf),
                            str(chemin_png.with_suffix(""))], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return chemin_png
    if len(lignes_svg) == 1 and len(lignes_svg[0]) == 1:
        svg_txt = lignes_svg[0][0]
        if shutil.which("rsvg-convert"):
            src = chemin_png.with_suffix(".tmp.svg")
            src.write_text(svg_txt, encoding="utf-8")
            subprocess.run(["rsvg-convert", "-d", str(dpi), "-p", str(dpi), "-o", str(chemin_png), str(src)], check=True)
            src.unlink()
            return chemin_png
        try:
            import cairosvg
            cairosvg.svg2png(bytestring=svg_txt.encode(), write_to=str(chemin_png), dpi=dpi)
            return chemin_png
        except ImportError:
            pass
    print("Aperçu PNG impossible (ni chromium+pdftoppm, ni rsvg-convert, ni cairosvg).")
    return None


# ----------------------------------------------------------------------------- ornements
def orn_losange(d, cx, cy, couche="bleu", a=1.1):
    d.poly(couche, [(cx, cy - a), (cx + a, cy), (cx, cy + a), (cx - a, cy), (cx, cy - a)])
    return a + 1.2


def orn_cube(d, cx, cy, couche="bleu", R=1.95):
    """Cube isométrique (hexagone + Y)."""
    d.poly(couche, [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
                    for a in (-90, -30, 30, 90, 150, 210, 270)])
    for a in (90, 210, 330):
        d.ligne(couche, (cx, cy), (cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))))
    return R * math.cos(math.radians(30)) + 1.1


def orn_necker(d, cx, cy, couche="bleu", a=2.5, k=1.05):
    fx, fy = cx - (a + k) / 2, cy - a / 2 + k / 2
    av = [(fx, fy), (fx + a, fy), (fx + a, fy + a), (fx, fy + a), (fx, fy)]
    d.poly(couche, av)
    d.poly(couche, [(x + k, y - k) for x, y in av])
    for (x, y) in av[:4]:
        d.ligne(couche, (x, y), (x + k, y - k))
    return (a + k) / 2 + 1.1


def orn_rosace(d, cx, cy, couche="bleu", R=2.55):
    d.cercle(couche, cx, cy, R, 40)
    for k in range(6):
        a = math.radians(60 * k)
        d.arc(couche, cx + R * math.cos(a), cy + R * math.sin(a), R, 60 * k + 120, 60 * k + 240, 16)
    return R + 1.1


def orn_ecrou(d, cx, cy, couche="bleu", R=2.3):
    d.poly(couche, [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in range(0, 361, 60)])
    d.cercle(couche, cx, cy, 0.95, 24)
    return R + 0.9


def orn_mire(d, cx, cy, couche="bleu", r=1.55):
    d.cercle(couche, cx, cy, r, 36)
    d.ligne(couche, (cx - 0.7, cy), (cx + 0.7, cy))
    d.ligne(couche, (cx, cy - 0.7), (cx, cy + 0.7))
    d.ligne(couche, (cx, cy - r - 0.45), (cx, cy - r - 0.95))
    d.ligne(couche, (cx, cy + r + 0.45), (cx, cy + r + 0.95))
    return r + 0.5


ORNEMENTS = {"losange": orn_losange, "cube": orn_cube, "necker": orn_necker, "rosace": orn_rosace,
             "ecrou": orn_ecrou, "mire": orn_mire}


def filet(d, x0, x1, y, ornement="losange", couche="bleu"):
    """Filet horizontal avec un ornement central (None = filet continu)."""
    cx = (x0 + x1) / 2
    if ornement and ornement != "aucun":
        demi = ORNEMENTS[ornement](d, cx, y, couche)
        d.ligne(couche, (x0, y), (cx - demi, y))
        d.ligne(couche, (cx + demi, y), (x1, y))
    else:
        d.ligne(couche, (x0, y), (x1, y))


def filet_vertical(d, x, y0, y1, ornement="losange", couche="bleu"):
    cy = (y0 + y1) / 2
    if ornement and ornement != "aucun":
        demi = ORNEMENTS[ornement](d, x, cy, couche)
        d.ligne(couche, (x, y0), (x, cy - demi))
        d.ligne(couche, (x, cy + demi), (x, y1))
    else:
        d.ligne(couche, (x, y0), (x, y1))


# ----------------------------------------------------------------------------- cadres
def cadre_simple(d, couche="bleu", i=3.0, r=1.6):
    d.poly(couche, rrect_pts(i, i, d.w - 2 * i, d.h - 2 * i, r))


def cadre_double(d, couche="bleu"):
    cadre_simple(d, couche, 2.7, 1.9)
    cadre_simple(d, couche, 3.6, 1.1)


def cadre_equerres(d, couche="bleu", i=3.0, L=6.0, r=1.6):
    """Équerres de coin : suggèrent le cadre et cachent un léger décalage tracé / découpe."""
    x0, y0, x1, y1 = i, i, d.w - i, d.h - i
    for start, (cx, cy), a0, a1, end in (
            ((x0, y0 + L), (x0 + r, y0 + r), 180, 270, (x0 + L, y0)),
            ((x1 - L, y0), (x1 - r, y0 + r), 270, 360, (x1, y0 + L)),
            ((x1, y1 - L), (x1 - r, y1 - r), 0, 90, (x1 - L, y1)),
            ((x0 + L, y1), (x0 + r, y1 - r), 90, 180, (x0, y1 - L))):
        d.poly(couche, [start] + arc_pts(cx, cy, r, a0, a1, 8) + [end])


def cadre_art_deco(d, couche="bleu", i=3.0, r=2.2):
    x0, y0, x1, y1 = i, i, d.w - i, d.h - i
    pts = []
    for (cx, cy, a0) in ((x1, y0, 180), (x1, y1, 270), (x0, y1, 0), (x0, y0, 90)):
        pts += arc_pts(cx, cy, r, a0, a0 - 90, 10)
    d.poly(couche, pts + [pts[0]])


def cadre_vis(d, couche="bleu", i=3.0, r=1.25, dv=6.1):
    """Cadre + 4 vis à tête fendue dans les coins (effet plaque gravée)."""
    cadre_simple(d, couche, i)
    for (x, y), ang in (((dv, dv), 25), ((d.w - dv, dv), 80), ((d.w - dv, d.h - dv), -35), ((dv, d.h - dv), 55)):
        d.cercle(couche, x, y, r, 28)
        a, k = math.radians(ang), r - 0.25
        d.ligne(couche, (x - k * math.cos(a), y - k * math.sin(a)), (x + k * math.cos(a), y + k * math.sin(a)))


CADRES = {"simple": cadre_simple, "double": cadre_double, "equerres": cadre_equerres,
          "art_deco": cadre_art_deco, "vis": cadre_vis}
