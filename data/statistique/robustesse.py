"""Robustesse, redondance, validation et stabilité temporelle de l'indice.

Cinq questions, cinq fonctions :
- ensemble()                  Le classement résiste-t-il quand on change les poids, la normalisation,
                              les années de référence ou qu'on retire un indicateur ?
- poids_par_source()          Quelle part du score vient réellement de chaque tableau ?
- correlations()              Deux indicateurs disent-ils la même chose (double comptage) ?
- validation_convergente()    Les facteurs de vulnérabilité vont-ils dans le même sens que le résultat ?
- historique()                Le classement tient-il d'une année à l'autre ?

Tout est calculé entre les 13 régions : ce sont des mesures de COHÉRENCE du classement, pas des
preuves de causalité ni des intervalles de confiance statistiques.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from data.statistique import indice as ix
from data.statistique.indicateur import calculer_indicateurs


# ------------------------------------------------------------------ utilitaires
def _rangs(risque: pd.DataFrame, cols: list[str], W: np.ndarray) -> np.ndarray:
    """Rangs (1 = risque le plus élevé) pour chaque ligne de poids de W : tirages x régions.
    Si un indicateur manque pour une région, les poids sont renormalisés (comme calculer_indice)."""
    X = risque[cols].fillna(0).values
    M = risque[cols].notna().values.astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        S = (W @ X.T) / (W @ M.T)
    S = np.where(np.isfinite(S), S, -np.inf)
    return (-S).argsort(axis=1).argsort(axis=1) + 1


def _spearman_lignes(rangs: np.ndarray, base: np.ndarray) -> np.ndarray:
    b = base - base.mean()
    r = rangs - rangs.mean(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (r @ b) / (np.sqrt((r ** 2).sum(axis=1)) * np.sqrt((b ** 2).sum()))


def _stats(rangs: np.ndarray, base: np.ndarray, top_k: int) -> dict:
    rho = _spearman_lignes(rangs, base)
    return {
        "n_scenarios": int(len(rangs)),
        "spearman_moyen": float(np.nanmean(rho)),
        "spearman_min": float(np.nanmin(rho)),
        "top_k_identique": float(((rangs <= top_k) == (base <= top_k)).all(axis=1).mean()),
    }


# ------------------------------------------------------------------ robustesse globale
def ensemble(tables: dict, annee_choc: int, poids: dict, *, normalisation: str = "robuste",
             niveau_annees: int = 3, normalisations=("minmax", "robuste", "rang"),
             niveaux=(1, 2, 3), amplitude: float = 0.5, tirages: int = 1000,
             tirages_par_variante: int = 20, top_k: int = 4, seed: int = 42):
    """Rejoue le classement sous de nombreuses variantes.

    Familles testées (chacune isolée, puis toutes combinées) :
      poids          : tirage aléatoire des poids (x [1-amplitude, 1+amplitude])
      normalisation  : min-max / bornes robustes / rangs
      annees         : 1, 2 ou 3 dernières années pour les niveaux
      retrait        : on retire un indicateur à la fois
      combine        : tout à la fois (sert aux fourchettes de rang et aux probabilités)

    Retourne (DataFrame par région, résumé). Le DataFrame a les colonnes rang_p5, rang_p95,
    rang_median, prob_prioritaire (part des scénarios où la région est dans le top k) ;
    ses attrs reprennent la stabilité globale (spearman_moyen, spearman_min).
    """
    rng = np.random.default_rng(seed)
    niveaux = sorted(set(niveaux) | {niveau_annees})
    cache = {k: calculer_indicateurs(tables, annee_choc, k=k) for k in niveaux}
    regions = cache[niveau_annees].index

    def risque_de(k, norm, retrait=None):
        r = ix.normaliser_risque(cache[k], norm).reindex(regions)
        if retrait:
            r = r.copy()
            r[retrait] = np.nan
        return r

    base_risque = risque_de(niveau_annees, normalisation)
    cols, w0 = ix._poids(base_risque, poids)
    if not cols:
        raise ValueError("Aucun indicateur pondéré disponible.")
    base = ix.calculer_indice(base_risque, poids)["rang"].values
    retraits = cols if len(cols) >= 3 else []

    def tirer(n):
        if n == 0:
            return w0[None, :]
        return w0 * (1 + rng.uniform(-amplitude, amplitude, size=(n, len(cols))))

    def lancer(variantes, n_poids):
        return np.vstack([_rangs(risque_de(k, nm, ret), cols, tirer(n_poids)) for k, nm, ret in variantes])

    familles = {
        "poids": lancer([(niveau_annees, normalisation, None)], tirages),
        "normalisation": lancer([(niveau_annees, n, None) for n in normalisations if n != normalisation], 0)
        if any(n != normalisation for n in normalisations) else None,
        "annees": lancer([(k, normalisation, None) for k in niveaux if k != niveau_annees], 0)
        if len(niveaux) > 1 else None,
        "retrait": lancer([(niveau_annees, normalisation, c) for c in retraits], 0) if retraits else None,
    }
    toutes = [(k, n, r) for k in niveaux for n in normalisations for r in [None] + retraits]
    combine = lancer(toutes, tirages_par_variante)
    familles["combine"] = combine

    res = pd.DataFrame({
        "rang_p5": np.percentile(combine, 5, axis=0),
        "rang_p95": np.percentile(combine, 95, axis=0),
        "rang_median": np.median(combine, axis=0),
        "prob_prioritaire": (combine <= top_k).mean(axis=0),
    }, index=regions)
    resume = {nom: _stats(r, base, top_k) for nom, r in familles.items() if r is not None}
    res.attrs["spearman_moyen"] = resume["combine"]["spearman_moyen"]
    res.attrs["spearman_min"] = resume["combine"]["spearman_min"]
    return res, resume


# ------------------------------------------------------------------ poids réels par source
def poids_par_source(poids: dict, colonnes) -> dict:
    """Part du poids total portée par chaque tableau source (un indicateur à deux sources
    se partage entre elles). Permet de voir qu'un score « à 8 indicateurs » repose sur peu de tableaux."""
    cols = [c for c in colonnes if poids.get(c, 0) > 0 and c in ix.INDICATEURS]
    total = sum(poids[c] for c in cols)
    out: dict[str, float] = {}
    for c in cols:
        sources = ix.INDICATEURS[c]["sources"]
        for s in sources:
            out[s] = out.get(s, 0.0) + poids[c] / len(sources) / total
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


# ------------------------------------------------------------------ redondance
def correlations(risque: pd.DataFrame, seuil: float = 0.8) -> dict:
    """Corrélation de Spearman entre indicateurs (risque orienté : positive = même signal).
    Une corrélation forte signale un double comptage possible."""
    c = risque.corr(method="spearman")
    paires = []
    for i, a in enumerate(c.columns):
        for b in c.columns[i + 1:]:
            v = c.loc[a, b]
            if pd.notna(v) and abs(v) >= seuil:
                paires.append({"a": a, "b": b, "rho": round(float(v), 2)})
    return {"matrice": c.round(2).to_dict(), "paires_redondantes": paires, "seuil": seuil}


# ------------------------------------------------------------------ validation convergente
def _score_famille(risque: pd.DataFrame, poids: dict, colonnes) -> pd.Series:
    cols = [c for c in colonnes if c in risque.columns and poids.get(c, 0) > 0]
    if not cols:
        return pd.Series(np.nan, index=risque.index)
    w = np.array([poids[c] for c in cols], dtype=float)
    X = risque[cols]
    den = (X.notna().values * w).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        s = (X.fillna(0).values * w).sum(axis=1) / den
    return pd.Series(s, index=risque.index)


def validation_convergente(risque: pd.DataFrame, poids: dict, n_perm: int = 5000, seed: int = 7) -> dict:
    """Les résultats (achèvement et CEP) sont-ils associés aux facteurs d'accès et de perturbation ?
    Corrélation de Spearman entre les
    deux sous-scores, avec une p-valeur par permutation (n = 13 régions : à prendre avec prudence).
    Montre une association, jamais une causalité."""
    a = _score_famille(risque, poids, ix.FAMILLES["resultat"])
    b = _score_famille(risque, poids, ix.FAMILLES["facteurs"])
    m = a.notna() & b.notna()
    if m.sum() < 5:
        return {"disponible": False, "raison": "moins de 5 régions comparables"}
    ra, rb = a[m].rank().values, b[m].rank().values
    rho = float(np.corrcoef(ra, rb)[0, 1])
    rng = np.random.default_rng(seed)
    perm = np.array([np.corrcoef(ra, rng.permutation(rb))[0, 1] for _ in range(n_perm)])
    p = float((np.sum(np.abs(perm) >= abs(rho) - 1e-12) + 1) / (n_perm + 1))
    force = "forte" if abs(rho) >= 0.6 else "modérée" if abs(rho) >= 0.4 else "faible"
    return {"disponible": True, "rho": round(rho, 2), "p_permutation": round(p, 4),
            "n_regions": int(m.sum()), "association": force,
            "lecture": f"Association {force} entre les résultats (achèvement et CEP) et les facteurs d'accès/perturbation "
                       f"(Spearman {rho:.2f}, {int(m.sum())} régions). Une association n'est pas une cause."}


def validation_attentes(rang: pd.Series, attendues, top_k: int) -> dict:
    """Confronte le classement aux régions que le terrain désigne comme les plus touchées."""
    attendues = [a for a in (attendues or []) if a in rang.index]
    if not attendues:
        return {"disponible": False, "raison": "aucune région attendue renseignée dans config.yaml (validation.regions_attendues_vulnerables)"}
    rangs = {a: int(rang[a]) for a in attendues}
    dans = [a for a, r in rangs.items() if r <= top_k]
    return {"disponible": True, "regions_attendues": attendues, "rangs": rangs, "top_k": top_k,
            "dans_top_k": dans, "part_dans_top_k": round(len(dans) / len(attendues), 2)}


# ------------------------------------------------------------------ stabilité dans le temps
def historique(tables: dict, annee_choc: int, poids: dict, normalisation: str = "robuste",
               niveau_annees: int = 3, seuil_saut: int = 4) -> dict:
    """Rejoue l'indice avec les données disponibles à chaque année depuis le choc : le classement
    de 2024/25 est-il cohérent avec celui de 2022/23 et 2023/24 ? Les sauts brusques sont listés
    pour être expliqués (rupture de données ou vrai changement)."""
    annees = sorted({int(a) for t in tables.values() if t is not None and "annee" in t for a in t["annee"].unique()})
    annees = [a for a in annees if a >= annee_choc]
    rangs = {}
    for a in annees:
        ind = calculer_indicateurs(tables, annee_choc, k=niveau_annees, annee_max=a)
        rangs[a] = ix.calculer_indice(ix.normaliser_risque(ind, normalisation), poids)["rang"]
    if len(rangs) < 2:
        return {"disponible": False, "raison": "moins de deux années depuis le choc"}
    df = pd.DataFrame(rangs)
    lib = {a: f"{a}/{(a + 1) % 100:02d}" for a in annees}
    spear, sauts = {}, []
    for a, b in zip(annees[:-1], annees[1:]):
        spear[f"{lib[a]} -> {lib[b]}"] = round(float(df[a].corr(df[b], method="spearman")), 2)
        for code in df.index:
            d = df.loc[code, b] - df.loc[code, a]
            if pd.notna(d) and abs(d) >= seuil_saut:
                sauts.append({"region": code, "de": lib[a], "vers": lib[b], "variation_rang": int(d)})
    return {
        "disponible": True, "annees": [lib[a] for a in annees],
        "rang_par_annee": {code: {lib[a]: (None if pd.isna(df.loc[code, a]) else int(df.loc[code, a])) for a in annees}
                           for code in df.index},
        "spearman_consecutifs": spear, "sauts": sauts, "seuil_saut": seuil_saut,
    }
