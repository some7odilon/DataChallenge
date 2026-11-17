"""Calcul des indicateurs régionaux à partir des tableaux propres (sortie de l'audit).

Chaque fonction travaille sur un « pivot » : index = region_code, colonnes = année de début
de l'année scolaire (2015, 2016...), valeurs = indicateur.
Aucune valeur manquante n'est imputée : une région sans donnée reçoit NaN.

Choix méthodologiques :
- niveaux = moyenne des k dernières années disponibles (une seule année est trop bruitée) ;
- les taux bruts (achèvement, TBS, CEP) sont PLAFONNÉS à 100 avant tout calcul : dépasser 100
  (élèves hors âge, redoublants, migrations) ne rend pas une région « moins vulnérable » ;
- la « tendance » est l'écart entre le niveau récent et la moyenne d'AVANT le choc 2022/23
  (et non une pente sur toute la période, qui mesurerait surtout la chute puis le rebond).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def pivot(df: pd.DataFrame, sexe: str | None = None, statut: str | None = None) -> pd.DataFrame:
    d = df.copy()
    if sexe and "sexe" in d.columns:
        d = d[d["sexe"] == sexe]
    if statut and "statut" in d.columns:
        d = d[d["statut"].astype(str).str.upper() == statut.upper()]
    if d.empty:
        return pd.DataFrame()
    return d.pivot_table(index="region_code", columns="annee", values="valeur", aggfunc="first")


def plafonner(piv: pd.DataFrame, plafond: float | None = 100.0) -> pd.DataFrame:
    """Plafonne un taux brut (par défaut à 100)."""
    if piv.empty or plafond is None:
        return piv
    return piv.clip(upper=plafond)


def niveau_recent(piv: pd.DataFrame, k: int = 2) -> pd.Series:
    """Moyenne des k dernières valeurs disponibles (lisse le bruit d'une seule année)."""
    out = {}
    for r, ligne in piv.iterrows():
        v = ligne.dropna().sort_index().iloc[-k:]
        out[r] = v.mean() if len(v) else np.nan
    return pd.Series(out, dtype=float)


def pente(piv: pd.DataFrame, min_pts: int = 4) -> pd.Series:
    """Pente linéaire (unités par an) sur toute la période disponible."""
    out = {}
    for r, ligne in piv.iterrows():
        v = ligne.dropna().sort_index()
        out[r] = np.polyfit(v.index.astype(float), v.values, 1)[0] if len(v) >= min_pts else np.nan
    return pd.Series(out, dtype=float)


def ecart_vs_avant_choc(piv: pd.DataFrame, annee_choc: int, k: int = 3) -> pd.Series:
    """Niveau récent moins moyenne des années précédant le choc (même unité que la série ;
    négatif = la région n'a pas retrouvé son niveau d'avant)."""
    if piv.empty:
        return pd.Series(dtype=float)
    avant = piv[[c for c in piv.columns if c < annee_choc]]
    if avant.shape[1] == 0:
        return pd.Series(np.nan, index=piv.index, dtype=float)
    return niveau_recent(piv, k) - avant.mean(axis=1)


def choc(piv: pd.DataFrame, annee_choc: int, k: int = 2) -> pd.DataFrame:
    """Perte au point bas et déficit résiduel par rapport à l'année précédant le choc.

    perte_pic        = 1 - valeur(année du choc) / valeur(année d'avant)      (>= 0)
    deficit_residuel = 1 - niveau récent / valeur(année d'avant)              (>= 0)
    """
    if piv.empty or (annee_choc - 1) not in piv.columns or annee_choc not in piv.columns:
        return pd.DataFrame(columns=["perte_pic", "deficit_residuel"])
    avant = piv[annee_choc - 1]
    pic = (1 - piv[annee_choc] / avant).clip(lower=0)
    res = (1 - niveau_recent(piv, k) / avant).clip(lower=0)
    return pd.DataFrame({"perte_pic": pic, "deficit_residuel": res})


def variation_vs_avant_choc(piv: pd.DataFrame, annee_choc: int, k: int = 2) -> pd.Series:
    """Niveau récent / moyenne des années précédant le choc - 1 (négatif = recul)."""
    if piv.empty:
        return pd.Series(dtype=float)
    avant = piv[[c for c in piv.columns if c < annee_choc]].mean(axis=1)
    return niveau_recent(piv, k) / avant - 1


def ecart_genre(df: pd.DataFrame, k: int = 2, plafond: float | None = None) -> pd.DataFrame:
    """Écart de parité sur le niveau récent. ecart_signe = F - G (négatif : filles en retrait)."""
    g, f = plafonner(pivot(df, "G"), plafond), plafonner(pivot(df, "F"), plafond)
    if g.empty or f.empty:
        return pd.DataFrame(columns=["ecart_abs", "ecart_signe"])
    signe = niveau_recent(f, k) - niveau_recent(g, k)
    return pd.DataFrame({"ecart_abs": signe.abs(), "ecart_signe": signe})


def calculer_indicateurs(tables: dict[str, pd.DataFrame], annee_choc: int = 2022, k: int = 3,
                         annee_max: int | None = None, plafond: float | None = 100.0) -> pd.DataFrame:
    """tables : clés 'achevement', 'effectifs', 'ecoles', 'cp1', 'cep', 'tbs', 'presco_tbs'
    (toutes facultatives).

    k          : nombre d'années récentes moyennées pour les niveaux
    annee_max  : ignore les données postérieures (pour rejouer l'indice à une date passée)
    plafond    : plafond des taux bruts (None pour désactiver)
    """
    if annee_max is not None:
        tables = {c: d[d["annee"] <= annee_max] for c, d in tables.items() if d is not None}
    cols: dict[str, pd.Series] = {}

    ach = tables.get("achevement")
    if ach is not None and not ach.empty:
        t = plafonner(pivot(ach, "T"), plafond)
        cols["achevement_niveau"] = niveau_recent(t, k)
        cols["achevement_tendance"] = ecart_vs_avant_choc(t, annee_choc, k)
        eg = ecart_genre(ach, k, plafond)
        if not eg.empty:
            cols["ecart_genre_achevement"] = eg["ecart_abs"]
            cols["ecart_signe"] = eg["ecart_signe"]

    chocs = []
    for cle, kw in (("effectifs", {"sexe": "T"}), ("ecoles", {"statut": "Total"})):
        d = tables.get(cle)
        if d is not None and not d.empty:
            c = choc(pivot(d, **kw), annee_choc, k)
            if not c.empty:
                chocs.append(0.5 * c["perte_pic"] + 0.5 * c["deficit_residuel"])
    if chocs:
        cols["choc_ecoles_effectifs"] = pd.concat(chocs, axis=1).mean(axis=1)

    cp1 = tables.get("cp1")
    if cp1 is not None and not cp1.empty:
        cols["entrees_cp1"] = variation_vs_avant_choc(pivot(cp1, "T"), annee_choc, k)

    cep = tables.get("cep")
    if cep is not None and not cep.empty:
        cols["reussite_cep"] = niveau_recent(plafonner(pivot(cep, "T"), plafond), k)

    tbs = tables.get("tbs")
    if tbs is not None and not tbs.empty:
        cols["scolarisation_tbs"] = niveau_recent(plafonner(pivot(tbs, "T"), plafond), k)

    presco = tables.get("presco_tbs")
    if presco is not None and not presco.empty:
        cols["presco_acces"] = niveau_recent(pivot(presco, "T"), k)

    if not cols:
        raise ValueError("Aucun tableau exploitable pour calculer les indicateurs.")
    return pd.DataFrame(cols).sort_index()