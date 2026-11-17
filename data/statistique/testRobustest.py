import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

import numpy as np
import pandas as pd
import pytest
import yaml

from data.statistique import indice as ix
from data.statistique import robustesse as rb
from data.statistique.indicateur import calculer_indicateurs, ecart_vs_avant_choc, pivot
from data.regions import REGIONS
from data.statistique.runIndice import executer
from data.statistique.testIndice import PIRE, faire_tables

CFG = yaml.safe_load((RACINE / "data/config.yaml").read_text(encoding="utf-8"))
POIDS = CFG["indice"]["ponderations"]


def _serie(region, valeurs, annees=range(2015, 2025), sexe="T"):
    return [{"region_code": region, "sexe": sexe, "annee": a, "valeur": float(v)} for a, v in zip(annees, valeurs)]


# --- indicateurs -----------------------------------------------------------------
def test_tendance_est_l_ecart_a_la_periode_d_avant_le_choc():
    df = pd.DataFrame(_serie("BMH", [60] * 7 + [30, 40, 50]))
    # niveau récent (30, 40, 50) = 40 ; moyenne avant 2022 = 60 -> -20 points
    assert ecart_vs_avant_choc(pivot(df, "T"), 2022, k=3)["BMH"] == pytest.approx(-20.0)
    assert np.isnan(ecart_vs_avant_choc(pivot(df[df.annee >= 2022], "T"), 2022, k=3)["BMH"])


def test_taux_bruts_plafonnes_a_100():
    df = pd.DataFrame(_serie("CEN", [112] * 10) + _serie("NOR", [100] * 10) + _serie("SAH", [90] * 10))
    ind = calculer_indicateurs({"tbs": df}, 2022, k=3)
    assert ind["scolarisation_tbs"].round(6).to_dict() == {"CEN": 100.0, "NOR": 100.0, "SAH": 90.0}
    brut = calculer_indicateurs({"tbs": df}, 2022, k=3, plafond=None)
    assert brut.loc["CEN", "scolarisation_tbs"] == 112.0


def test_annee_max_ignore_les_donnees_posterieures():
    df = pd.DataFrame(_serie("BMH", [50] * 9 + [90]))
    assert calculer_indicateurs({"cep": df}, 2022, k=1)["reussite_cep"]["BMH"] == 90.0
    assert calculer_indicateurs({"cep": df}, 2022, k=1, annee_max=2023)["reussite_cep"]["BMH"] == 50.0


# --- normalisation --------------------------------------------------------------
def test_normalisations_bornes_et_orientation():
    x = list(range(1, 13)) + [1000.0]                      # une valeur extrême
    ind = pd.DataFrame({"ecart_genre_achevement": x, "achevement_niveau": x}, index=list(REGIONS))
    for m in ix.METHODES_NORMALISATION:
        r = ix.normaliser_risque(ind, m)
        assert r.min().min() >= 0 and r.max().max() <= 100
        # sens « haut » : la plus grande valeur a le risque maximal ; sens « bas » : la plus petite
        # (avec « robuste », les extrêmes sont bornés : d'autres régions peuvent partager le maximum)
        assert r.loc["SOU", "ecart_genre_achevement"] == r["ecart_genre_achevement"].max() == 100
        assert r.loc["BMH", "achevement_niveau"] == r["achevement_niveau"].max() == 100
        assert r.loc["BMH", "ecart_genre_achevement"] == 0 and r.loc["SOU", "achevement_niveau"] == 0
    minmax = ix.normaliser_risque(ind, "minmax")["ecart_genre_achevement"]
    robuste = ix.normaliser_risque(ind, "robuste")["ecart_genre_achevement"]
    assert minmax.iloc[6] < 1 and robuste.iloc[6] > 40      # l'extrême écrase l'échelle min-max, pas l'échelle robuste
    with pytest.raises(ValueError):
        ix.normaliser_risque(ind, "inconnue")


def test_bornes_niveau():
    assert ix.bornes_niveau(1, 13, 4) == (1, 4) and ix.bornes_niveau(5, 13, 4) == (5, 8)
    assert ix.bornes_niveau(9, 13, 4) == (9, 13)


# --- poids -------------------------------------------------------------------------
def test_poids_somme_un_et_aucune_source_dominante():
    assert sum(POIDS.values()) == pytest.approx(1.0)
    assert set(POIDS) <= set(ix.INDICATEURS)
    assert set(CFG["indice"]["justification_poids"]) == set(POIDS)         # chaque poids est justifié
    par_source = rb.poids_par_source(POIDS, list(POIDS))
    assert sum(par_source.values()) == pytest.approx(1.0)
    assert max(par_source.values()) <= 0.5                                  # aucune source > 50 %
    assert par_source["primaire_achevement_region"] == pytest.approx(0.45)
    assert par_source["primaire_ecoles_region"] == pytest.approx(0.075)     # le choc se partage entre 2 sources


# --- robustesse -------------------------------------------------------------------
@pytest.fixture(scope="module")
def ens():
    return rb.ensemble(faire_tables(), 2022, POIDS, normalisation="robuste", niveau_annees=3,
                       tirages=300, tirages_par_variante=5, top_k=4)


def test_ensemble_structure_et_region_vulnerable_stable(ens):
    res, resume = ens
    assert set(resume) == {"poids", "normalisation", "annees", "retrait", "combine"}
    assert {"rang_p5", "rang_p95", "rang_median", "prob_prioritaire"} <= set(res.columns)
    assert (res.rang_p5 <= res.rang_median).all() and (res.rang_median <= res.rang_p95).all()
    assert res.loc[PIRE, "prob_prioritaire"] > 0.95 and res.loc[PIRE, "rang_p95"] <= 2
    for fam, v in resume.items():
        assert -1 <= v["spearman_min"] <= v["spearman_moyen"] <= 1, fam
        assert 0 <= v["top_k_identique"] <= 1
    assert resume["combine"]["spearman_moyen"] > 0.8
    assert res.attrs["spearman_moyen"] == resume["combine"]["spearman_moyen"]
    assert resume["retrait"]["n_scenarios"] == len(POIDS)                   # un scénario par indicateur retiré


def test_ensemble_reproductible():
    t = faire_tables()
    a, _ = rb.ensemble(t, 2022, POIDS, tirages=100, tirages_par_variante=3)
    b, _ = rb.ensemble(t, 2022, POIDS, tirages=100, tirages_par_variante=3)
    pd.testing.assert_frame_equal(a, b)


# --- redondance et validation ------------------------------------------------------
def test_correlations_detecte_le_double_comptage():
    x = np.arange(13.0)
    risque = pd.DataFrame({"achevement_niveau": x, "scolarisation_tbs": x * 2 + 1, "entrees_cp1": x[::-1]}, index=list(REGIONS))
    c = rb.correlations(risque, 0.8)
    paires = {(p["a"], p["b"]): p["rho"] for p in c["paires_redondantes"]}
    assert paires[("achevement_niveau", "scolarisation_tbs")] == 1.0
    assert paires[("achevement_niveau", "entrees_cp1")] == -1.0             # corrélation négative aussi signalée
    assert c["matrice"]["achevement_niveau"]["achevement_niveau"] == 1.0


def test_validation_convergente():
    x = np.arange(13.0)
    index = list(REGIONS)
    lie = pd.DataFrame({"achevement_niveau": x, "achevement_tendance": x, "entrees_cp1": x + 1, "scolarisation_tbs": x * 2}, index=index)
    v = rb.validation_convergente(lie, POIDS)
    assert v["disponible"] and v["rho"] > 0.95 and v["p_permutation"] < 0.01 and v["association"] == "forte"
    assert "n'est pas une cause" in v["lecture"]
    independant = lie.copy()
    independant["entrees_cp1"] = np.random.default_rng(3).permutation(x)
    independant["scolarisation_tbs"] = np.random.default_rng(4).permutation(x)
    assert abs(rb.validation_convergente(independant, POIDS)["rho"]) < 0.6
    assert not rb.validation_convergente(lie.iloc[:3], POIDS)["disponible"]


def test_validation_attentes():
    rang = pd.Series(range(1, 14), index=list(REGIONS))
    v = rb.validation_attentes(rang, ["BMH", "CAS", "SOU", "ZZZ"], top_k=4)
    assert v["regions_attendues"] == ["BMH", "CAS", "SOU"] and v["dans_top_k"] == ["BMH", "CAS"]
    assert v["part_dans_top_k"] == pytest.approx(0.67, abs=0.01)
    assert not rb.validation_attentes(rang, [], 4)["disponible"]


# --- stabilité dans le temps -------------------------------------------------------
def test_historique():
    h = rb.historique(faire_tables(), 2022, POIDS, "robuste", 3)
    assert h["disponible"] and h["annees"] == ["2022/23", "2023/24", "2024/25"]
    assert all(h["rang_par_annee"][PIRE][a] == 1 for a in h["annees"])
    assert set(h["spearman_consecutifs"]) == {"2022/23 -> 2023/24", "2023/24 -> 2024/25"}
    assert all(-1 <= v <= 1 for v in h["spearman_consecutifs"].values())
    assert not rb.historique({"cep": pd.DataFrame(_serie("BMH", [1] * 10)).query("annee < 2022")}, 2022, POIDS)["disponible"]


# --- export de bout en bout -------------------------------------------------------
def test_export_enrichi_et_diagnostics(tmp_path):
    proc = tmp_path / "data/processed"
    proc.mkdir(parents=True)
    noms = {"achevement": "primaire_achevement_region", "effectifs": "primaire_effectifs_region",
            "ecoles": "primaire_ecoles_region", "cp1": "primaire_nouveaux_cp1_region",
            "cep": "primaire_cep_region", "tbs": "primaire_tbs_region", "presco_tbs": "prescolaire_T5"}
    for k, df in faire_tables().items():
        df.to_csv(proc / f"{noms[k]}.csv", index=False)
    cfg = json.loads(json.dumps(CFG))
    cfg["export_dir"] = "export"
    cfg["indice"]["sensibilite"]["tirages"] = 200
    cfg["validation"] = {"regions_attendues_vulnerables": [PIRE, "NOR"]}
    executer(tmp_path, cfg)

    exp = tmp_path / "export"
    indice = json.loads((exp / "indice.json").read_text(encoding="utf-8"))
    r0 = indice[0]
    assert r0["code"] == PIRE and isinstance(r0["classement_robuste"], bool)
    assert {"prob_prioritaire", "rang_p5", "rang_p95", "ecart_score_au_suivant", "confiance"} <= set(r0)
    assert indice[-1]["ecart_score_au_suivant"] is None                     # pas de région après la dernière
    meta = json.loads((exp / "metadata.json").read_text(encoding="utf-8"))
    assert meta["tableaux_absents"] == [] and meta["version_pipeline"] == "0.2.0"
    assert sum(meta["poids_par_source"].values()) == pytest.approx(1.0, abs=1e-3)
    assert meta["robustesse"]["combine"]["spearman_moyen"] > 0.8
    assert meta["validation"]["convergente"]["disponible"] and meta["validation"]["attentes"]["disponible"]
    assert meta["historique"]["disponible"] and "rang_par_annee" not in meta["historique"]
    assert set(meta["justification_poids"]) == set(POIDS)
    series = json.loads((exp / "series.json").read_text(encoding="utf-8"))
    assert series[PIRE]["rang_par_annee"]["2024/25"] == 1
    md = (tmp_path / "docs/diagnostics_indice.md").read_text(encoding="utf-8")
    for titre in ("D'où vient le score", "Verdict", "Redondance", "Validation", "Stabilité dans le temps", "Limites"):
        assert titre in md
    assert "Non réalisée" not in md                                        # attentes renseignées


def test_export_sans_validation_externe_le_dit(tmp_path):
    proc = tmp_path / "data/processed"
    proc.mkdir(parents=True)
    noms = {"achevement": "primaire_achevement_region", "effectifs": "primaire_effectifs_region",
            "ecoles": "primaire_ecoles_region", "cp1": "primaire_nouveaux_cp1_region",
            "cep": "primaire_cep_region", "tbs": "primaire_tbs_region", "presco_tbs": "prescolaire_T5"}
    for k, df in faire_tables().items():
        df.to_csv(proc / f"{noms[k]}.csv", index=False)
    cfg = json.loads(json.dumps(CFG))
    cfg["export_dir"] = "export"
    cfg["indice"]["sensibilite"]["tirages"] = 100
    executer(tmp_path, cfg)
    md = (tmp_path / "docs/diagnostics_indice.md").read_text(encoding="utf-8")
    assert "Non réalisée" in md and "À renseigner" in md
