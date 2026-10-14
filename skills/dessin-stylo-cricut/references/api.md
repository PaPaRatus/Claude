# API de `cricut_stylo.py`

Unités : millimètres, origine en haut à gauche, y vers le bas. Angles en degrés
(0° = vers la droite, 90° = vers le bas).

## Dessin

```python
from cricut_stylo import *
d = Dessin(w=85, h=55, decoupe="rrect", r=3.5, couches=("noir", "bleu"), couleurs=None)
```

- `decoupe` : `"rrect"` (coins arrondis de rayon `r`), `"rect"`, `"cercle"` (ellipse inscrite
  dans w × h), `"aucune"`, ou un chemin SVG `d` en mm (forme libre).
- `couches` : noms des stylos, dans l'ordre de passage. Un nom inconnu crée une couche à la volée.
- `couleurs` : couleurs d'affichage supplémentaires `{nom: "#hex"}` (STYLOS contient noir,
  bleu, or, argent, rouge, vert, blanc).

## Tracés

| Méthode | Effet |
|---|---|
| `ligne(couche, p0, p1, ...)` | polyligne par points |
| `poly(couche, pts)` | polyligne depuis une liste |
| `rect(couche, x, y, w, h, r=0)` | rectangle (arrondi si r > 0) |
| `cercle(couche, cx, cy, r, n=None)` | cercle |
| `arc(couche, cx, cy, r, a0, a1)` | arc de a0 à a1 |
| `pointilles(couche, p0, p1, trait=0.9, vide=0.6)` | ligne pointillée |
| `axe(couche, p0, p1)` | trait mixte (axe de dessin technique) |
| `fleche(couche, pointe, direction, L=1.2)` | tête de flèche ouverte |
| `hachurer(couche, polys, angle=45, pas=0.9)` | remplit des polygones fermés (pair-impair : anneaux et trous OK) |
| `motif(couche, polys, x0, y0, largeur, boite=(100,100))` | place un logo défini en polylignes dans son repère ; renvoie les polylignes placées |
| `ombre_hachuree(couche, polys, d=(0.95,0.95), pas=0.95)` | ombre portée hachurée sous des traits (effet relief / gravure) |
| `deplacer(dx, dy, couches=None)` | translate tout (ou certaines couches) |
| `boite(couches=None)` | (xmin, ymin, xmax, ymax) pour mesurer |

## Texte (trait unique)

| Méthode | Effet |
|---|---|
| `texte(s, x, y, cap, couche, ls=0, sx=1, ancre="start", police="futural")` | écrit ; `y` = ligne de base, `cap` = hauteur de capitale en mm, `ls` = espacement ajouté (mm), `sx` = condensation, `ancre` = start/middle/end. Renvoie la largeur. |
| `Dessin.largeur(s, cap, ls, sx, police)` | mesure sans dessiner |
| `texte_ajuste(s, x, y, cap, couche, wmax, ...)` | condense puis réduit pour tenir dans `wmax` ; erreur sous `cap_min` |
| `texte_tourne(s, x, y, cap, couche, angle)` | texte centré sur (x, y) puis tourné |

Polices utiles : `futural` (bâton, la plus lisible), `rowmand` (bâton double, plus grasse),
`timesr` (à empattements), `scripts` (cursive). Texte sur un cercle : place chaque lettre
avec `texte_tourne` à l'angle de la tangente (voir `exemple_etiquette.py`).

## Ornements et cadres

Fonctions `orn_*(d, cx, cy, couche)` — renvoient la demi-largeur occupée (pour couper un filet) :
`losange`, `cube` (isométrique), `necker`, `rosace`, `ecrou`, `mire` ; dictionnaire `ORNEMENTS`.

- `filet(d, x0, x1, y, ornement="losange", couche)` / `filet_vertical(d, x, y0, y1, ...)`
- Cadres `CADRES[nom](d, couche)` : `simple`, `double`, `equerres` (cache le décalage
  tracé/découpe), `art_deco`, `vis` (plaque vissée).
- `rrect_pts(x, y, w, h, r)`, `arc_pts(cx, cy, r, a0, a1, n)` : points utilitaires.

## Contrôle et export

| Méthode | Effet |
|---|---|
| `verifier(marge=2.5)` | liste des points trop près du bord de découpe (vide = OK) |
| `svg(couleurs=None, papier=None, apercu=False)` | SVG Design Space (`apercu=True` : rendu réaliste sur papier, sans la découpe) |
| `enregistrer(chemin)` | écrit le SVG Design Space |
| `apercu_png(chemin, papier=PAPIER_BLANC, couleurs=None)` | aperçu PNG 300 dpi |
| `planche(lignes_svg, chemin_png, page_w, page_h)` | grille de comparaison (liste de lignes de SVG d'aperçu) |
| `resume()` | nombre de tracés par couche |

Aperçus : chromium + pdftoppm (ou `CRICUT_CHROMIUM=/chemin/chrome`), sinon rsvg-convert ou
cairosvg pour un dessin seul. Sans moteur, le SVG reste valide.
