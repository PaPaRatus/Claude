#!/usr/bin/env python3
"""Sélection : monogramme en relief hachuré + cube isométrique (F03) + cadres F07 / F10 / F11.

Usage : python3 cricut_final.py <dossier_sortie>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_lib import GEL, render_png                                    # noqa: E402
from cricut_styles import nom_capitales, signature                         # noqa: E402
from cricut_deco import relief                                             # noqa: E402
from cricut_deco2 import cadre_equerres, cadre_simple, orn_cube, paysage   # noqa: E402


def vertical(cadre):
    c = signature(nom_capitales, ornement=orn_cube, deco=relief)
    cadre(c)
    return c


SELECTION = [
    ("H1_vertical_cube_cadre", lambda: vertical(cadre_simple)),
    ("H2_vertical_cube_equerres", lambda: vertical(cadre_equerres)),
    ("H3_paysage_cube_cadre", lambda: paysage(orn_cube, relief, cadre_simple)),
    ("H4_paysage_cube_equerres", lambda: paysage(orn_cube, relief, cadre_equerres)),
]

if __name__ == "__main__":
    OUT = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    cartes = []
    for name, fn in SELECTION:
        c = fn()
        c.check()
        (OUT / f"carte_cricut_{name}.svg").write_text(c.svg(), encoding="utf-8")
        cartes.append(c)
        print(name, f"{c.w:g}x{c.h:g}", {k: len(v) for k, v in c.layers.items()})
    for suffix, kw in (("", dict(paper="#FBFAF6")), ("_papier-noir", dict(pens=GEL, paper="#1C1F24"))):
        render_png([[c.svg(preview=True, **kw) for c in cartes[:2]] +
                    [c.svg(preview=True, **kw) for c in cartes[2:]]],
                   OUT / f"apercu_H_selection{suffix}.png", page_w=2 * 55 + 2 * 85 + 3 * 6 + 16,
                   page_h=85 + 14)
