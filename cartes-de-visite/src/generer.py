#!/usr/bin/env python3
"""Génère les cartes de visite Julien MARTIN (recto / verso) en PDF + PNG.

Usage : python3 generer.py <dossier_polices> <dossier_sortie>
  - dossier_polices : contient fonts_local.css + fonts/*.ttf (Josefin Sans, Barlow)
  - dossier_sortie  : reçoit les PDF et PNG

Format fini 85 x 55 mm. Version impression = +3 mm de fond perdu par côté.
Dépendances : segno, chromium (headless), pdftoppm.
"""
import io
import subprocess
import sys
from pathlib import Path

import segno

FONTS = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)

W, H = 85.0, 55.0
INK = "#12161C"
BLUE = "#1F5FBF"
GRID = "#DCE5F1"

NOM = "Julien MARTIN"
FONCTION = "Bureau d’études"
TEL = "06 23 35 95 60"
MAIL = "martinjulien.be@gmail.com"

# vCard volontairement minimale : moins de modules = QR plus gros à l'impression
VCARD = (
    "BEGIN:VCARD\nVERSION:3.0\n"
    f"FN:{NOM}\nTEL:{TEL.replace(' ', '')}\nEMAIL:{MAIL}\nEND:VCARD"
)


def qr_group(x, y, size):
    """QR vCard en <path> vectoriel (un rectangle par série de modules), carré de `size` mm."""
    qr = segno.make(VCARD, error="l", micro=False)
    n = qr.symbol_size(border=0)[0]
    s = size / n
    d = []
    for r, row in enumerate(qr.matrix):
        c = 0
        while c < n:
            if row[c]:
                c0 = c
                while c < n and row[c]:
                    c += 1
                d.append(f"M{c0} {r}h{c-c0}v1h-{c-c0}z")
            else:
                c += 1
    sw = 0.025 / s  # filet infime : évite les micro-coupures entre rangées
    return (f'<g transform="translate({x} {y}) scale({s:.5f})">'
            f'<path d="{"".join(d)}" fill="{INK}" stroke="{INK}" stroke-width="{sw:.3f}"/></g>')


def monogramme(cx, top, width, stroke=0.45):
    """Monogramme JM en trait fin (repère 100 x 93), centré sur cx."""
    s = width / 100.0
    x0 = cx - width / 2
    sw = stroke / s
    return f'''<g transform="translate({x0:.3f} {top:.3f}) scale({s:.5f})"
  fill="none" stroke="{INK}" stroke-width="{sw:.3f}" stroke-linejoin="miter" stroke-linecap="butt">
  <path d="M0 0 H50.8 V67.5 A25.4 25.4 0 0 1 0 67.5"/>
  <path d="M0 0 L50.8 46.6 L100 0 V93"/>
  <circle cx="50.8" cy="46.6" r="{1.25/s:.2f}" fill="{BLUE}" stroke="none"/>
</g>'''


def fond(b):
    """Papier millimétré + cadre de plan avec croix de coin. Repère = format fini."""
    g = []
    g.append(f'<rect x="{-b}" y="{-b}" width="{W+2*b}" height="{H+2*b}" fill="#FFFFFF"/>')
    # quadrillage 5 mm calé sur le format fini
    lines = []
    x = -5 * int(b // 5 + 1)
    while x <= W + b:
        lines.append(f'<path d="M{x} {-b}V{H+b}"/>')
        x += 5
    y = -5 * int(b // 5 + 1)
    while y <= H + b:
        lines.append(f'<path d="M{-b} {y}H{W+b}"/>')
        y += 5
    g.append(f'<g stroke="{GRID}" stroke-width="0.12" fill="none">{"".join(lines)}</g>')
    # cadre : filets qui dépassent aux coins (style feuille de plan)
    i, o = 4.5, 2.2
    g.append(f'''<g stroke="{INK}" stroke-width="0.22" fill="none">
  <path d="M{i-o} {i}H{W-i+o}"/><path d="M{i-o} {H-i}H{W-i+o}"/>
  <path d="M{i} {i-o}V{H-i+o}"/><path d="M{W-i} {i-o}V{H-i+o}"/></g>''')
    return "".join(g)


def recto(b):
    cx = W / 2
    return f'''{fond(b)}
{monogramme(cx, 9.0, 23.0)}
<g text-anchor="middle" fill="{INK}">
  <text x="{cx+1.1}" y="38.6" font-family="Josefin Sans" font-weight="400"
        font-size="5.6" letter-spacing="2.2">MARTIN</text>
  <text x="{cx+0.8}" y="43.6" font-family="Josefin Sans" font-weight="300"
        font-size="3.1" letter-spacing="2.0">JULIEN</text>
  <text x="{cx+0.4}" y="48.0" font-family="Josefin Sans" font-weight="400"
        font-size="1.9" letter-spacing="0.9" fill="{BLUE}">BUREAU D'ÉTUDES</text>
</g>'''


def verso(b):
    x0, x1 = 9.0, 76.0
    bx = 27.0                       # cartouche
    rows = [("NOM", NOM), ("POSTE", FONCTION), ("TÉL", TEL), ("MAIL", MAIL)]
    rh, top = 4.0, 31.5
    cart = [f'<rect x="{bx}" y="{top}" width="{x1-bx}" height="{rh*4}" '
            f'fill="#FFFFFF" stroke="{INK}" stroke-width="0.22"/>',
            f'<path d="M{bx+10.5} {top}V{top+rh*4}" stroke="{INK}" stroke-width="0.14"/>']
    for k in range(1, 4):
        cart.append(f'<path d="M{bx} {top+rh*k}H{x1}" stroke="{INK}" stroke-width="0.14"/>')
    for k, (lab, val) in enumerate(rows):
        by = top + rh * k + 2.75
        cart.append(f'<text x="{bx+1.2}" y="{by-0.15}" font-family="Josefin Sans" '
                    f'font-weight="400" font-size="1.75" letter-spacing="0.45" fill="{BLUE}">{lab}</text>')
        if k == 0:
            cart.append(f'<text x="{bx+12}" y="{by+0.2}" font-family="Josefin Sans" font-weight="600" '
                        f'font-size="3.3" letter-spacing="0.15" fill="{INK}">{val}</text>')
        elif k == 1:
            cart.append(f'<text x="{bx+12}" y="{by}" font-family="Barlow" font-style="italic" '
                        f'font-size="2.8" fill="{INK}">{val}</text>')
        else:
            cart.append(f'<text x="{bx+12}" y="{by}" font-family="Barlow" font-weight="500" '
                        f'font-size="2.8" letter-spacing="0.1" fill="{INK}">{val}</text>')

    svc = [("01", "Réalisation de plans", None),
           ("02", "Création de composants de bibliothèque", None)]
    t = []
    y = 17.2
    for num, l1, l2 in svc:
        t.append(f'<text x="{x0}" y="{y}" font-family="Josefin Sans" font-weight="600" '
                 f'font-size="2.6" fill="{BLUE}">{num}</text>')
        t.append(f'<text x="{x0+5.2}" y="{y}" font-family="Barlow" font-size="3.1" fill="{INK}">{l1}</text>')
        if l2:
            y += 3.9
            t.append(f'<text x="{x0+5.2}" y="{y}" font-family="Barlow" font-size="2.9" fill="{INK}">{l2}</text>')
        y += 6.2

    head = (f'<text x="{x0}" y="10.4" font-family="Josefin Sans" font-weight="600" font-size="2.3" '
            f'letter-spacing="0.75" fill="{BLUE}">TOPSOLID\'WOOD</text>'
            f'<path d="M{x0+31.5} 9.6H{x1}" stroke="{BLUE}" stroke-width="0.14"/>')

    return f'''{fond(b)}
{head}
{"".join(t)}
<rect x="9" y="31.5" width="16" height="16" fill="#FFFFFF"/>
{qr_group(10.0, 32.5, 14.0)}
{"".join(cart)}'''


def svg(content, b):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W+2*b}mm" height="{H+2*b}mm" '
            f'viewBox="{-b} {-b} {W+2*b} {H+2*b}">{content}</svg>')


def html(b):
    css = (FONTS / "fonts_local.css").read_text()
    css = css.replace("url(fonts/", f"url(file://{FONTS}/fonts/")
    pw, ph = W + 2 * b, H + 2 * b
    return f'''<!doctype html><meta charset="utf-8"><style>
{css}
@page {{ size: {pw}mm {ph}mm; margin: 0 }}
html,body {{ margin:0; padding:0 }}
.p {{ width:{pw}mm; height:{ph}mm; overflow:hidden; page-break-after:always; break-after:page }}
.p:last-child {{ page-break-after:auto; break-after:auto }}
svg {{ display:block }}
</style>
<div class="p">{svg(recto(b), b)}</div>
<div class="p">{svg(verso(b), b)}</div>'''


def build(b, name):
    h = OUT / f"_{name}.html"
    h.write_text(html(b), encoding="utf-8")
    pdf = OUT / f"{name}.pdf"
    subprocess.run(["/opt/pw-browsers/chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--allow-file-access-from-files", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", f"file://{h}"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    h.unlink()
    return pdf


if __name__ == "__main__":
    imp = build(3.0, "cartes-visite_impression_85x55_fond-perdu-3mm")
    fin = build(0.0, "cartes-visite_apercu_85x55")
    for pdf, pref in ((fin, "apercu"),):
        subprocess.run(["pdftoppm", "-r", "400", "-png", str(pdf), str(OUT / f"_{pref}")], check=True)
    for n, nm in (("1", "recto"), ("2", "verso")):
        src = next(OUT.glob(f"_apercu-{n}.png")) if list(OUT.glob(f"_apercu-{n}.png")) else next(OUT.glob(f"_apercu-0{n}.png"))
        src.rename(OUT / f"carte_{nm}.png")
    print("ok", imp, fin)
