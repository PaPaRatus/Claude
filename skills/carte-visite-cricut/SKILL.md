---
name: carte-visite-cricut
description: "Conçoit tout type de carte de visite « faite main » tracée au stylo et découpée à la Cricut (Design Space) : minimaliste, typographique, monogramme, emblème rond, bandeau à motif, esprit plan technique, recto-verso, formats standard / US / carré / mini, coins arrondis, droits, ronds ou pilule — livrée en SVG prêt à importer avec aperçu et contrôle des marges. Utilise ce skill dès qu'on parle de carte de visite (la créer, la refaire, la décliner, proposer des pistes, choisir un style, un format, un dos de carte) pour une impression au stylo, au traceur, à la Cricut ou en print and cut, pour soi ou pour un client, même si les mots skill ou SVG ne sont pas prononcés."
---

# Cartes de visite au stylo pour Cricut

Objectif : une carte qui ressemble à son propriétaire et à son métier, pas un modèle de plus.
Le générateur `scripts/carte_visite.py` met en page automatiquement 6 gabarits très
différents à partir d'un JSON ; pour tout ce qui sort des gabarits, on dessine sur mesure avec
la bibliothèque `scripts/cricut_stylo.py`. Dans les deux cas, on regarde le résultat avant
de le livrer.

## Déroulé

1. **Comprendre la personne** : métier, clientèle, ton souhaité (sobre, chaleureux,
   technique, artisanal, luxe, ludique), éléments existants (logo, couleurs, ancienne carte).
   Rassembler le contenu exact. Ne demander que ce qui manque.
2. **Relire le texte** avant tout tracé (une coquille au stylo = une série à jeter) :
   typographie française (majuscule au premier mot seulement : « Bureau d’études »,
   apostrophe ’, téléphone `06 23 35 95 60`), vocabulaire juste du métier. Signaler les doutes.
3. **Proposer 3 pistes contrastées** (gabarits ou orientations différents, voir
   `references/design.md` pour choisir selon le métier) dans une seule config avec
   `"variantes"` → une planche de comparaison. Montrer la planche, expliquer chaque piste en
   une phrase, recommander celle qu'on préfère et pourquoi.
4. **Affiner** la piste retenue (ornement, cadre, motif, tailles, recto-verso) ; si un
   besoin dépasse les gabarits, écrire un script sur mesure (section plus bas).
5. **Contrôler** : lire le rapport (marges, plus petit texte, notes de réduction) et
   regarder l'aperçu PNG avec l'outil de lecture d'image, en zoomant sur les zones denses.
   Corriger avant de livrer : un œil extérieur doit trouver la carte nette et équilibrée.
6. **Livrer** SVG + aperçu + mode d'emploi Design Space (ci-dessous) + conseil d'un premier
   essai sur papier ordinaire.

```bash
pip install Hershey-Fonts                      # une fois
python3 scripts/carte_visite.py config.json sortie/
```

## Gabarits (champ `gabarit`, chacun en portrait ou paysage)

| Gabarit | Allure | Pour qui |
|---|---|---|
| `monogramme` | logo en vedette, axe central (portrait) ou identité / infos séparées par un filet (paysage) | marque personnelle forte, artisans, indépendants avec logo |
| `typographique` | grand nom aligné à gauche en haut, coordonnées calées en bas | créatifs, consultants, architectes, profils « éditoriaux » |
| `centre` | minimal, beaucoup de blanc, nom sur une ligne | professions libérales, bien-être, luxe sobre |
| `embleme` | sceau rond avec texte courbe et monogramme | artisans, métiers de bouche, ateliers, marques « maison » |
| `bandeau` | bande de motif (hachures, croisillons, iso, points, lignes) sur un côté | métiers techniques ou graphiques, look affirmé |
| `cartouche` | activités numérotées + tableau façon cartouche de plan | bureaux d'études, ingénieurs, industrie, BTP |

Formats : `standard` 85 × 55, `us` 89 × 51, `carre` 55 × 55, `mini` 70 × 28, ou `[l, h]`.
Formes : `arrondi`, `droit`, `rond`, `pilule`. Verso : `monogramme`, `motif`, `slogan`.
Tous les champs : `references/config.md`.

## Principes qui font une belle carte au stylo (et pourquoi)

- **Hiérarchie claire** : nom > activité > coordonnées > statut. Le stylo n'a qu'une
  épaisseur : la hiérarchie se fait par la taille, l'espacement et la couleur.
- **Deux stylos** : le principal (noir) porte l'information, le secondaire (bleu…) le dessin et
  le second plan (prénom, titre, statut, filets, ornements, cadre). Chaque couleur ajoutée =
  une pause pour changer de stylo et un risque de décalage.
- **Espacer les capitales, jamais les minuscules** (le générateur le fait seul).
- **Un seul élément décoratif fort** ; la sobriété fait le « classe ».
- **Marges** : plus d'air en bas qu'en haut (sinon le contenu paraît tomber) ; le générateur
  centre, réduit le logo si c'est dense, et signale ce qui dépasse.
- **Ce qui se trace mal** : QR codes, aplats, texte sous 1,5 mm de capitale, traits parallèles
  à moins de 0,8 mm. Le générateur bloque tout tracé à moins de 2,5 mm de la découpe.
- **Cadres** : un cadre parallèle au bord révèle le moindre décalage tracé/découpe (≈ 0,5 mm) ;
  les équerres de coin le cachent.

Le détail (choix par métier, contenus, recto-verso, cartes pliées) : `references/design.md`.

## Sur mesure (au-delà des gabarits)

Écrire un script qui importe `cricut_stylo` (API : `references/api.md`) : `Dessin(w, h, decoupe=...)`,
texte à trait unique (droit, tourné, courbe), hachures et motifs, ornements, cadres,
monogramme en polylignes, rainage pour une carte pliée, `verifier()`, `apercu_png()`.
On peut aussi partir d'une carte générée et la compléter : `construire(cfg)` dans
`carte_visite.py` renvoie le `Dessin` avant export.

## Mode d'emploi Design Space (à donner à l'utilisateur)

1. Importer le SVG, vérifier la taille (ex. 85 × 55 mm, proportions verrouillées) ;
   si elle a changé, remettre la largeur exacte, tout suit.
2. Calques `n_STYLO_<couleur>` → opération **Stylo**, choisir la couleur ;
   `RAINAGE_pli` (carte pliée) → **Rainage** ; `DECOUPE_contour` → **Découpe de base**.
3. Tout sélectionner → **Attacher** (sinon les calques sont répartis sur le tapis).
4. La machine trace (pause à chaque changement de stylo), puis découpe. Papier 250–300 g,
   stylo extra-fin 0,3 mm pour les petits textes.
5. Recto-verso : méthode du gabarit décrite dans `references/design.md`.

## Préférences connues de Julien Martin (technicien BE, micro-entreprise)

Carte verticale `monogramme`, papier blanc, noir + bleu sans or, monogramme JM avec ombre
hachurée, cube isométrique dans le filet, équerres de coin, pas d'easter egg.
Config : `examples/julien_martin.json` (reproduit sa carte finale au 1/100 mm).
Ces préférences ne valent que pour lui : pour quelqu'un d'autre, repartir de son métier.
