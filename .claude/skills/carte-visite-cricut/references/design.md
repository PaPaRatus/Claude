# Concevoir une carte de visite au stylo

## Sommaire
1. Choisir une direction selon le métier
2. Contenu : quoi mettre, quoi retirer
3. Typographie et tailles
4. Stylos, papiers, combinaisons qui marchent
5. Recto-verso : la méthode du gabarit
6. Cartes pliées, formes spéciales, sur mesure
7. Liste de contrôle avant livraison

## 1. Choisir une direction selon le métier

Toujours proposer **trois pistes contrastées** (gabarits ou orientations différents), puis
affiner celle qui plaît. Points de départ :

| Univers | Gabarits à essayer | Décors adaptés |
|---|---|---|
| Bureau d'études, ingénierie, industrie, BTP | `monogramme`, `cartouche`, `bandeau` (hachures) | cube, écrou, mire, équerres, hachures de coupe |
| Artisanat (bois, métal, cuir, céramique) | `embleme`, `monogramme`, `bandeau` (iso, croisillons) | sceau, rosace, ombre hachurée, cadre vis |
| Créatifs, architectes, designers | `typographique`, `centre` | presque rien : un trait, beaucoup de blanc |
| Professions libérales, conseil, santé | `centre`, `typographique` | losange, filet fin, pas de cadre |
| Bien-être, beauté, mariage, luxe | `centre`, `embleme` | rosace, art déco, papier ivoire, stylo or |
| Métiers de bouche, commerces, ateliers | `embleme`, `bandeau` (points, lignes) | sceau, texte courbe, slogan au verso |

Un logo existant prime : on le redessine en traits (monogramme personnalisé) plutôt que
d'inventer. Sans logo, les initiales dans un cercle ou un sceau suffisent.

## 2. Contenu : quoi mettre, quoi retirer

- **Indispensable** : nom, activité (en mots compréhensibles par un client), un moyen de
  contact sûr (téléphone mobile, e-mail).
- **Utile** : site, ville, réseau social principal, statut (micro-entreprise…).
- **À éviter** : plus de 3 lignes d'activité, adresse complète si elle n'apporte rien,
  plusieurs numéros, slogans creux, QR code (intraçable au stylo).
- Aucune mention légale n'est obligatoire sur une carte de visite (le SIRET l'est sur les
  devis et factures) ; l'ajouter seulement si la personne le souhaite.
- Le dos est un bon endroit pour le logo en grand, un motif ou une phrase : il allège le recto.

## 3. Typographie et tailles

- Hauteur de capitale : nom 3–5,5 mm, coordonnées ≥ 1,8 mm, mentions ≥ 1,45 mm (en capitales
  espacées). Sous 1,7 mm, tester au stylo extra-fin 0,3 mm.
- Espacer les capitales (0,5 à 1,7 mm), jamais les minuscules.
- Majuscule au premier mot seulement (« Bureau d’études »), apostrophe ’, espaces dans le
  téléphone (`06 23 35 95 60`), e-mail en minuscules.
- Polices Hershey : `futural` (bâton, la plus lisible, défaut), `timesr` (à empattements,
  pour un slogan ou un nom classique), `rowmand` (bâton double, plus gras). La cursive
  `scripts` fait vite « faire-part » : à réserver aux univers qui l'assument.
- Le vocabulaire du métier doit être exact (ex. découpe de vinyle adhésif ≠ sérigraphie).

## 4. Stylos, papiers, combinaisons qui marchent

| Papier | Stylos | Effet |
|---|---|---|
| Blanc ou ivoire 250–300 g, lisse ou texturé | noir + bleu | net, technique (choix de Julien) |
| Ivoire, kraft clair | noir + or | chaleureux, artisanal |
| Kraft | noir + blanc gel | brut, atelier |
| Noir ou bleu nuit | blanc gel + or ou argent | luxe, effet « wahou » (uniquement si demandé) |

Deux stylos par défaut ; trois au maximum (`monogramme_stylo: "or"`).

## 5. Recto-verso : la méthode du gabarit

Le stylo trace une face à la fois. Pour que le verso tombe juste :

1. Tracer et découper les **rectos** (dessin attaché à la découpe), comme d'habitude.
2. Sans bouger la feuille, retirer les cartes : la chute restée sur le tapis devient un
   **gabarit** avec des fenêtres exactement à la place des cartes.
3. Retourner chaque carte **de gauche à droite** (le haut reste en haut) et la reposer dans
   sa fenêtre.
4. Dans Design Space, ouvrir le verso et le placer au **même endroit sur le tapis** que le
   recto (mêmes coordonnées X / Y dans l'écran de préparation), calque de découpe désactivé
   (tracer seulement).
5. Lancer le tracé. Faire un premier essai sur papier ordinaire.

Le verso n'a pas besoin d'être inversé en miroir : la carte est symétrique et on la retourne
de gauche à droite. Une carte ronde ou carrée doit garder son repère (une petite encoche au
crayon au dos aide). Variante plus simple : imprimer le verso, ou tracer un verso très
centré (logo seul) qui pardonne un léger décalage.

## 6. Cartes pliées, formes spéciales, sur mesure

- **Carte pliée** (ex. 85 × 110 mm pliée en 85 × 55) : script sur mesure avec
  `d.rainure((0, 55), (85, 55))` → calque `RAINAGE_pli` (opération Rainage, stylet ou
  molette). Le contenu du panneau du haut est tourné de 180° si la carte se plie vers
  l'arrière (`texte_tourne`, ou dessiner puis transformer les points).
- **Forme libre** : `Dessin(..., decoupe="<chemin SVG en mm>")` (encoche, onglet, hexagone…) ;
  vérifier les marges à la main (`verifier()` ne connaît que rectangle, coins arrondis et cercle).
- **Partir d'un gabarit et compléter** : `(d, rapport), verso, cfg = construire(cfg)` dans
  `carte_visite.py`, puis ajouter des tracés à `d` et appeler `d.enregistrer()` /
  `d.apercu_png()`.
- **Easter egg** (petit dessin caché, ex. tentacule sortant d'une équerre) : seulement sur
  demande, petit, dans un coin libre, de la couleur secondaire ; il ne doit jamais concurrencer
  le nom.

## 7. Liste de contrôle avant livraison

- [ ] Texte relu : orthographe, majuscules, apostrophes, numéro, e-mail.
- [ ] Rapport sans ⚠ bloquant ; plus petit texte ≥ 1,45 mm ; marges équilibrées.
- [ ] Aperçu regardé et zoomé : rien ne se touche, les encres de couleurs différentes ne se
      chevauchent pas, l'ornement est net.
- [ ] Hiérarchie lisible à 1 m : on voit le nom, puis le métier.
- [ ] Mode d'emploi Design Space fourni, premier essai sur papier ordinaire conseillé.
