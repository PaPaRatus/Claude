#!/usr/bin/env python3
"""Génère des cartes de visite tracées au stylo + découpées à la Cricut, depuis un JSON.

Usage :
    python3 carte_visite.py config.json dossier_sortie/

Pour chaque carte : <fichier>.svg (Design Space), <fichier>.png (aperçu papier blanc),
<fichier>_verso.svg/.png si un verso est demandé, et un rapport de contrôle.
"variantes" dans la config → une planche de comparaison <fichier>_planche.png.

Gabarits : monogramme, typographique, centre, embleme, bandeau, cartouche
(chacun en portrait ou paysage). Champs : references/config.md.
"""
import copy
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cricut_stylo import (CADRES, PAPIER_BLANC, Dessin, filet,  # noqa: E402
                          filet_vertical, planche, rrect_pts)

# ------------------------------------------------------------------ données
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
FORMATS = {"standard": (85.0, 55.0), "us": (89.0, 51.0), "carre": (55.0, 55.0), "mini": (70.0, 28.0)}
FORMES = {"arrondi": "rrect", "droit": "rect", "rond": "cercle", "pilule": "rrect"}
GABARIT_AUTO = {  # ornement / cadre quand la config dit "auto"
    "monogramme": ("cube", "equerres"), "typographique": ("aucun", "aucun"),
    "centre": ("losange", "aucun"), "embleme": ("losange", "aucun"),
    "bandeau": ("losange", "aucun"), "cartouche": ("aucun", "equerres"),
}
DEFAUT = {
    "gabarit": "monogramme", "orientation": "portrait", "format": "standard",
    "forme": "arrondi", "rayon": 3.5,
    "nom": "", "prenom": "", "titre": "", "activites": [], "telephone": "", "email": "",
    "site": "", "adresse": [], "reseaux": [], "statut": "", "slogan": "",
    "monogramme": None, "monogramme_largeur": None, "relief": True,
    "ornement": "auto", "filet": True, "cadre": "auto", "motif": "hachures",
    "separateur": False, "embleme_haut": None, "embleme_bas": None,
    "stylos": {"principal": "noir", "secondaire": "bleu"}, "monogramme_stylo": "principal",
    "verso": None, "fichier": "carte",
}
OMBRE = (0.95, 0.95)


# ------------------------------------------------------------------ moteur
class Carte:
    def __init__(self, cfg):
        self.cfg = cfg
        fm = cfg["format"]
        w, h = (float(fm[0]), float(fm[1])) if isinstance(fm, (list, tuple)) else FORMATS[fm]
        if w != h and (cfg["orientation"] == "portrait") == (w > h):
            w, h = h, w
        self.w, self.h = w, h
        self.forme = FORMES[cfg["forme"]]
        self.r = min(w, h) / 2 if cfg["forme"] == "pilule" else cfg["rayon"]
        st = cfg["stylos"]
        self.P, self.S = st["principal"], st["secondaire"]
        acc = cfg["monogramme_stylo"]
        self.M = {"principal": self.P, "secondaire": self.S}.get(acc, acc)
        self.couches = list(dict.fromkeys([self.P, self.S, self.M]))
        self.d = self.neuf()
        self.decor = self.neuf()      # décors de bord (bande, motif) : hors calcul des marges du contenu
        self.cible = self.d
        self.notes, self.tailles = [], []
        g = cfg["gabarit"]
        self.ornement = GABARIT_AUTO[g][0] if cfg["ornement"] == "auto" else cfg["ornement"]
        self.cadre = GABARIT_AUTO[g][1] if cfg["cadre"] == "auto" else cfg["cadre"]

    def neuf(self):
        return Dessin(self.w, self.h, decoupe=self.forme, r=self.r, couches=self.couches)

    # ---------------------------------------------------- contenu
    def mono_def(self):
        m = self.cfg["monogramme"]
        if not m:
            return None
        if isinstance(m, str) and m in MONOGRAMMES:
            return MONOGRAMMES[m]
        if isinstance(m, dict) or m == "initiales":
            return m
        raise SystemExit(f"monogramme inconnu : {m!r} (JM, initiales, ou objet {{boite, polylignes}})")

    def contacts(self):
        c = self.cfg
        adr = c["adresse"] if isinstance(c["adresse"], list) else [c["adresse"]]
        return [t for t in [c["telephone"], c["email"], c["site"], *adr, *c["reseaux"]] if t]

    def lignes(self, textes, wmax, cap=1.95):
        """Coupe en deux une ligne qui devrait sinon descendre sous 1,75 mm de capitale."""
        out = []
        for t in textes:
            if Dessin.largeur(t, cap, 0.04, 0.82) <= wmax * cap / 1.75:
                out.append(t)
                continue
            mots = t.split()
            best = min(((max(Dessin.largeur(" ".join(mots[:i]), cap, 0.04, 0.82),
                             Dessin.largeur(" ".join(mots[i:]), cap, 0.04, 0.82)), i)
                        for i in range(1, len(mots))), default=(1e9, 0))
            if best[0] > wmax * 1.25:
                raise SystemExit(f"Texte trop long même sur deux lignes : « {t} ». Raccourcir.")
            out += [" ".join(mots[:best[1]]), " ".join(mots[best[1]:])]
        return out

    # ---------------------------------------------------- dessin de base
    def txt(self, s, x, y, cap, couche, wmax, ls=0.0, sx=1.0, ancre="middle", cap_min=1.6,
            police="futural", role=""):
        if not s:
            return 0.0
        if any(ch.islower() for ch in s):    # typographie : on n'espace pas les minuscules
            ls = min(ls, 0.25)
        try:
            w, cap2, sx2 = self.cible.texte_ajuste(s, x, y, cap, couche, wmax, ls, sx, ancre, police,
                                                   cap_min=cap_min)
        except ValueError as e:
            raise SystemExit(f"Texte impossible à caser : {e}. Raccourcir ce texte.")
        if cap2 < cap - 1e-6:
            self.notes.append(f"« {s} » réduit à {cap2:.2f} mm de capitale (au lieu de {cap:.2f})")
        elif sx2 < sx - 1e-6:
            self.notes.append(f"« {s} » légèrement condensé ({sx2:.2f})")
        self.tailles.append((role or s, cap2, w))
        return w

    def mono(self, x0, y0, mw, relief=None):
        """Dessine le monogramme (coin haut-gauche x0, y0) ; renvoie sa hauteur, ombre comprise."""
        mdef = self.mono_def()
        relief = self.cfg["relief"] if relief is None else relief
        if mdef == "initiales":
            ini = (self.cfg["prenom"][:1] + self.cfg["nom"][:1]).upper()
            r = mw / 2
            self.cible.cercle(self.M, x0 + r, y0 + r, r * 0.96, 72)
            self.cible.texte(ini, x0 + r, y0 + r + mw * 0.2, mw * 0.4, self.M, ls=mw * 0.04, ancre="middle")
            return mw
        bw, bh = mdef["boite"]
        dx = -OMBRE[0] / 2 if relief else 0.0           # l'ombre alourdit la droite : recentrage optique
        polys = self.cible.motif(self.M, mdef["polylignes"], x0 + dx, y0, mw, (bw, bh))
        if relief:
            self.cible.ombre_hachuree(self.S, polys, OMBRE)
        return mw * bh / bw + (OMBRE[1] if relief else 0.0)

    def mono_h(self, mw):
        mdef = self.mono_def()
        if mdef == "initiales":
            return mw
        return mw * mdef["boite"][1] / mdef["boite"][0] + (OMBRE[1] if self.cfg["relief"] else 0.0)

    def pile(self, items, x, ancre="middle"):
        """Empile des éléments à partir de y = 0 dans un fragment ; renvoie (fragment, hauteur).
        Éléments : ("mono", largeur) ("txt", texte, cap, couche, wmax, options) ("esp", h)
        ("filet", largeur) ("trait", largeur) ("point",)."""
        frag = self.neuf()
        self.cible = frag
        y = 0.0
        for it in items:
            k = it[0]
            if k == "esp":
                y += it[1]
            elif k == "mono":
                mw = it[1]
                y += self.mono(x - mw / 2 if ancre == "middle" else x, y, mw)
            elif k == "txt":
                _, s, cap, couche, wmax, opt = it
                if s:
                    self.txt(s, x, y + cap, cap, couche, wmax, ancre=ancre, **opt)
                    y += cap
            elif k in ("filet", "trait"):
                L = it[1]
                x0 = x - L / 2 if ancre == "middle" else x
                if k == "filet":
                    filet(frag, x0, x0 + L, y, self.ornement, self.S)
                else:
                    frag.ligne(self.S, (x0, y), (x0 + L, y))
            elif k == "point":
                frag.cercle(self.S, x, y, 0.35, 12)
        self.cible = self.d
        return frag, y

    def poser(self, frag, dx=0.0, dy=0.0):
        frag.deplacer(dx, dy)
        for k, v in frag.couches.items():
            self.d.couches.setdefault(k, []).extend(v)

    def centrer_v(self, h, haut=0.0, bas=None):
        """Haut d'un bloc de hauteur h centré dans [haut, bas], avec un peu plus d'air en bas."""
        bas = self.h if bas is None else bas
        return haut + (bas - haut - h - 0.4) / 2

    # ---------------------------------------------------- blocs réutilisables
    def items_contacts(self, cap1=2.4, cap=1.95, pas=4.6, sx=0.88, wmax=41.0):
        items = []
        for i, t in enumerate(self.contacts()):
            tel = i == 0 and t == self.cfg["telephone"]
            c_ = cap1 if tel else cap
            if i:
                items.append(("esp", pas - c_))
            items.append(("txt", t, c_, self.P, wmax,
                          dict(ls=0.14 if tel else 0.03, sx=1.0 if tel else sx, role="contact")))
        return items

    def items_statut(self, avant, wmax=40.0, cap=1.45):
        if not self.cfg["statut"]:
            return []
        return [("esp", avant), ("txt", self.cfg["statut"], cap, self.S, wmax,
                                 dict(ls=0.55, cap_min=1.4, role="statut"))]

    def items_acts(self, wmax, cap=1.95, pas=4.2, sx=0.88):
        items = []
        for i, t in enumerate(self.lignes(self.cfg["activites"], wmax, cap)):
            if i:
                items.append(("esp", pas - cap))
            items.append(("txt", t, cap, self.P, wmax, dict(ls=0.04, sx=sx, role="activité")))
        return items

    # ---------------------------------------------------- fin
    def finir(self):
        b = self.d.boite()
        marges = (b[1], self.h - b[3], b[0], self.w - b[2]) if b else (0, 0, 0, 0)
        self.poser(self.decor)
        if self.cadre and self.cadre != "aucun":
            CADRES[self.cadre](self.d, self.S)
        fautes = self.d.verifier()
        if fautes:
            raise SystemExit(f"Tracés trop près du bord de découpe (< 2,5 mm) : {fautes[:4]}. "
                             "Réduire le contenu ou changer de gabarit.")
        return marges

    def rapport(self, marges):
        d = self.d
        L = [f"Gabarit {self.cfg['gabarit']} ({self.cfg['orientation']}), {d.w:g} x {d.h:g} mm, "
             f"forme {self.cfg['forme']}",
             f"Marges du contenu : haut {marges[0]:.1f}, bas {marges[1]:.1f}, gauche {marges[2]:.1f}, "
             f"droite {marges[3]:.1f} mm"]
        vrais = [t for t in self.tailles if t[1] > 0]
        if vrais:
            petit = min(vrais, key=lambda t: t[1])
            large = max(vrais, key=lambda t: t[2])
            L.append(f"Plus petit texte : {petit[0]} ({petit[1]:.2f} mm de capitale)"
                     + ("  ⚠ < 1,7 mm : tester au stylo fin" if petit[1] < 1.7 else ""))
            L.append(f"Ligne la plus large : {large[0]} ({large[2]:.1f} mm)")
        cs = [k for k, v in d.couches.items() if v]
        L.append(f"Calques stylo : {', '.join(cs)} → {len(cs) - 1} changement(s) de stylo, puis découpe")
        L += [f"Note : {n}" for n in dict.fromkeys(self.notes)]
        return "\n".join(L)


# ------------------------------------------------------------------ gabarits
def g_monogramme(c):
    """Monogramme en vedette. Portrait : un seul axe centré. Paysage : identité | infos."""
    cfg, P, S = c.cfg, c.P, c.S
    if c.h > c.w:
        mw = cfg["monogramme_largeur"] or 21.0
        it = [("mono", mw), ("esp", 4.3)] if c.mono_def() else []
        it += [("txt", cfg["nom"], 4.4, P, c.w - 15, dict(ls=1.7, role="nom"))]
        if cfg["prenom"]:
            it += [("esp", 2.0), ("txt", cfg["prenom"], 2.4, S, c.w - 17, dict(ls=1.75, role="prénom"))]
        if cfg["titre"]:
            it += [("esp", 2.3), ("txt", cfg["titre"], 1.7, S, c.w - 15, dict(ls=0.5, role="titre"))]
        it += [("esp", 3.825), ("filet", c.w - 24), ("esp", 3.825)] if cfg["filet"] else [("esp", 5.0)]
        if cfg["activites"]:
            it += c.items_acts(c.w - 14)
            it += [("esp", 3.0), ("point",), ("esp", 3.6)] if cfg["separateur"] else [("esp", 6.6)]
        it += c.items_contacts(wmax=c.w - 14)
        it += c.items_statut(2.95, c.w - 15)
        frag, h = c.pile(it, c.w / 2)
        c.poser(frag, 0, c.centrer_v(h))
    else:
        xL, mw = 19.5 * c.w / 85, cfg["monogramme_largeur"] or 18.5
        it = [("mono", mw), ("esp", 4.3)] if c.mono_def() else []
        it += [("txt", cfg["nom"], 3.5, P, 27, dict(ls=1.35, role="nom"))]
        if cfg["prenom"]:
            it += [("esp", 2.5), ("txt", cfg["prenom"], 2.0, S, 26, dict(ls=1.4, role="prénom"))]
        gauche, hg = c.pile(it, xL)
        X = 40.0 * c.w / 85
        wmax = c.w - X - 8
        it = []
        if cfg["titre"]:
            it += [("txt", cfg["titre"], 1.7, S, wmax, dict(ls=0.5, role="titre")), ("esp", 2.6)]
        if cfg["activites"]:
            it += c.items_acts(wmax) + [("esp", 2.05), ("trait", 4.0), ("esp", 4.0)]
        it += c.items_contacts(wmax=wmax)
        it += c.items_statut(4.15, wmax)
        droite, hd = c.pile(it, X, "start")
        tg, td = c.centrer_v(hg), c.centrer_v(hd)
        c.poser(gauche, 0, tg)
        c.poser(droite, 0, td)
        if cfg["filet"]:
            filet_vertical(c.d, X - 4.0, min(tg, td), max(tg + hg, td + hd), c.ornement, S)


def g_typographique(c):
    """Esprit éditorial : grand nom aligné à gauche en haut, coordonnées calées en bas.
    Tout est proportionnel à la hauteur de la carte (k = 1 pour 55 mm), ce qui sert aussi les mini-cartes."""
    cfg, P, S = c.cfg, c.P, c.S
    paysage = c.w > c.h
    k = max(0.55, min(1.0, (c.h if paysage else c.w) / 55.0))
    m = max(5.0, (8.0 if paysage else 7.0) * k)
    mx = m + (0.45 * c.r if cfg["forme"] == "pilule" else 0.0)   # bouts en demi-cercle : on rentre le texte
    mw = cfg["monogramme_largeur"] or (11.0 if paysage else 13.0) * k
    a_mono = bool(c.mono_def())
    haut = [("mono", mw), ("esp", 4.5 * k)] if a_mono and not paysage else []
    wnom = c.w - 2 * mx - ((mw + 4) if a_mono and paysage else 0)
    if cfg["prenom"]:
        haut += [("txt", cfg["prenom"], max(2.0, 3.0 * k), P, wnom, dict(ls=0.25, role="prénom")),
                 ("esp", max(1.6, 1.9 * k))]
    haut += [("txt", cfg["nom"], max(3.0, (5.4 if paysage else 4.6) * k), P, wnom, dict(ls=0.7 * k, role="nom"))]
    if cfg["titre"]:
        haut += [("esp", 2.3 * k), ("txt", cfg["titre"], 1.8, S, c.w - 2 * mx, dict(ls=0.45, role="titre"))]
    cap_c, cap1 = 1.85, max(1.9, 2.2 * k)
    if paysage:
        # bas de carte en deux colonnes calées sur la marge basse : coordonnées | activités
        haut += [("esp", max(2.2, 3.0 * k)), ("trait", 9.0 * k)]
        wg = 34.0 if cfg["activites"] else c.w - 2 * mx
        xd = mx + wg + 4.0
        bas = c.items_contacts(cap1=cap1, cap=cap_c, pas=max(3.4, 4.2 * k), sx=0.9, wmax=wg)
        bas += c.items_statut(3.0 * k, wg, 1.4)
        droite = c.items_acts(c.w - mx - xd, cap=1.8, pas=3.8, sx=0.9) if cfg["activites"] else []
        colonnes = [(bas, mx), (droite, xd)]
    else:
        if cfg["activites"]:
            haut += [("esp", 3.0), ("trait", 9.0), ("esp", 3.2)]
            haut += c.items_acts(c.w - 2 * mx, cap=1.85, pas=3.9, sx=0.9)
        bas = c.items_contacts(cap1=cap1, cap=cap_c, pas=4.2, sx=0.9, wmax=c.w - 2 * mx)
        bas += c.items_statut(3.0, c.w - 2 * mx, 1.4)
        colonnes = [(bas, mx)]
    f1, h1 = c.pile(haut, mx, "start")
    c.poser(f1, 0, m)
    for items, x in colonnes:
        if not items:
            continue
        f2, h2 = c.pile(items, x, "start")
        if m + h1 + 2.0 * k > c.h - m - h2 - 1.5:
            raise SystemExit("Trop de contenu pour le gabarit typographique : retirer une activité ou un contact.")
        c.poser(f2, 0, c.h - m - h2)
    if a_mono and paysage:
        frag = c.neuf()
        c.cible = frag
        c.mono(c.w - mx - mw, m, mw)
        c.cible = c.d
        c.poser(frag)


def g_centre(c):
    """Minimal centré : beaucoup de blanc, nom sur une ligne, petit filet."""
    cfg, P, S = c.cfg, c.P, c.S
    wmax = c.w - 16
    it = []
    if c.mono_def():
        it += [("mono", cfg["monogramme_largeur"] or (15.0 if c.h > c.w else 12.0)), ("esp", 4.0)]
    plein = f"{cfg['prenom']} {cfg['nom']}".strip()
    if Dessin.largeur(plein, 3.0, 1.0) <= wmax:
        it += [("txt", plein, 3.0, P, wmax, dict(ls=1.0, role="nom"))]
    else:
        it += [("txt", cfg["nom"], 3.2, P, wmax, dict(ls=1.2, role="nom")), ("esp", 2.0),
               ("txt", cfg["prenom"], 2.2, S, wmax, dict(ls=1.0, role="prénom"))]
    if cfg["titre"]:
        it += [("esp", 2.4), ("txt", cfg["titre"], 1.7, S, wmax, dict(ls=0.55, role="titre"))]
    it += [("esp", 3.4), ("filet", 18.0), ("esp", 3.4)] if cfg["filet"] else [("esp", 4.5)]
    if cfg["activites"]:
        it += c.items_acts(wmax, cap=1.85, pas=4.0, sx=0.9) + [("esp", 4.6)]
    it += c.items_contacts(cap1=2.1, cap=1.8, pas=4.0, sx=0.9, wmax=wmax)
    it += c.items_statut(2.8, wmax, 1.4)
    frag, h = c.pile(it, c.w / 2)
    c.poser(frag, 0, c.centrer_v(h))


def _sceau(c, cx, cy, R):
    """Anneau avec textes courbes, monogramme ou initiales au centre.
    Renvoie True si le statut a été écrit dans l'anneau (pour ne pas le répéter)."""
    cfg, P, S = c.cfg, c.P, c.S
    e = 3.4
    c.d.cercle(S, cx, cy, R, 90)
    c.d.cercle(S, cx, cy, R - e, 80)
    rt = R - e / 2
    haut = cfg["embleme_haut"] or f"{cfg['prenom']} {cfg['nom']}".strip().upper()
    statut_dedans = cfg["embleme_bas"] is None and not cfg["titre"] and bool(cfg["statut"])
    bas = cfg["embleme_bas"] if cfg["embleme_bas"] is not None else (cfg["titre"] or cfg["statut"]).upper()
    for s, top in ((haut, True), (bas, False)):
        if not s:
            continue
        cap, ls = 1.75, 0.45
        while (Dessin.largeur(s, cap) + ls * len(s)) / rt > math.radians(150) and cap > 1.4:
            cap, ls = cap - 0.05, max(0.2, ls - 0.02)
        if (Dessin.largeur(s, cap) + ls * len(s)) / rt > math.radians(165):
            raise SystemExit(f"Texte d'emblème trop long : « {s} » (raccourcir embleme_haut / embleme_bas)")
        c.d.texte_courbe(s, cx, cy, rt, cap, P, haut=top, ls=ls)
        c.tailles.append(("texte de l'emblème", cap, 0))
    for a in (0, 180):                                       # points entre texte du haut et du bas
        c.d.cercle(S, cx + rt * math.cos(math.radians(a)), cy + rt * math.sin(math.radians(a)), 0.3, 10)
    ri = R - e - 1.3
    mdef = c.mono_def()
    if mdef:
        frag = c.neuf()
        c.cible = frag
        if mdef == "initiales":
            ini = (cfg["prenom"][:1] + cfg["nom"][:1]).upper()
            frag.texte(ini, cx, cy + ri * 0.33, ri * 0.66, c.M, ls=ri * 0.06, ancre="middle")
        else:
            mw = min(cfg["monogramme_largeur"] or 99, 2 * ri / math.hypot(1, mdef["boite"][1] / mdef["boite"][0]))
            c.mono(cx - mw / 2, cy - c.mono_h(mw) / 2, mw)
        c.cible = c.d
        c.poser(frag)
    return statut_dedans


def g_embleme(c):
    """Sceau rond (texte courbe + monogramme) à côté (paysage) ou au-dessus (portrait) des infos."""
    cfg, P, S = c.cfg, c.P, c.S
    if c.w > c.h:
        R = min(15.5, c.h / 2 - 5.5)
        cx, cy = 5.0 + R, c.h / 2
        statut_dedans = _sceau(c, cx, cy, R)
        X = cx + R + 5.5
        wmax = c.w - X - 7
        it = [("txt", cfg["nom"], 3.2, P, wmax, dict(ls=1.0, role="nom"))]
        if cfg["prenom"]:
            it += [("esp", 2.2), ("txt", cfg["prenom"], 2.0, S, wmax, dict(ls=1.0, role="prénom"))]
        it += [("esp", 3.6)]
        if cfg["activites"]:
            it += c.items_acts(wmax, cap=1.85, pas=4.0) + [("esp", 2.0), ("trait", 4.0), ("esp", 3.8)]
        it += c.items_contacts(cap1=2.2, cap=1.85, pas=4.3, wmax=wmax)
        if not statut_dedans:
            it += c.items_statut(3.6, wmax)
        frag, h = c.pile(it, X, "start")
        c.poser(frag, 0, c.centrer_v(h))
    else:
        R = min(13.5, c.w / 2 - 6)
        it = [("txt", cfg["nom"], 3.4, P, c.w - 15, dict(ls=1.2, role="nom"))]
        if cfg["prenom"]:
            it += [("esp", 2.0), ("txt", cfg["prenom"], 2.1, S, c.w - 17, dict(ls=1.2, role="prénom"))]
        it += [("esp", 3.4), ("filet", 18.0), ("esp", 3.4)] if cfg["filet"] else [("esp", 4.5)]
        if cfg["activites"]:
            it += c.items_acts(c.w - 14, cap=1.85, pas=4.0) + [("esp", 5.0)]
        it += c.items_contacts(cap1=2.2, cap=1.85, pas=4.3, wmax=c.w - 14)
        statut_dedans = cfg["embleme_bas"] is None and not cfg["titre"] and bool(cfg["statut"])
        if not statut_dedans:
            it += c.items_statut(2.95, c.w - 15)
        frag, h = c.pile(it, c.w / 2)
        total = 2 * R + 5.5 + h
        top = c.centrer_v(total)
        _sceau(c, c.w / 2, top + R, R)
        c.poser(frag, 0, top + 2 * R + 5.5)


def g_bandeau(c):
    """Bande de motif (hachures, iso, points...) sur le côté gauche (paysage) ou en haut (portrait)."""
    cfg, P, S = c.cfg, c.P, c.S
    paysage = c.w > c.h
    if paysage:
        band = rrect_pts(4.0, 4.0, 11.0, c.h - 8.0, 1.6)
        X, ancre, wmax = 21.0, "start", c.w - 21.0 - 7.0
    else:
        band = rrect_pts(4.0, 4.0, c.w - 8.0, 11.0, 1.6)
        X, ancre, wmax = c.w / 2, "middle", c.w - 15
    c.decor.poly(S, band)
    c.decor.remplir(S, [band], cfg["motif"])
    it = []
    if c.mono_def():
        it += [("mono", cfg["monogramme_largeur"] or (12.0 if paysage else 15.0)), ("esp", 4.0)]
    it += [("txt", cfg["nom"], 4.0 if paysage else 3.8, P, wmax, dict(ls=1.1, role="nom"))]
    if cfg["prenom"]:
        it += [("esp", 2.0), ("txt", cfg["prenom"], 2.2, S, wmax, dict(ls=1.1, role="prénom"))]
    if cfg["titre"]:
        it += [("esp", 2.3), ("txt", cfg["titre"], 1.7, S, wmax, dict(ls=0.5, role="titre"))]
    it += [("esp", 3.6)]
    if cfg["activites"]:
        it += c.items_acts(wmax, cap=1.85, pas=4.0) + [("esp", 4.6)]
    it += c.items_contacts(cap1=2.2, cap=1.85, pas=4.3, wmax=wmax)
    it += c.items_statut(3.0, wmax)
    frag, h = c.pile(it, X, ancre)
    c.poser(frag, 0, c.centrer_v(h) if paysage else c.centrer_v(h, 15.0))


def g_cartouche(c):
    """Esprit plan technique : activités numérotées en haut, cartouche (tableau) en bas."""
    cfg, P, S = c.cfg, c.P, c.S
    m = 7.0
    x0, x1 = m, c.w - m
    mw = cfg["monogramme_largeur"] or 8.0
    a_mono = bool(c.mono_def())
    yh = m + 1.7
    wtitre = c.d.texte("ACTIVITÉS" if cfg["activites"] else "COORDONNÉES", x0, yh, 1.7, S, ls=0.75)
    c.d.ligne(S, (x0 + wtitre + 1.6, yh - 0.85), (x1 - (mw + 2.5 if a_mono else 0), yh - 0.85))
    if a_mono:
        frag = c.neuf()
        c.cible = frag
        c.mono(x1 - mw, m, mw, relief=False)
        c.cible = c.d
        c.poser(frag)
    y = yh + 5.2
    acts = c.lignes(cfg["activites"], x1 - x0 - 5, 2.2)
    if a_mono and acts:                       # une activité longue passerait sous le monogramme
        plus_large = max(Dessin.largeur(t, 2.2, 0.06) for t in acts)
        if x0 + 5.0 + plus_large > x1 - mw - 1.0:
            y = max(y, m + c.mono_h(mw) - (0.95 if cfg["relief"] else 0) + 1.6 + 2.2)
    for i, t in enumerate(acts):
        c.d.texte(f"{i + 1:02d}", x0, y, 1.9, S, ls=0.15)
        c.txt(t, x0 + 5.0, y, 2.2, P, x1 - x0 - 5.0, ls=0.06, ancre="start", role="activité")
        y += 4.4
    lignes = [("NOM", f"{cfg['prenom']} {cfg['nom']}".strip(), 2.9)]
    for lab, val in (("TITRE", cfg["titre"]), ("TÉL", cfg["telephone"]), ("MAIL", cfg["email"]),
                     ("WEB", cfg["site"]), ("STATUT", cfg["statut"])):
        if val:
            lignes.append((lab, val, 2.2))
    rh = 4.0
    top = c.h - m - rh * len(lignes)
    if top < y - 2.0:
        rh = 3.6
        top = c.h - m - rh * len(lignes)
        if top < y - 2.0:
            raise SystemExit("Trop de contenu pour le gabarit cartouche : retirer une ligne.")
    lab_w = 12.5 if c.w > c.h else 11.0
    c.d.rect(S, x0, top, x1 - x0, rh * len(lignes))
    c.d.ligne(S, (x0 + lab_w, top), (x0 + lab_w, top + rh * len(lignes)))
    for k, (lab, val, cap) in enumerate(lignes):
        by = top + rh * k + rh * 0.69
        if k:
            c.d.ligne(S, (x0, top + rh * k), (x1, top + rh * k))
        c.d.texte(lab, x0 + 1.2, by - 0.15, 1.5, S, ls=0.3)
        c.txt(val, x0 + lab_w + 1.5, by + (0.2 if k == 0 else 0), min(cap, rh * 0.62), P,
              x1 - x0 - lab_w - 3.0, ls=0.12 if k == 0 else 0.06, sx=1.0 if k == 0 else 0.9,
              ancre="start", cap_min=1.5, role=lab.lower())


GABARITS = {"monogramme": g_monogramme, "typographique": g_typographique, "centre": g_centre,
            "embleme": g_embleme, "bandeau": g_bandeau, "cartouche": g_cartouche}


# ------------------------------------------------------------------ verso
def verso(cfg):
    """Dos de carte : monogramme seul, motif avec réserve centrale, ou slogan."""
    v = {"gabarit": "monogramme", **(cfg["verso"] or {})}
    vc = {**cfg, "cadre": v.get("cadre", cfg["cadre"]), "ornement": v.get("ornement", cfg["ornement"])}
    c = Carte(vc)
    S, P = c.S, c.P
    m = min(c.w, c.h)
    nom = f"{cfg['prenom']} {cfg['nom']}".strip().upper()
    if v["gabarit"] == "monogramme":
        it = [("mono", v.get("monogramme_largeur", m * 0.5))] if c.mono_def() else []
        if v.get("nom", True) and nom:
            it += [("esp", 5.0), ("txt", nom, 1.9, S, c.w - 16, dict(ls=1.1, role="nom"))]
        frag, h = c.pile(it, c.w / 2)
        c.poser(frag, 0, c.centrer_v(h))
    elif v["gabarit"] == "motif":
        zone = rrect_pts(4.5, 4.5, c.w - 9, c.h - 9, 2.0)
        r = m * 0.3
        trou = [(c.w / 2 + r * math.cos(math.radians(a)), c.h / 2 + r * math.sin(math.radians(a)))
                for a in range(0, 361, 4)]
        c.d.poly(S, zone)
        c.d.poly(S, trou)
        c.d.remplir(S, [zone, trou], v.get("motif", "iso"))
        mdef = c.mono_def()
        if mdef:
            mw = (r - 2.2) * 2 / (1.414 if mdef == "initiales" else math.hypot(1, mdef["boite"][1] / mdef["boite"][0]))
            frag = c.neuf()
            c.cible = frag
            c.mono(c.w / 2 - mw / 2, c.h / 2 - c.mono_h(mw) / 2, mw)
            c.cible = c.d
            c.poser(frag)
        c.cadre = "aucun"
    elif v["gabarit"] == "slogan":
        lignes = v.get("texte") or cfg["slogan"]
        if not lignes:
            raise SystemExit("verso slogan : renseigner verso.texte ou slogan")
        lignes = lignes if isinstance(lignes, list) else [lignes]
        it = []
        for i, t in enumerate(lignes):
            if i:
                it.append(("esp", 2.2))
            it.append(("txt", t, 3.0, P, c.w - 14, dict(ls=0.3, police=v.get("police", "timesr"), role="slogan")))
        it += [("esp", 3.6), ("filet", 16.0), ("esp", 3.6)] if cfg["filet"] else [("esp", 4.5)]
        it += [("txt", nom, 1.7, S, c.w - 16, dict(ls=0.9, role="nom"))]
        frag, h = c.pile(it, c.w / 2)
        c.poser(frag, 0, c.centrer_v(h))
    else:
        raise SystemExit("verso.gabarit : monogramme, motif ou slogan")
    marges = c.finir()
    return c.d, c.rapport(marges)


# ------------------------------------------------------------------ construction
def construire(cfg):
    full = copy.deepcopy(DEFAUT)
    full.update(cfg)
    full["stylos"] = {**DEFAUT["stylos"], **cfg.get("stylos", {})}
    if full["gabarit"] not in GABARITS:
        raise SystemExit(f"gabarit inconnu : {full['gabarit']} ({', '.join(GABARITS)})")
    if full["orientation"] not in ("portrait", "paysage"):
        raise SystemExit("orientation : portrait ou paysage")
    mw0 = full["monogramme_largeur"]
    fm = full["format"]
    petit_cote = min(fm) if isinstance(fm, (list, tuple)) else min(FORMATS[fm])
    seuil = min(6.0, 0.11 * petit_cote)      # marge mini attendue, proportionnelle aux petites cartes
    for k in range(12):          # contenu dense : on réduit le monogramme pour garder des marges
        c = Carte(full)
        GABARITS[full["gabarit"]](c)
        marges = c.finir()
        if min(marges[:2]) >= seuil or not full["monogramme"] or full["gabarit"] in ("cartouche", "embleme"):
            break
        base = mw0 or {"monogramme": 21.0 if c.h > c.w else 18.5, "typographique": 13.0}.get(full["gabarit"], 15.0)
        if base - (k + 1) < 9:
            break
        full["monogramme_largeur"] = base - (k + 1)
    rapport = c.rapport(marges)
    if min(marges[:2]) < seuil - 0.5:
        rapport += "\n⚠ Marge haute/basse faible : contenu dense, retirer une ligne ou raccourcir"
    if mw0 is None and full["monogramme_largeur"] is not None:
        rapport += f"\nNote : monogramme réduit à {full['monogramme_largeur']:g} mm pour garder des marges"
    return (c.d, rapport), (verso(full) if full["verso"] else None), full


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    variantes = cfg.pop("variantes", None)
    cartes = []
    for v in [{}] + (variantes or []):
        (d, rapport), vers, full = construire({**cfg, **v})
        nom = full["fichier"]
        d.enregistrer(out / f"{nom}.svg")
        d.apercu_png(out / f"{nom}.png")
        print(f"=== {nom}.svg\n{rapport}\n")
        cartes.append(d)
        if vers:
            dv, rv = vers
            dv.enregistrer(out / f"{nom}_verso.svg")
            dv.apercu_png(out / f"{nom}_verso.png")
            print(f"=== {nom}_verso.svg (dos)\n{rv}\n")
            cartes.append(dv)
    if len(cartes) > 1:
        rangs = [cartes[i:i + 4] for i in range(0, len(cartes), 4)]      # 4 cartes par rangée
        larg = max(sum(x.w for x in r) + 6 * (len(r) - 1) for r in rangs) + 16
        haut = sum(max(x.h for x in r) for r in rangs) + 6 * (len(rangs) - 1) + 14
        planche([[x.svg(papier=PAPIER_BLANC, apercu=True) for x in r] for r in rangs],
                out / f"{cfg.get('fichier', 'carte')}_planche.png", larg, haut)
        print(f"Planche de comparaison : {cfg.get('fichier', 'carte')}_planche.png")


if __name__ == "__main__":
    main()
