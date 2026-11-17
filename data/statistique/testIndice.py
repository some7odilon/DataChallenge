import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

import numpy as np
import pandas as pd
import yaml

from data.statistique import indice as ix
from data.statistique.indicateur import calculer_indicateurs, choc, niveau_recent, pente, pivot
from data.regions import REGIONS
from data.statistique.runIndice import executer

ANNEES = list(range(2015, 2025))
PIRE, ECOLE_GARCONS = "SAH", "NOR"


def _long(valeurs_par_sexe, region, extra=None):
    lignes = []
    for sexe, serie in valeurs_par_sexe.items():
        for a, v in zip(ANNEES, serie):
            d = {"region_code": region, "region": REGIONS[region], "sexe": sexe,
                 "annee_scolaire": f"{a}/{(a+1)%100:02d}", "annee": a, "valeur": v}
            if extra:
                d.update(extra)
            lignes.append(d)
    return lignes


def faire_tables(seed=0):
    rng = np.random.default_rng(seed)
    t = {k: [] for k in ("achevement", "effectifs", "ecoles", "cp1", "cep", "tbs", "presco_tbs")}
    for code in REGIONS:
        pire = code == PIRE
        base = 40 if pire else rng.uniform(55, 80)
        tend = -1.5 if pire else rng.uniform(-0.2, 0.6)
        T = base + tend * np.arange(10) + rng.normal(0, 0.5, 10)
        ecart = -6 if pire else (8 if code == ECOLE_GARCONS else rng.uniform(-2, 2))  # F - G
        G, F = T - ecart / 2, T + ecart / 2
        t["achevement"] += _long({"G": G, "F": F, "T": T}, code)

        eff = 100000 * (1 + rng.uniform(0, 0.5)) * np.ones(10)
        chute = 0.45 if pire else rng.uniform(0, 0.08)
        eff[7:] *= 1 - chute
        eff[9] = eff[6] * (1 - chute * (0.9 if pire else 0.2))
        t["effectifs"] += _long({"T": eff, "G": eff / 2, "F": eff / 2}, code)
        ecoles = 1000 * np.ones(10)
        ecoles[7:] *= 1 - chute
        t["ecoles"] += _long({"T": ecoles}, code) if False else [
            {**r, "statut": "Total"} for r in _long({"T": ecoles}, code)]
        cp1 = 50000 * np.ones(10)
        cp1[7:] *= 1 - chute
        t["cp1"] += _long({"T": cp1}, code)
        t["cep"] += _long({"T": (45 if pire else rng.uniform(60, 80)) * np.ones(10)}, code)
        t["tbs"] += _long({"T": (60 if pire else rng.uniform(80, 112)) * np.ones(10)}, code)   # certains > 100
        t["presco_tbs"] += _long({"T": (2 if pire else rng.uniform(3, 8)) * np.ones(10)}, code)
    return {k: pd.DataFrame(v) for k, v in t.items()}


def test_indicateurs_basiques():
    df = pd.DataFrame({"region_code": ["BMH"] * 5, "annee": [2015, 2016, 2017, 2018, 2019],
                       "sexe": ["T"] * 5, "valeur": [10.0, 12, 14, 16, 18]})
    pv = pivot(df, "T")
    assert abs(pente(pv)["BMH"] - 2.0) < 1e-9
    assert niveau_recent(pv, 2)["BMH"] == 17.0
    # choc : valeur 100 avant, 60 pendant, 90 récemment
    c = pd.DataFrame({"region_code": ["BMH"] * 4, "annee": [2021, 2022, 2023, 2024], "sexe": "T",
                      "valeur": [100.0, 60, 80, 100]})
    r = choc(pivot(c, "T"), 2022)
    assert abs(r.loc["BMH", "perte_pic"] - 0.4) < 1e-9
    assert abs(r.loc["BMH", "deficit_residuel"] - 0.1) < 1e-9     # moyenne(80, 100) = 90 -> 10 %


def test_deficit_residuel_valeur():
    c = pd.DataFrame({"region_code": ["BMH"] * 4, "annee": [2021, 2022, 2023, 2024], "sexe": "T",
                      "valeur": [100.0, 60, 80, 100]})
    assert abs(choc(pivot(c, "T"), 2022).loc["BMH", "deficit_residuel"] - 0.1) < 1e-9


def test_classement_retrouve_la_region_vulnerable():
    ind = calculer_indicateurs(faire_tables(), 2022)
    assert len(ind) == 13
    cfg = yaml.safe_load((RACINE / "data/config.yaml").read_text(encoding="utf-8"))
    poids = cfg["indice"]["ponderations"]
    risque = ix.normaliser_risque(ind)
    assert risque.min().min() >= 0 and risque.max().max() <= 100
    res = ix.calculer_indice(risque, poids)
    assert res.loc[PIRE, "rang"] == 1
    sens = ix.sensibilite(risque, poids, 0.5, 500, 4)
    assert sens.loc[PIRE, "prob_prioritaire"] > 0.95
    assert sens.loc[PIRE, "rang_p95"] <= 2
    assert sens.attrs["spearman_moyen"] > 0.8
    # direction de l'écart de genre : filles en retrait dans la région vulnérable, garçons ailleurs
    assert ind.loc[PIRE, "ecart_signe"] < 0 and ind.loc[ECOLE_GARCONS, "ecart_signe"] > 0
    prof = ix.profils(ix.contributions(risque, poids), risque, ind["ecart_signe"])
    # la région à fort écart en faveur des filles est profilée « genre », avec les garçons en retrait
    assert prof.loc[ECOLE_GARCONS, "profil_code"] == "genre"
    assert prof.loc[ECOLE_GARCONS, "groupe_en_retrait"] == "garçons"
    assert "garçons" in prof.loc[ECOLE_GARCONS, "recommandation"]
    # les profils ne sont pas tous identiques malgré les poids inégaux
    assert prof["profil_code"].nunique() >= 2
    assert len(prof.loc[PIRE, "facteurs_dominants"]) >= 1


def test_valeur_manquante_poids_renormalises():
    ind = calculer_indicateurs(faire_tables(), 2022)
    ind.loc["CAS", "reussite_cep"] = np.nan
    cfg = yaml.safe_load((RACINE / "data/config.yaml").read_text(encoding="utf-8"))
    res = ix.calculer_indice(ix.normaliser_risque(ind), cfg["indice"]["ponderations"])
    assert np.isfinite(res.loc["CAS", "score"])
    assert abs(res.loc["CAS", "couverture_poids"] - (1 - cfg["indice"]["ponderations"]["reussite_cep"])) < 1e-9
    assert ix.niveau_confiance(0.8) == "moyenne" and ix.niveau_confiance(0.5) == "faible"


def test_table_absente_ne_plante_pas():
    t = faire_tables()
    del t["cep"], t["presco_tbs"]
    ind = calculer_indicateurs(t, 2022)
    assert "reussite_cep" not in ind.columns and "achevement_niveau" in ind.columns


def test_bout_en_bout_export_json_strict(tmp_path):
    proc = tmp_path / "data/processed"
    proc.mkdir(parents=True)
    noms = {"achevement": "primaire_achevement_region", "effectifs": "primaire_effectifs_region",
            "ecoles": "primaire_ecoles_region", "cp1": "primaire_nouveaux_cp1_region",
            "cep": "primaire_cep_region", "tbs": "primaire_tbs_region", "presco_tbs": "prescolaire_T5"}
    for k, df in faire_tables().items():
        if k == "presco_tbs":
            continue                                              # tableau absent -> listé dans metadata
        df.to_csv(proc / f"{noms[k]}.csv", index=False)
    cfg = yaml.safe_load((RACINE / "data/config.yaml").read_text(encoding="utf-8"))
    cfg["export_dir"] = "export"
    executer(tmp_path, cfg)
    exp = tmp_path / "export"
    indice = json.loads((exp / "indice.json").read_text(encoding="utf-8"))
    assert len(indice) == 13 and indice[0]["code"] == PIRE and indice[0]["niveau"] == "prioritaire"
    assert [r["rang"] for r in indice] == sorted(r["rang"] for r in indice)
    assert sum(r["niveau"] == "prioritaire" for r in indice) == cfg["priorite_top_k"]
    meta = json.loads((exp / "metadata.json").read_text(encoding="utf-8"))
    assert meta["tableaux_absents"] == ["prescolaire_T5"] and "limites" in meta
    series = json.loads((exp / "series.json").read_text(encoding="utf-8"))
    assert set(series[PIRE]["achevement"]) == {"G", "F", "T"}
    prof = json.loads((exp / "profils.json").read_text(encoding="utf-8"))
    assert all(p["recommandation"] for p in prof)
    assert (tmp_path / "docs/dictionnaire_indicateurs.md").exists()
    assert (proc / "indice_regions.csv").exists()
