# Configuration de `carte_visite.py`

Fichier JSON ; seuls les champs utiles sont nécessaires.

## Mise en page

| Champ | Défaut | Valeurs |
|---|---|---|
| `gabarit` | `"monogramme"` | `monogramme`, `typographique`, `centre`, `embleme`, `bandeau`, `cartouche` |
| `orientation` | `"portrait"` | `portrait`, `paysage` |
| `format` | `"standard"` | `standard` (85 × 55), `us` (89 × 51), `carre` (55 × 55), `mini` (70 × 28), ou `[largeur, hauteur]` en mm |
| `forme` | `"arrondi"` | `arrondi`, `droit`, `rond` (format carré), `pilule` (bouts en demi-cercle, idéal en `mini`) |
| `rayon` | `3.5` | rayon des coins (forme `arrondi`) |
| `cadre` | `"auto"` | `equerres`, `simple`, `double`, `art_deco`, `vis`, `aucun` (`auto` = celui du gabarit) |
| `ornement` | `"auto"` | au centre des filets : `cube`, `losange`, `necker`, `rosace`, `ecrou`, `mire`, `aucun` |
| `filet` | `true` | filet séparateur (gabarits monogramme, centre, embleme, verso slogan) |
| `motif` | `"hachures"` | bande du gabarit `bandeau` : `hachures`, `croisillons`, `lignes`, `iso`, `points` |
| `separateur` | `false` | petit point entre activités et coordonnées (monogramme portrait) |
| `stylos` | `{"principal": "noir", "secondaire": "bleu"}` | noms des stylos = noms des calques (noir, bleu, or, argent, rouge, vert, blanc) |
| `monogramme_stylo` | `"principal"` | `principal`, `secondaire` ou un 3ᵉ stylo (ex. `"or"`) |
| `fichier` | `"carte"` | nom de base des fichiers produits |

## Contenu

| Champ | Rôle |
|---|---|
| `nom` | En grand. Capitales conseillées (espacées automatiquement). |
| `prenom` | Plus petit, stylo secondaire (sauf gabarits typographique / centre). |
| `titre` | Fonction ou métier en une ligne (ex. `"ÉBÉNISTE"`), en capitales. |
| `activites` | Liste de lignes courtes (≈ 30 caractères). Trop longue : coupée en deux, puis réduite ; au-delà, erreur explicite. |
| `telephone`, `email`, `site` | Coordonnées (le téléphone en premier est un peu plus grand). |
| `adresse` | Texte ou liste de lignes. |
| `reseaux` | Liste (ex. `["@atelier.durand"]`). |
| `statut` | Ex. `"MICRO-ENTREPRISE"` : dernière ligne, discrète. |
| `slogan` | Texte ou liste de lignes, utilisé par le verso `slogan`. |
| `embleme_haut`, `embleme_bas` | Textes courbes du sceau (défaut : prénom nom / titre ou statut). |

## Monogramme

| Champ | Rôle |
|---|---|
| `monogramme` | `"JM"` (intégré), `"initiales"`, `null`, ou un objet personnalisé (ci-dessous). |
| `monogramme_largeur` | Largeur en mm (sinon taille du gabarit, réduite automatiquement si le contenu est dense). |
| `relief` | `true` : ombre hachurée sous le logo (effet gravure), recentrage optique automatique. |

Logo personnalisé, en traits simples dans un repère de son choix :

```json
"monogramme": {"boite": [100, 93], "polylignes": [[[0, 0], [50.8, 0], [50.8, 67.5]], [[0, 0], [50.8, 46.6], [100, 0], [100, 93]]]}
```

Pour une courbe, échantillonner des points (un tous les 5–6°). Relever un logo existant sur
une photo ou un plan coté, puis vérifier l'aperçu.

## Verso

```json
"verso": {"gabarit": "motif", "motif": "iso"}
"verso": {"gabarit": "monogramme", "monogramme_largeur": 28, "nom": true}
"verso": {"gabarit": "slogan", "texte": ["Le bois,", "dans les règles de l’art"], "police": "timesr"}
```

Produit `<fichier>_verso.svg` / `.png`. Champs facultatifs : `cadre`, `ornement`.

## Variantes

`"variantes": [{...}, {...}]` : chaque objet surcharge la config de base (donner un `fichier`
différent) ; une planche `<fichier>_planche.png` compare toutes les cartes (4 par rangée).
Attention, une variante hérite de tout : préciser `format`, `forme`, `monogramme`… si besoin.

## Exemple : trois pistes pour une ébéniste

```json
{
  "fichier": "durand_monogramme", "nom": "DURAND", "prenom": "Sophie", "titre": "ÉBÉNISTE",
  "activites": ["Agencement sur mesure", "Restauration de meubles"],
  "telephone": "07 12 34 56 78", "email": "sophie@durand-bois.fr",
  "statut": "ENTREPRISE INDIVIDUELLE", "monogramme": "initiales",
  "variantes": [
    {"fichier": "durand_embleme", "gabarit": "embleme", "orientation": "paysage",
     "embleme_haut": "ATELIER DURAND", "embleme_bas": "ÉBÉNISTERIE"},
    {"fichier": "durand_typo", "gabarit": "typographique", "orientation": "paysage", "monogramme": null,
     "verso": {"gabarit": "slogan", "texte": ["Le bois,", "dans les règles de l’art"]}}
  ]
}
```
