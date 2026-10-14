#!/usr/bin/env python3
"""Génère une carte de visite tracée au stylo + découpée à la Cricut, depuis un fichier JSON.

Usage :
    python3 carte_visite.py config.json dossier_sortie/

Produit <fichier>.svg (à importer dans Design Space), <fichier>.png (aperçu papier blanc)
et affiche un rapport de contrôle (marges, tailles de texte, largeurs, calques).
Si la config contient "variantes", produit aussi une planche de comparaison.

Voir references/config.md pour tous les champs.
"""
import copy
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_stylo import (CADRES, PAPIER_BLANC, Dessin, filet, filet_vertical,  # noqa: E402
                          planche)

# ------------------------------------------------------------------ monogrammes
MONO_JM = {  # monogramme JM de Julien Martin, repère 100 x 93
    "boite": [100.0, 93.0],
    "polylignes": [
        [[0, 0], [50.8, 0], [50.8, 67.5]] +
        [[25.4 + 25.4 * math.cos(math.radians(a)), 67.5 + 25.4 * math.sin(math.radians(a))]
         for a in range(0, 181, 6)],
        [[0, 0], [50.8, 46.6], [100, 0], [100, 93]],
    ],
}
MONOGRAMMES = {"JM": MONO_JM}

DEFAUT = {
    "orientation": "portrait",
    "nom": "", "prenom": "", "activites": [], "telephone": "", "email": "", "site": "",
    "statut": "",
    "monogramme": None, "monogramme_largeur": None,
    "relief": True, "ornement": "cube", "filet": True, "cadre": "equerres",
    "separateur": False,
    "stylos": {"principal": "noir", "secondaire": "bleu"},
    "monogramme_stylo": "principal",
    "fichier": "carte",
}

OMBRE = (0.95, 0.95)


def _mono_def(cfg):
    m = cfg["monogramme"]
    if not m:
        return None
    if isinstance(m, str) and m in MONOGRAMMES:
        return MONOGRAMMES[m]
    if isinstance(m, dict):
        return m
    if m == "initiales":
        return "initiales"
    raise SystemExit(f"monogramme inconnu : {m!r} (JM, initiales, ou objet {{boite, polylignes}})")


class Carte:
    """Mise en page commune : couches principal / secondaire (/ accent), rapport."""

    def __init__(self, cfg, w, h):
        self.cfg = cfg
        st = cfg["stylos"]
        couches = [st["principal"], st["secondaire"]]
        acc = cfg["monogramme_stylo"]
        if acc not in ("principal", "secondaire") and acc not in couches:
            couches.append(acc)
        self.P, self.S = st["principal"], st["secondaire"]
        self.M = {"principal": self.P, "secondaire": self.S}.get(acc, acc)
        self.d = Dessin(w, h, couches=couches)
        self.notes = []
        self.tailles = []

    def txt(self, s, x, y, cap, couche, wmax, ls=0.0, sx=1.0, ancre="middle", cap_min=1.6, role=""):
        if not s:
            return 0.0
        w, cap2, sx2 = self.d.texte_ajuste(s, x, y, cap, couche, wmax, ls, sx, ancre, cap_min=cap_min)
        if cap2 < cap - 1e-6:
            self.notes.append(f"« {s} » réduit à {cap2:.2f} mm de capitale (au lieu de {cap:.2f}) pour tenir")
        elif sx2 < sx - 1e-6:
            self.notes.append(f"« {s} » légèrement condensé ({sx2:.2f}) pour tenir")
        self.tailles.append((role or s, cap2, w))
        return w

    def monogramme(self, mdef, x0, y0, mw):
        if mdef == "initiales":
            ini = (self.cfg["prenom"][:1] + self.cfg["nom"][:1]).upper()
            r = mw / 2
            cx, cy = x0 + r, y0 + r
            self.d.cercle(self.M, cx, cy, r * 0.96, 72)
            self.d.texte(ini, cx, cy + mw * 0.2, mw * 0.4, self.M, ls=mw * 0.04, ancre="middle")
            return [], mw
        bw, bh = mdef["boite"]
        polys = self.d.motif(self.M, mdef["polylignes"], x0, y0, mw, (bw, bh))
        return polys, mw * bh / bw

    def finir(self):
        cadre = self.cfg["cadre"]
        if cadre and cadre != "aucun":
            CADRES[cadre](self.d, self.S)
        fautes = self.d.verifier()
        if fautes:
            raise SystemExit(f"tracés trop près du bord de découpe (< 2,5 mm) : {fautes[:4]}")
        return self.d

    def rapport(self, marges):
        d = self.d
        lignes = [f"Format {d.w:g} x {d.h:g} mm, coins arrondis {d.r:g} mm",
                  f"Marges du contenu : haut {marges[0]:.1f} mm, bas {marges[1]:.1f} mm"]
        petit = min(self.tailles, key=lambda t: t[1])
        large = max(self.tailles, key=lambda t: t[2])
        lignes.append(f"Plus petit texte : {petit[0]} ({petit[1]:.2f} mm de capitale)"
                      + ("  ⚠ < 1,7 mm : tester au stylo fin" if petit[1] < 1.7 else ""))
        lignes.append(f"Ligne la plus large : {large[0]} ({large[2]:.1f} mm)")
        cs = [k for k, v in d.couches.items() if v]
        lignes.append(f"Calques stylo : {', '.join(cs)} → {len(cs) - 1} changement(s) de stylo, puis découpe")
        lignes += [f"Note : {n}" for n in self.notes]
        return "\n".join(lignes)


# ------------------------------------------------------------------ portrait 55 x 85
def portrait(cfg):
    c = Carte(cfg, 55.0, 85.0)
    d, P, S = c.d, c.P, c.S
    cx = 27.5
    mdef = _mono_def(cfg)
    y = top = 0.0                          # le contenu commence à y = 0 puis est recentré
    if mdef:
        mw = cfg["monogramme_largeur"] or 21.0
        ombre = cfg["relief"] and mdef != "initiales"
        dx = -OMBRE[0] / 2 if ombre else 0.0          # l'ombre alourdit la droite : recentrage optique
        polys, mh = c.monogramme(mdef, cx - mw / 2 + dx, y, mw)
        if ombre:
            d.ombre_hachuree(S, polys, OMBRE)
        y += mh + (OMBRE[1] if ombre else 0.0) + 4.3
    nom_bl = y + 4.4
    c.txt(cfg["nom"], cx, nom_bl, 4.4, P, 40.0, ls=1.7, role="nom")
    bl = nom_bl
    if cfg["prenom"]:
        bl = nom_bl + 4.4
        c.txt(cfg["prenom"], cx, bl, 2.4, S, 38.0, ls=1.75, role="prénom")
    acts = cfg["activites"]
    if acts:
        act_bl = bl + 9.6
        if cfg["filet"]:
            filet(d, 12.0, 43.0, (bl + act_bl - 1.95) / 2, cfg["ornement"], S)
        for k, t in enumerate(acts):
            c.txt(t, cx, act_bl + k * 4.2, 1.95, P, 41.0, ls=0.04, sx=0.88, role="activité")
        bl = act_bl + (len(acts) - 1) * 4.2
        if cfg["separateur"]:
            d.cercle(S, cx, bl + 3.0, 0.35, 12)
        bl += 9.0
    else:
        if cfg["filet"]:
            filet(d, 12.0, 43.0, bl + 3.8, cfg["ornement"], S)
        bl += 10.0
    premier = True
    for champ, cap, sx, ls in (("telephone", 2.4, 1.0, 0.14), ("email", 1.95, 0.88, 0.03),
                               ("site", 1.95, 0.88, 0.03)):
        if cfg[champ]:
            if not premier:
                bl += 4.6
            c.txt(cfg[champ], cx, bl, cap, P, 41.0, ls=ls, sx=sx, role=champ)
            premier = False
    if cfg["statut"]:
        bl += 4.4
        c.txt(cfg["statut"], cx, bl, 1.45, S, 40.0, ls=0.55, cap_min=1.4, role="statut")
    # centrage vertical : un peu plus d'air en bas qu'en haut (sinon le contenu paraît tomber)
    hauteur = bl - top
    t = (85.0 - hauteur - 0.4) / 2
    d.deplacer(0, t - top)
    c.finir()
    marges = (t, 85.0 - t - hauteur)
    return d, c.rapport(marges), marges


# ------------------------------------------------------------------ paysage 85 x 55
def paysage(cfg):
    c = Carte(cfg, 85.0, 55.0)
    d, P, S = c.d, c.P, c.S
    # colonne gauche : monogramme + nom (dessinés à y=0 puis recentrés)
    gauche = Dessin(85, 55, couches=list(d.couches))
    c.d = gauche
    xL = 19.5
    mdef = _mono_def(cfg)
    y = 0.0
    if mdef:
        mw = cfg["monogramme_largeur"] or 18.5
        ombre = cfg["relief"] and mdef != "initiales"
        dx = -OMBRE[0] / 2 if ombre else 0.0
        polys, mh = c.monogramme(mdef, xL - mw / 2 + dx, 0.0, mw)
        if ombre:
            gauche.ombre_hachuree(S, polys, OMBRE)
        y = mh + (OMBRE[1] if ombre else 0.0) + 4.3
    bl = y + 3.5
    c.txt(cfg["nom"], xL, bl, 3.5, P, 27.0, ls=1.35, role="nom")
    if cfg["prenom"]:
        bl += 4.5
        c.txt(cfg["prenom"], xL, bl, 2.0, S, 26.0, ls=1.4, role="prénom")
    top_g, hg = 0.0, bl                     # le bloc gauche commence à y = 0 (monogramme ou nom)
    # colonne droite
    droite = Dessin(85, 55, couches=list(d.couches))
    c.d = droite
    X, wmax = 40.0, 37.0
    bl2 = 1.95
    for k, t in enumerate(cfg["activites"]):
        c.txt(t, X, bl2 + k * 4.2, 1.95, P, wmax, ls=0.04, sx=0.88, ancre="start", role="activité")
    if cfg["activites"]:
        bl2 += (len(cfg["activites"]) - 1) * 4.2
        droite.ligne(S, (X, bl2 + 4.0), (X + 4.0, bl2 + 4.0))
        bl2 += 10.4
    premier = True
    for champ, cap, sx, ls in (("telephone", 2.4, 1.0, 0.14), ("email", 1.95, 0.88, 0.03),
                               ("site", 1.95, 0.88, 0.03)):
        if cfg[champ]:
            if not premier:
                bl2 += 4.6
            c.txt(cfg[champ], X, bl2, cap, P, wmax, ls=ls, sx=sx, ancre="start", role=champ)
            premier = False
    if cfg["statut"]:
        bl2 += 5.6
        c.txt(cfg["statut"], X, bl2, 1.45, S, wmax, ls=0.55, ancre="start", cap_min=1.4, role="statut")
    hd = bl2
    # recentrage vertical de chaque colonne, puis fusion
    tg = (55.0 - (hg - top_g) - 0.4) / 2
    td = (55.0 - hd - 0.4) / 2
    gauche.deplacer(0, tg - top_g)
    droite.deplacer(0, td)
    for src in (gauche, droite):
        for k, v in src.couches.items():
            d.couches[k] += v
    c.d = d
    if cfg["filet"]:
        filet_vertical(d, 36.0, min(tg, td) + 0.5, max(tg + hg - top_g, td + hd), cfg["ornement"], S)
    c.finir()
    marges = (min(tg, td), 55.0 - max(tg + hg - top_g, td + hd))
    return d, c.rapport(marges), marges


def couper(texte, wmax, cap=1.95, ls=0.04, sx=0.82):
    """Coupe une activité en deux lignes équilibrées (au mot près), seulement si elle devrait
    sinon descendre sous 1,75 mm de capitale pour tenir sur une ligne."""
    if Dessin.largeur(texte, cap, ls, sx) <= wmax * cap / 1.75:
        return [texte]
    mots = texte.split()
    meilleur = None
    for i in range(1, len(mots)):
        a, b = " ".join(mots[:i]), " ".join(mots[i:])
        w = max(Dessin.largeur(a, cap, ls, sx), Dessin.largeur(b, cap, ls, sx))
        if meilleur is None or w < meilleur[0]:
            meilleur = (w, [a, b])
    if meilleur is None or meilleur[0] > wmax * 1.25:      # au-delà, la réduction de taille serait trop forte
        raise SystemExit(f"Activité trop longue même sur deux lignes : « {texte} ». Raccourcir le libellé.")
    return meilleur[1]


def construire(cfg):
    full = copy.deepcopy(DEFAUT)
    full.update(cfg)
    full["stylos"] = {**DEFAUT["stylos"], **cfg.get("stylos", {})}
    wmax = 41.0 if full["orientation"] == "portrait" else 37.0
    full["activites"] = [ligne for t in full["activites"] for ligne in couper(t, wmax)]
    if full["orientation"] not in ("portrait", "paysage"):
        raise SystemExit("orientation : portrait ou paysage")
    fn = portrait if full["orientation"] == "portrait" else paysage
    # trop de contenu : on réduit le monogramme jusqu'à retrouver >= 6,5 mm de marge haute
    mw = full["monogramme_largeur"] or (21.0 if fn is portrait else 18.5)
    while True:
        full["monogramme_largeur"] = mw
        d, rapport, marges = fn(full)
        if min(marges) >= 6.5 or not full["monogramme"] or mw <= 13.0:
            break
        mw -= 1.0
    if min(marges) < 6.5:
        rapport += "\n⚠ Marge < 6,5 mm : contenu trop dense, retirer une ligne ou raccourcir les textes"
    elif full["monogramme_largeur"] < (21.0 if fn is portrait else 18.5) and not cfg.get("monogramme_largeur"):
        rapport += f"\nNote : monogramme réduit à {mw:g} mm de large pour garder des marges confortables"
    return d, rapport, full


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    variantes = cfg.pop("variantes", None)
    cartes = []
    for v in ([{}] + (variantes or [])):
        conf = {**cfg, **v}
        try:
            d, rapport, full = construire(conf)
        except ValueError as e:
            raise SystemExit(f"Texte impossible à caser : {e}. Raccourcir ce texte ou réduire le contenu.")
        nom = full["fichier"]
        d.enregistrer(out / f"{nom}.svg")
        d.apercu_png(out / f"{nom}.png")
        cartes.append(d)
        print(f"=== {nom}.svg\n{rapport}\n")
    if variantes:
        hmax = max(c.h for c in cartes)
        larg = sum(c.w for c in cartes) + 6 * (len(cartes) - 1) + 16
        planche([[c.svg(papier=PAPIER_BLANC, apercu=True) for c in cartes]],
                out / f"{cfg.get('fichier', 'carte')}_planche.png", larg, hmax + 14)
        print(f"Planche de comparaison : {cfg.get('fichier', 'carte')}_planche.png")


if __name__ == "__main__":
    main()
