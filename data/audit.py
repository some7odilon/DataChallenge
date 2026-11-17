from __future__ import annotations

import re
import csv
import html

import numpy as np
import pandas as pd

from data.regions import REGIONS, harmoniser_region

COLS_VALEUR = {"annee_scolaire", "annee", "valeur"}
SEUIL_RUPTURE = 0.30  # variation annuelle relative signalée


class Journal:
    def __init__(self):
        self.entrees: list[dict] = []
        self.arbitrages: list[dict] = []

    def log(self, tableau, niveau, etape, message, n=None):
        self.entrees.append({"tableau": tableau, "niveau": niveau, "etape": etape,
                             "message": message, "n": None if n is None else int(n)})

    def vers_markdown(self) -> str:
        sortie = ["# Journal de traitement", "",
                  "Généré automatiquement par `data/runAudit.py`. "
                  "Les valeurs conflictuelles à vérifier sont consignées séparément dans `docs/doublons_a_arbitrer.csv`.", ""]
        tableaux = list(dict.fromkeys(e["tableau"] for e in self.entrees))
        for t in tableaux:
            sortie += [f"## {t}", "", "| Niveau | Étape | Message | N |", "|---|---|---|---|"]
            for e in (x for x in self.entrees if x["tableau"] == t):
                n = "" if e["n"] is None else e["n"]
                sortie.append(f"| {e['niveau']} | {e['etape']} | {e['message']} | {n} |")
            sortie.append("")
        return "\n".join(sortie)


def deviner_type(titre: str) -> str:
    t = titre.lower()
    if re.search(r"\bips\b", t):
        return "indice"
    if re.search(r"\b(tbs|tba|tap)\b", t):
        return "taux_brut"
    if "taux" in t:
        return "taux_pct"
    if any(m in t for m in ("nombre", "structures", "salles", "écoles", "ecoles")):
        return "nombre"
    return "effectif"


def auditer_tableau(df: pd.DataFrame, nom: str, type_valeur: str, journal: Journal):
    """Retourne (tableau_propre, rapport) ou (None, None) si le tableau est inutilisable."""
    def j(niveau, etape, msg, n=None):
        journal.log(nom, niveau, etape, msg, n)

    if df is None or df.empty or "valeur" not in df.columns:
        j("ALERTE", "structure", "Tableau vide ou illisible : ignoré")
        return None, None

    df = df.copy()
    n_initial = len(df)
    cles = [c for c in df.columns if c not in COLS_VALEUR]
    for c in cles:
        df[c] = df[c].astype("string").str.strip()
    j("INFO", "structure", f"{n_initial} lignes lues ; clés : {', '.join(cles) or 'aucune'} ; "
      f"{df['annee_scolaire'].nunique()} années ({df['annee_scolaire'].min()} à {df['annee_scolaire'].max()})")

    # ---- 1. régions
    a_region = "region_brut" in df.columns
    agreg = None
    regions_manquantes: list[str] = []
    if a_region:
        mapping = {b: harmoniser_region(b) for b in df["region_brut"].dropna().unique()}
        df["region_code"] = df["region_brut"].map(lambda b: mapping.get(b, {}).get("code"))
        df["region"] = df["region_brut"].map(lambda b: mapping.get(b, {}).get("region"))
        methode = df["region_brut"].map(lambda b: mapping.get(b, {}).get("methode"))
        for b, m in mapping.items():
            if m["methode"] in ("alias", "approx"):
                j("CORRECTION", "regions", f"« {b} » rapproché de {m['region']} ({m['methode']}, score {m['score']}) : à valider")
        agreg = df[methode == "agregat"]
        if len(agreg):
            j("CORRECTION", "regions", "Lignes d'agrégat (national/total) mises de côté pour contrôle", len(agreg))
        inconnus = df[methode == "inconnu"]
        if len(inconnus):
            valeurs = sorted(inconnus["region_brut"].dropna().unique())[:10]
            libelles = ", ".join(
                html.escape(" ".join(str(v).split()), quote=False)[:80]
                if len(" ".join(str(v).split())) <= 80 else "[libellé long masqué]"
                for v in valeurs
            )
            j("ALERTE", "regions", f"Libellés non reconnus, lignes écartées : {libelles}", len(inconnus))
        agreg_region = df[methode == "agregat_region"]
        if len(agreg_region):
            j("INFO", "regions", "Totaux régionaux mis de côté (ils ne sont pas des régions supplémentaires)", len(agreg_region))
        df = df[methode.isin(["exact", "alias", "approx"])].copy()
        regions_manquantes = sorted(set(REGIONS) - set(df["region_code"].dropna()))
        trouvees = df["region_code"].nunique()
        if regions_manquantes:
            j("ALERTE", "regions", f"{trouvees}/13 régions trouvées ; absentes : {', '.join(regions_manquantes)}")
        else:
            j("INFO", "regions", "13/13 régions trouvées")

    cles_an = [c for c in cles if c != "region_brut"] + (["region_code"] if a_region else [])
    sous = cles_an + ["annee_scolaire"]

    # ---- 2. doublons
    exact = df.duplicated(subset=sous + ["valeur"], keep="first")
    if exact.any():
        j("CORRECTION", "doublons", "Doublons exacts supprimés", exact.sum())
        df = df[~exact]
    conflit = df.duplicated(subset=sous, keep=False)
    if conflit.any():
        lignes_conflit = df.loc[conflit].copy()
        j("ALERTE", "doublons", "Valeurs contradictoires exclues en attente d'arbitrage ; détails dans doublons_a_arbitrer.csv", conflit.sum())
        for _, ligne in lignes_conflit.iterrows():
            entree = {"tableau": nom}
            entree.update({c: None if pd.isna(ligne[c]) else ligne[c] for c in sous})
            entree["valeur_candidate"] = None if pd.isna(ligne["valeur"]) else ligne["valeur"]
            entree["decision"] = "À vérifier dans le classeur source"
            journal.arbitrages.append(entree)
        df = df.loc[~conflit].copy()
    if not exact.any() and not conflit.any():
        j("INFO", "doublons", "Aucun doublon")

    # ---- 3. valeurs manquantes et incohérentes
    nan = int(df["valeur"].isna().sum())
    j("ALERTE" if nan else "INFO", "manquants", "Valeurs manquantes conservées (pas d'imputation)" if nan else "Aucune valeur manquante", nan or None)
    neg = df["valeur"] < 0
    if neg.any():
        df.loc[neg, "valeur"] = np.nan
        j("CORRECTION", "valeurs", "Valeurs négatives remplacées par « manquant »", neg.sum())
    limite = {"taux_pct": 100, "taux_achevement": 100, "taux_brut": 200}.get(type_valeur)
    if limite:
        hors = df["valeur"] > limite
        if hors.any():
            j("ALERTE", "valeurs", f"Valeurs au-dessus de {limite} (non modifiées)", hors.sum())
    if type_valeur in ("effectif", "nombre"):
        non_entier = df["valeur"].notna() & (df["valeur"] % 1 != 0)
        if non_entier.any():
            j("ALERTE", "valeurs", "Effectifs non entiers", non_entier.sum())

    # ---- 4. couverture par région
    if a_region and len(df):
        attendu = df["annee_scolaire"].nunique()
        couverture = df.dropna(subset=["valeur"]).groupby("region_code")["annee_scolaire"].nunique()
        incomplets = sorted(couverture[couverture < attendu].index)
        if incomplets:
            j("ALERTE", "couverture", f"Régions avec séries incomplètes : {', '.join(incomplets)}", len(incomplets))

    # ---- 5. cohérence G + F = T
    if type_valeur in ("effectif", "nombre") and "sexe" in df.columns and {"G", "F", "T"} <= set(df["sexe"].dropna()):
        autres = [c for c in sous if c != "sexe"]
        p = df.pivot_table(index=autres, columns="sexe", values="valeur", aggfunc="first")
        ok = p[["G", "F", "T"]].dropna()
        if len(ok):
            ecart = (ok["G"] + ok["F"] - ok["T"]).abs()
            mauvais = int((ecart > np.maximum(1, 0.001 * ok["T"])).sum())
            j("ALERTE" if mauvais else "INFO", "coherence", "Cas où garçons + filles ≠ total" if mauvais else "Garçons + filles = total partout", mauvais or None)

    # ---- 6. contrôle national = somme des régions
    if a_region and agreg is not None and len(agreg) and type_valeur in ("effectif", "nombre"):
        hors_region = [c for c in sous if c != "region_code"]
        a = agreg.groupby(hors_region)["valeur"].first()
        s = df.groupby(hors_region)["valeur"].sum(min_count=1)
        rel = ((s - a) / a).abs().dropna()
        if len(rel):
            mauvais = int((rel > 0.01).sum())
            j("ALERTE" if mauvais else "INFO", "coherence", "Écarts > 1 % entre national et somme des régions" if mauvais else "National = somme des régions", mauvais or None)

    # ---- 7. ruptures de série
    ruptures_par_annee: dict[str, str] = {}
    d = df.dropna(subset=["valeur"]).copy()
    if "sexe" in d.columns and "T" in set(d["sexe"].dropna()):
        d = d[d["sexe"] == "T"]
    grp = [c for c in cles_an if c != "sexe"]
    if len(d):
        if not grp:
            d["_g"] = 1
            grp = ["_g"]
        d = d.sort_values("annee")
        d["var"] = d.groupby(grp)["valeur"].pct_change()
        n_series = d.groupby(grp).ngroups
        fortes = d[d["var"].abs() > SEUIL_RUPTURE]
        for annee, bloc in fortes.groupby("annee_scolaire"):
            k = bloc.groupby(grp).ngroups
            ruptures_par_annee[annee] = f"{k}/{n_series}"
            nature = "systémique (choc général ou changement de méthode)" if k / n_series > 0.5 else "localisée"
            j("ALERTE", "ruptures", f"Variation > {int(SEUIL_RUPTURE*100)} % en {annee} : {k}/{n_series} séries, rupture {nature}", k)

    # ---- sortie
    prefixe = (["region_code", "region"] if a_region else [])
    autres_cles = [c for c in cles if c != "region_brut"]
    propre = df[prefixe + autres_cles + ["annee_scolaire", "annee", "valeur"]].reset_index(drop=True)
    propre["annee"] = propre["annee"].astype(int)
    rapport = {
        "type": type_valeur, "lignes_initiales": n_initial, "lignes_finales": len(propre),
        "regions_manquantes": regions_manquantes, "ruptures_par_annee": ruptures_par_annee,
        "valeurs_manquantes": int(propre["valeur"].isna().sum()),
    }
    j("INFO", "sortie", f"{len(propre)} lignes propres exportées (sur {n_initial})")
    return propre, rapport
