#!/usr/bin/env python3
"""Modèle : étiquette ronde Ø 50 mm (pot, boîte, cadeau) tracée au stylo puis découpée.

Usage : python3 exemple_etiquette.py dossier_sortie/
Copier ce fichier et l'adapter : il montre texte courbe, couronne hachurée, ornement,
contrôle des marges et aperçu.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_stylo import Dessin, orn_rosace  # noqa: E402


def texte_courbe(d, s, cx, cy, R, cap, couche, haut=True, ls=0.35):
    """Lettres posées une à une le long d'un cercle (lecture de gauche à droite)."""
    largeurs = [Dessin.largeur(ch, cap) + ls for ch in s]
    total = sum(largeurs) - ls
    span = total / R                                   # angle couvert (radians)
    pos = -span / 2
    for ch, w in zip(s, largeurs):
        a = pos + (w - ls) / 2 / R
        if haut:
            th = -math.pi / 2 + a
            rot = math.degrees(th) + 90
        else:
            th = math.pi / 2 - a
            rot = math.degrees(th) - 90
        if ch.strip():
            d.texte_tourne(ch, cx + R * math.cos(th), cy + R * math.sin(th), cap, couche, rot)
        pos += w / R


def etiquette():
    D = 50.0
    d = Dessin(D, D, decoupe="cercle", couches=("noir", "bleu"))
    c = D / 2
    # couronne hachurée entre deux cercles (règle pair-impair : l'anneau seul est hachuré)
    ext, inn = 21.5, 19.6
    cercle = lambda r: [(c + r * math.cos(math.radians(a)), c + r * math.sin(math.radians(a)))
                        for a in range(0, 361, 3)]
    d.poly("bleu", cercle(ext))
    d.poly("bleu", cercle(inn))
    d.hachurer("bleu", [cercle(ext), cercle(inn)], angle=45, pas=1.0)
    # textes courbes à l'intérieur de la couronne
    texte_courbe(d, "FAIT MAIN", c, c, 16.6, 2.2, "noir", haut=True, ls=0.6)
    texte_courbe(d, "ATELIER · 2026", c, c, 16.6, 2.0, "noir", haut=False, ls=0.45)
    # centre
    d.texte("Miel", c, c + 1.8, 6.0, "noir", ls=0.3, ancre="middle", police="timesr")
    d.texte("DE MONTAGNE", c, c + 6.6, 1.8, "noir", ls=0.6, ancre="middle")
    orn_rosace(d, c, c - 7.6, "bleu", R=2.1)
    return d


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    d = etiquette()
    fautes = d.verifier(marge=2.0)
    if fautes:
        raise SystemExit(f"Trop près du bord : {fautes[:5]}")
    print("Tracés par stylo :", d.resume(), "| encombrement :", [round(v, 1) for v in d.boite()])
    d.enregistrer(out / "etiquette_ronde.svg")
    print("Aperçu :", d.apercu_png(out / "etiquette_ronde.png"))
