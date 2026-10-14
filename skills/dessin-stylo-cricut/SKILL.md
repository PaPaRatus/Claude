---
name: dessin-stylo-cricut
description: "Conçoit des visuels tracés au stylo par une Cricut (Explore, Maker, Joy) ou un traceur : étiquettes, marque-places, faire-part, cartes de vœux, badges, panneaux, motifs géométriques, hachures, guillochés, illustrations au trait, texte à trait unique — livrés en SVG prêt pour Design Space (calques par stylo + découpe) avec aperçu. Utilise ce skill dès qu'on parle de dessiner, écrire ou décorer « au stylo » avec une Cricut, de mode « Stylo/Draw » de Design Space, de police à trait unique (single line font), de fichier SVG pour traceur, ou qu'un visuel doit être tracé puis découpé, même si la demande ne dit pas « SVG ». Pour une carte de visite, préférer le skill carte-visite-cricut."
---

# Visuels au stylo pour Cricut

Un stylo trace des **lignes**, jamais des surfaces. Tout le savoir-faire consiste à exprimer
un visuel avec des traits que Design Space comprend, à la bonne taille pour la pointe, puis à
vérifier le résultat avant que l'utilisateur gâche du papier. La bibliothèque
`scripts/cricut_stylo.py` fait le travail technique ; `scripts/exemple_etiquette.py` est un
modèle complet à copier.

## Déroulé

1. **Cadrer** : format et forme de découpe (rectangle arrondi, cercle, forme libre, ou pas
   de découpe), papier (blanc par défaut ; foncé seulement si demandé, avec stylos gel),
   nombre de stylos (2 recommandé), textes exacts. Relis l'orthographe et la typographie
   française avant de dessiner.
2. **Écrire un script** à partir de `exemple_etiquette.py` : un `Dessin(w, h, decoupe=...)`,
   puis texte, traits, hachures, ornements, cadres (API : `references/api.md`).
3. **Contrôler** : `d.verifier()` (rien à moins de 2,5 mm du bord de découpe), `d.boite()`
   pour mesurer, puis **regarder l'aperçu PNG** (outil de lecture d'image) et zoomer sur les
   détails fins. Juger à l'œil seul ne suffit pas : mesure les marges et les écarts.
4. **Itérer** jusqu'à un rendu net, proposer des variantes sur une planche (`planche()`).
5. **Livrer** le SVG, l'aperçu et le mode d'emploi Design Space ci-dessous.

## Contraintes du stylo (et pourquoi)

| Règle | Valeur | Raison |
|---|---|---|
| Police | Hershey à trait unique (`futural`, `timesr`, `rowmand`…) | une police normale est tracée en contour : lettres creuses, illisibles en petit |
| Hauteur de capitale | ≥ 1,7 mm (1,45 mm en capitales espacées) | la pointe fine fait 0,4 mm ; en dessous les lettres se bouchent |
| Écart entre deux traits parallèles | ≥ 0,8 mm (pas des hachures ≥ 2 × la pointe) | sinon l'encre comble l'espace et fait une tache |
| Marge au bord de découpe | ≥ 2,5 mm | décalage tracé/découpe possible d'environ 0,5 mm |
| Traits de couleurs différentes | ne pas les faire se toucher | deux encres qui se croisent bavent ; laisser un liseré |
| Surfaces pleines | hachures (`hachurer`) ou trame | le stylo ne remplit pas |
| QR codes, aplats, dégradés | à éviter | ingérables au stylo |
| Nombre de stylos | 2 conseillé, 3 maximum | chaque couleur = une pause pour changer de stylo |

La bibliothèque gère d'office : **tracés aller-retour** (Design Space referme les tracés
ouverts ; avec l'aller-retour la fermeture est de longueur nulle), **accents français**
(é è ê ë à â ç î ï ô ù û ü, majuscules accentuées, œ, °), un calque `<path>` par stylo.

## Idées de décors qui marchent au stylo

Hachures à 45° (coupe technique, ombre portée/relief), trames isométriques, guilloché
(ondulations entrelacées), rosace de compas, cube isométrique ou de Necker, équerres de
coin, cotations et flèches, traits mixtes d'axe, règle graduée, cadres art déco, vis à tête
fendue, petites illustrations au trait (une courbe effilée = deux bords qui convergent).
Garder un seul élément fort par visuel ; la sobriété fait le « classe ».

## Mode d'emploi Design Space (à donner à l'utilisateur)

1. **Importer** le SVG, vérifier la taille affichée (proportions verrouillées ; si elle a
   changé, remettre la largeur exacte, tout suit).
2. Chaque calque `n_STYLO_<couleur>` → opération **Stylo** (Draw), choisir la couleur ;
   le calque `DECOUPE_contour` → **Découpe de base**.
3. Tout sélectionner → **Attacher** : sans ça, Design Space répartit les calques sur le
   tapis et le dessin ne tombe plus dans la découpe.
4. Lancer : la machine trace (pause à chaque changement de stylo), puis découpe.
   Premier essai sur papier ordinaire. Stylo extra-fin 0,3 mm pour le petit texte ;
   sur papier foncé, stylos gel (blanc, or, argent).
5. Sans tracé possible (visuel trop dense, photo…), plan B : « Imprimer puis découper »
   avec seulement le contour en découpe.

## Fichiers

- `scripts/cricut_stylo.py` : bibliothèque (Dessin, texte, hachures, ornements, cadres, export, aperçus).
- `scripts/exemple_etiquette.py` : modèle complet (étiquette ronde, texte courbe, hachures, contrôle, aperçu).
- `references/api.md` : toutes les fonctions et leurs paramètres.
