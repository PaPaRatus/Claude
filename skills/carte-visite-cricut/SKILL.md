---
name: carte-visite-cricut
description: Crée des cartes de visite « faites main » tracées au stylo et découpées à la Cricut (Design Space), en SVG prêt à importer, dans le style monogramme géométrique + écriture à trait unique + ornements techniques (cube isométrique, équerres de coin, ombre hachurée). Utilise ce skill dès qu'on parle de carte de visite à faire à la Cricut, au stylo, au traceur ou en « print and cut », de refaire ou décliner une carte de visite de ce style (pour soi ou pour un client), de choisir un ornement, un cadre, une orientation ou des couleurs de stylos pour une carte, même si le mot « skill » ou « SVG » n'est pas prononcé.
---

# Cartes de visite au stylo pour Cricut

Le générateur `scripts/carte_visite.py` produit, à partir d'un petit fichier JSON, un SVG que
Design Space sait tracer au stylo puis découper, un aperçu PNG et un rapport de contrôle.
La mise en page est automatique et reprend une carte affinée au millimètre avec son
utilisateur (voir `examples/julien_martin.json`) : ne la refais pas à la main, règle-la par la config.

## Déroulé

1. **Rassembler le contenu.** Demande seulement ce qui manque : nom, prénom, activités
   (3 lignes courtes au maximum), téléphone, e-mail, site éventuel, statut juridique,
   monogramme ou initiales, orientation. Si l'utilisateur a déjà une carte, pars d'elle.
2. **Relire le texte avant de dessiner** (une coquille tracée au stylo, c'est une série à jeter) :
   typographie française (« Bureau d’études » : majuscule au premier mot seulement,
   apostrophe ’), téléphone groupé par deux (`06 23 35 95 60`), bon vocabulaire de métier
   (ex. de la découpe vinyle n'est **pas** de la sérigraphie). Signale les doutes plutôt
   que de deviner.
3. **Écrire la config** (champs : `references/config.md`) et lancer :
   ```bash
   pip install Hershey-Fonts            # une fois
   python3 scripts/carte_visite.py config.json sortie/
   ```
4. **Regarder l'aperçu** (`sortie/<fichier>.png`) avec l'outil de lecture d'image, et lire le
   rapport : marges, plus petit texte, ligne la plus large, notes de réduction. Zoome sur les
   zones denses (recadrage PIL) avant de conclure. Corrige par la config, relance.
5. **Proposer des variantes** si l'utilisateur hésite : liste `"variantes"` dans la config
   (orientation, ornement, cadre…) → une planche `<fichier>_planche.png` pour comparer.
6. **Livrer** le SVG + l'aperçu + le mode d'emploi Design Space ci-dessous, et conseiller un
   premier essai sur papier ordinaire.

## Principes de mise en page (pourquoi ils sont là)

- **Deux stylos par défaut** (noir + bleu) : chaque couleur = un changement de stylo et un
  risque de décalage. Le noir porte l'information (monogramme, nom, activités, contact) ;
  le bleu porte le dessin et le secondaire (ombre, cadre, filet, ornement, prénom, statut).
  Le statut juridique est l'information la moins importante : il reste discret.
- **Ombre hachurée du monogramme** (`relief`) : effet gravure apprécié. Le script recentre
  optiquement le monogramme (l'ombre alourdit la droite) et laisse un liseré blanc entre
  trait et ombre pour que les encres ne se touchent pas.
- **Marges** : le contenu est centré avec un peu plus d'air en bas qu'en haut, sinon il
  paraît tomber. Si le contenu est trop dense, le monogramme rétrécit tout seul ; au-delà,
  le rapport demande de raccourcir.
- **Équerres de coin plutôt que cadre complet** : un cadre parallèle au bord révèle le
  moindre décalage tracé/découpe (≈ 0,5 mm) ; des équerres le cachent. Le cadre complet
  reste possible (`"simple"`, `"double"`, `"vis"`).
- **Pas de QR code** : un stylo ne remplit pas les modules.
- **Tailles** : capitale ≥ 1,7 mm conseillée (stylo fin 0,4 mm) ; 1,45 mm toléré pour une
  ligne en capitales espacées (le statut). Le rapport l'indique.
- **Un seul ornement fort** : le cube (ou autre) au centre du filet sépare déjà les blocs ;
  inutile d'ajouter un séparateur (`"separateur": false`).
- **Nom en capitales espacées**, prénom dessous plus petit : l'écriture cursive Hershey a
  été jugée moins classe. Évite les minuscules espacées.
- **Easter egg** (ex. une tentacule de poulpe sortant d'une équerre) : possible avec la
  bibliothèque, mais seulement si l'utilisateur le demande ; il a été retiré de la carte finale.

## Préférences connues de Julien Martin (technicien BE, micro-entreprise)

Carte verticale, papier blanc (pas de papier noir), bicolore noir + bleu sans or,
monogramme JM avec ombre hachurée, cube isométrique dans le filet, équerres de coin.
Config de référence : `examples/julien_martin.json` (sortie identique à sa carte finale).

## Mode d'emploi Design Space (à donner à l'utilisateur)

1. Importer le SVG, vérifier la taille (55 × 85 mm en vertical, 85 × 55 en paysage,
   proportions verrouillées). Si l'import la change, remettre la largeur : tout suit.
2. Calques `1_STYLO_…`, `2_STYLO_…` → opération **Stylo**, choisir la couleur.
   Calque `…_DECOUPE_contour` → **Découpe de base**.
3. Tout sélectionner → **Attacher** (sinon les éléments sont répartis sur le tapis).
4. La machine trace (pause pour changer de stylo), puis découpe. Papier 250–300 g ;
   stylo extra-fin 0,3 mm conseillé pour le texte noir.

## Aller plus loin

- Champs de configuration, monogramme personnalisé (polylignes) : `references/config.md`.
- Autres décors (ornements, cadres, hachures, texte tourné, cotations) : la bibliothèque
  `scripts/cricut_stylo.py` — pour un visuel hors gabarit, utiliser le skill
  `dessin-stylo-cricut`.
