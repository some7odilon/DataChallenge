"""Indice composite de risque, analyse de sensibilité et profils d'action.

Lecture : score de 0 (risque le plus faible observé) à 100 (risque le plus élevé observé),
RELATIF aux 13 régions. Ce n'est pas un taux de décrochage : c'est un classement.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# sens = "bas" : plus la valeur est basse, plus le risque est élevé ; "haut" : l'inverse
ACH = ["primaire_achevement_region"]
INDICATEURS = {
    "achevement_niveau": {
        "sens": "bas", "sources": ACH,
        "label": "Taux d'achèvement récent (moyenne des dernières années, plafonné à 100)"},
    "achevement_tendance": {
        "sens": "bas", "sources": ACH,
        "label": "Écart de l'achèvement récent par rapport à la période d'avant le choc 2022/23 (points)"},
    "ecart_genre_achevement": {
        "sens": "haut", "sources": ACH,
        "label": "Écart filles-garçons d'achèvement (valeur absolue)",
        "note": "Mesure la disparité, pas un désavantage présumé des filles : le sens de l'écart est conservé à part."},
    "choc_ecoles_effectifs": {
        "sens": "haut", "sources": ["primaire_effectifs_region", "primaire_ecoles_region"],
        "label": "Perte d'élèves et d'écoles liée au choc 2022/23 (pic et déficit résiduel)",
        "note": "Signal de perturbation scolaire : une baisse d'effectifs ou d'écoles ne prouve pas à elle seule des abandons."},
    "entrees_cp1": {
        "sens": "bas", "sources": ["primaire_nouveaux_cp1_region"],
        "label": "Évolution des nouveaux inscrits en CP1 par rapport à avant le choc"},
    "reussite_cep": {
        "sens": "bas", "sources": ["primaire_cep_region"],
        "label": "Taux de réussite au CEP récent",
        "note": "Calculé sur les candidats : une forte sortie avant le CEP peut le masquer. À lire avec prudence."},
    "scolarisation_tbs": {
        "sens": "bas", "sources": ["primaire_tbs_region"],
        "label": "Taux brut de scolarisation au primaire (plafonné à 100)",
        "note": "Un TBS supérieur à 100 reflète aussi des élèves hors âge et des redoublants ; il est plafonné à 100."},
    "presco_acces": {
        "sens": "bas", "sources": ["prescolaire_T5"],
        "label": "TBS du préscolaire (accès précoce)",
        "note": "Lien indirect avec le primaire : poids faible."},
}

# Familles servant à la validation convergente : les facteurs « prédisent-ils » le résultat ?
# (l'écart de genre, dérivé de l'achèvement, n'est dans aucune des deux)
FAMILLES = {
    "resultat": ["achevement_niveau", "achevement_tendance", "reussite_cep"],
    "facteurs": ["choc_ecoles_effectifs", "entrees_cp1", "scolarisation_tbs", "presco_acces"],
}

GROUPES = {
    "achevement": {"nom": "Faible achèvement du cycle",
                   "indicateurs": ["achevement_niveau", "achevement_tendance", "reussite_cep"],
                   "reco": "Accompagner le maintien jusqu'au CM2 : suivi des élèves à risque, soutien scolaire "
                           "et préparation au CEP, appui aux classes de fin de cycle."},
    "genre": {"nom": "Disparités filles-garçons",
              "indicateurs": ["ecart_genre_achevement"],
              "reco": "Cibler le maintien du groupe en retrait (voir sens de l'écart) : mesures de soutien "
                      "adaptées et analyse des causes locales avant d'agir."},
    "choc": {"nom": "Perturbation scolaire",
             "indicateurs": ["choc_ecoles_effectifs"],
             "reco": "Prioriser la réouverture et la sécurisation des écoles, la continuité éducative "
                     "(écoles temporaires, enseignement à distance) et la réintégration des élèves déplacés."},
    "entree": {"nom": "Entrée dans le cycle fragile",
               "indicateurs": ["entrees_cp1", "scolarisation_tbs", "presco_acces"],
               "reco": "Renforcer l'accès à l'école : inscription au CP1, développement du préscolaire, "
                       "proximité des établissements et sensibilisation des familles."},
}


METHODES_NORMALISATION = ("minmax", "robuste", "rang")


def normaliser_risque(ind: pd.DataFrame, methode: str = "minmax") -> pd.DataFrame:
    """Ramène chaque indicateur sur 0-100 entre les régions, orienté pour que 100 = risque maximal.

    minmax  : (x - min) / (max - min). Sensible aux valeurs extrêmes.
    robuste : valeurs bornées aux déciles 10 et 90 avant le min-max : un extrême ne tire plus l'échelle.
    rang    : rang en pourcentage entre les régions (ignore l'écart réel entre valeurs).
    """
    if methode not in METHODES_NORMALISATION:
        raise ValueError(f"Méthode de normalisation inconnue : {methode}")
    out = pd.DataFrame(index=ind.index)
    for c, m in INDICATEURS.items():
        if c not in ind.columns:
            continue
        x = ind[c].astype(float)
        n = int(x.notna().sum())
        if methode == "rang":
            if n < 2:
                out[c] = np.where(x.notna(), 0.0, np.nan)
                continue
            r = (x.rank(method="average") - 1) / (n - 1)
        else:
            if methode == "robuste" and n >= 3:
                x = x.clip(lower=x.quantile(0.1), upper=x.quantile(0.9))
            lo, hi = x.min(), x.max()
            if not np.isfinite(lo) or hi == lo:
                out[c] = np.where(x.notna(), 0.0, np.nan)  # pas de discrimination possible
                continue
            r = (x - lo) / (hi - lo)
        out[c] = (1 - r if m["sens"] == "bas" else r) * 100
    return out


def _poids(risque: pd.DataFrame, poids: dict) -> tuple[list[str], np.ndarray]:
    cols = [c for c in poids if c in risque.columns and poids[c] > 0]
    return cols, np.array([poids[c] for c in cols], dtype=float)


def calculer_indice(risque: pd.DataFrame, poids: dict) -> pd.DataFrame:
    """Moyenne pondérée ; si un indicateur manque pour une région, les poids sont renormalisés."""
    cols, w = _poids(risque, poids)
    X = risque[cols]
    M = X.notna().values
    den = (M * w).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        score = (X.fillna(0).values * w).sum(axis=1) / den
    res = pd.DataFrame({"score": score, "couverture_poids": den / w.sum()}, index=risque.index)
    res["rang"] = res["score"].rank(ascending=False, method="min")
    return res


def sensibilite(risque: pd.DataFrame, poids: dict, amplitude: float = 0.5, tirages: int = 1000,
                top_k: int = 4, seed: int = 42) -> pd.DataFrame:
    """Tire au hasard des pondérations (chaque poids x [1-a, 1+a]) et mesure la stabilité du rang."""
    cols, w0 = _poids(risque, poids)
    X0 = risque[cols].fillna(0).values
    M = risque[cols].notna().values.astype(float)
    rng = np.random.default_rng(seed)
    W = w0 * (1 + rng.uniform(-amplitude, amplitude, size=(tirages, len(cols))))
    with np.errstate(invalid="ignore", divide="ignore"):
        S = (W @ X0.T) / (W @ M.T)                     # tirages x régions
    S = np.where(np.isfinite(S), S, -np.inf)
    rangs = (-S).argsort(axis=1).argsort(axis=1) + 1    # 1 = risque le plus élevé
    base = calculer_indice(risque, poids)["rang"].values
    b = base - base.mean()
    r = rangs - rangs.mean(axis=1, keepdims=True)
    rho = (r @ b) / (np.sqrt((r ** 2).sum(axis=1)) * np.sqrt((b ** 2).sum()))
    res = pd.DataFrame({
        "rang_p5": np.percentile(rangs, 5, axis=0),
        "rang_p95": np.percentile(rangs, 95, axis=0),
        "rang_median": np.median(rangs, axis=0),
        "prob_prioritaire": (rangs <= top_k).mean(axis=0),
    }, index=risque.index)
    res.attrs["spearman_moyen"] = float(np.nanmean(rho))
    res.attrs["spearman_min"] = float(np.nanmin(rho))
    return res


def contributions(risque: pd.DataFrame, poids: dict) -> pd.DataFrame:
    """Part du score (en points) due à chaque indicateur."""
    cols, w = _poids(risque, poids)
    X = risque[cols]
    den = (X.notna().values * w).sum(axis=1)[:, None]
    with np.errstate(invalid="ignore", divide="ignore"):
        c = X.fillna(0).values * w / den
    return pd.DataFrame(c, index=risque.index, columns=cols)


def niveau_confiance(couverture: float, nb_annees: int | None = None) -> str:
    if couverture >= 0.9 and (nb_annees is None or nb_annees >= 8):
        return "élevée"
    return "moyenne" if couverture >= 0.7 else "faible"


def profils(contrib: pd.DataFrame, risque: pd.DataFrame, ecart_signe: pd.Series | None = None,
            n_facteurs: int = 3) -> pd.DataFrame:
    """Profil = dimension la plus dégradée de la région (risque moyen par groupe d'indicateurs,
    indépendant du poids du groupe, pour ne pas favoriser les groupes qui pèsent le plus).
    Les facteurs dominants, eux, sont classés par contribution au score."""
    lignes = {}
    for r, ligne in contrib.iterrows():
        par_groupe = {}
        for g, d in GROUPES.items():
            v = risque.loc[r, [i for i in d["indicateurs"] if i in risque.columns]].dropna()
            if len(v):
                par_groupe[g] = v.mean()
        g = max(par_groupe, key=par_groupe.get) if par_groupe else "achevement"
        top = ligne.sort_values(ascending=False).head(n_facteurs)
        reco = GROUPES[g]["reco"]
        sens = ""
        if g == "genre" and ecart_signe is not None and pd.notna(ecart_signe.get(r)):
            sens = "filles" if ecart_signe[r] < 0 else "garçons"
            reco += f" Groupe en retrait : {sens}."
        lignes[r] = {
            "profil": GROUPES[g]["nom"], "profil_code": g,
            "facteurs_dominants": [i for i, v in top.items() if v > 0],
            "groupe_en_retrait": sens or None,
            "recommandation": reco,
        }
    return pd.DataFrame.from_dict(lignes, orient="index")


def niveau_priorite(rang: float, n: int, top_k: int = 4) -> str:
    """Classe les régions selon le même seuil prioritaire que l'analyse de sensibilité."""
    priorite = min(max(int(top_k), 1), n)
    surveillance = min(2 * priorite, n)
    if rang <= priorite:
        return "prioritaire"
    return "à surveiller" if rang <= surveillance else "moins exposée"


def bornes_niveau(rang: float, n: int, top_k: int = 4) -> tuple[int, int]:
    """Plage de rangs du niveau, cohérente avec le seuil top-k prioritaire."""
    priorite = min(max(int(top_k), 1), n)
    surveillance = min(2 * priorite, n)
    if rang <= priorite:
        return 1, priorite
    if rang <= surveillance:
        return priorite + 1, surveillance
    return surveillance + 1, n
