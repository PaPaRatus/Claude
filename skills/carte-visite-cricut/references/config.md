# Configuration de `carte_visite.py`

Fichier JSON. Seuls les champs utiles sont nécessaires ; les autres prennent la valeur par défaut.

| Champ | Défaut | Rôle |
|---|---|---|
| `fichier` | `"carte"` | Nom de base des fichiers produits (`.svg`, `.png`). |
| `orientation` | `"portrait"` | `"portrait"` (55 × 85 mm) ou `"paysage"` (85 × 55 mm). |
| `nom` | `""` | Ligne principale, en grand. Conseillé en CAPITALES (espacées automatiquement). |
| `prenom` | `""` | Sous le nom, plus petit, stylo secondaire. Capitales conseillées. |
| `activites` | `[]` | Liste de lignes courtes (≈ 30 caractères max). Une ligne trop longue est coupée en deux, puis réduite ; au-delà, erreur explicite. |
| `telephone` | `""` | Format français groupé : `"06 23 35 95 60"`. |
| `email` | `""` | En minuscules. |
| `site` | `""` | Facultatif, sous l'e-mail. |
| `statut` | `""` | Ex. `"MICRO-ENTREPRISE"` : dernière ligne, petite, stylo secondaire. |
| `monogramme` | `null` | `"JM"` (intégré), `"initiales"` (initiales dans un cercle), un objet personnalisé (ci-dessous) ou `null`. |
| `monogramme_largeur` | auto | 21 mm (portrait) / 18,5 mm (paysage) ; réduit automatiquement si le contenu est dense. |
| `relief` | `true` | Ombre hachurée sous le monogramme (sauf `"initiales"`). |
| `filet` | `true` | Filet séparateur (horizontal en portrait, vertical en paysage). |
| `ornement` | `"cube"` | Au centre du filet : `cube`, `losange`, `necker`, `rosace`, `ecrou`, `mire`, `aucun`. |
| `cadre` | `"equerres"` | `equerres`, `simple`, `double`, `art_deco`, `vis`, `aucun`. |
| `separateur` | `false` | Petit point entre activités et coordonnées (portrait). |
| `stylos` | `{"principal": "noir", "secondaire": "bleu"}` | Noms des stylos (= noms des calques). Couleurs connues : noir, bleu, or, argent, rouge, vert, blanc. |
| `monogramme_stylo` | `"principal"` | `"principal"`, `"secondaire"` ou le nom d'un 3ᵉ stylo (ex. `"or"`) → 3 calques. |
| `variantes` | — | Liste d'objets qui surchargent la config (avec leur propre `fichier`) → une planche de comparaison. |

## Monogramme personnalisé

Décris le logo en polylignes (traits simples, pas de surfaces) dans un repère de ton choix :

```json
"monogramme": {
  "boite": [100, 93],
  "polylignes": [
    [[0, 0], [50.8, 0], [50.8, 67.5]],
    [[0, 0], [50.8, 46.6], [100, 0], [100, 93]]
  ]
}
```

`boite` = largeur et hauteur du repère ; le logo est mis à l'échelle de `monogramme_largeur`.
Pour une courbe, échantillonne des points (un arc tous les 5–6°). Pour reprendre un logo
existant, relève ses points sur une photo ou un plan coté, puis vérifie l'aperçu.

## Exemple minimal

```json
{
  "fichier": "dupont",
  "nom": "DUPONT",
  "prenom": "CLAIRE",
  "activites": ["Architecture d’intérieur", "Conseil couleur"],
  "telephone": "06 11 22 33 44",
  "email": "claire@dupont-interieur.fr",
  "statut": "ENTREPRISE INDIVIDUELLE",
  "monogramme": "initiales",
  "ornement": "losange",
  "variantes": [{"fichier": "dupont_paysage", "orientation": "paysage"}]
}
```
