"""Calcule indicateurs, indice, robustesse et profils, puis exporte les JSON pour l'application.

Usage (après l'audit) :
    python3 data/statistique/runIndice.py

Entrées  : data/processed/*.csv (sortie de l'audit)
Sorties  : <export_dir>/indicateurs.json, indice.json, profils.json, series.json, metadata.json
           data/processed/indice_regions.csv
           docs/dictionnaire_indicateurs.md, docs/diagnostics_indice.md
Tout s'exécute en local.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

import numpy as np
import pandas as pd
import yaml

from data.statistique import indice as ix
from data.statistique import robustesse as rb
from data.statistique.indicateur import calculer_indicateurs, pivot
from data.regions import REGIONS

VERSION = "0.2.0"
FICHIERS = {  # clé interne -> nom du CSV produit par l'audit (sans extension)
    "achevement": "primaire_achevement_region",
    "effectifs": "primaire_effectifs_region",
    "ecoles": "primaire_ecoles_region",
    "cp1": "primaire_nouveaux_cp1_region",
    "cep": "primaire_cep_region",
    "tbs": "primaire_tbs_region",
    "presco_tbs": "prescolaire_T5",
}


def _propre(x):
    """NaN/inf -> None, types numpy -> types Python (JSON strict)."""
    if isinstance(x, dict):
        return {str(k): _propre(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_propre(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not np.isfinite(x) else round(float(x), 4)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def _ecrire(chemin: Path, obj):
    chemin.write_text(json.dumps(_propre(obj), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def _rapport_diagnostics(meta: dict) -> str:
    """Rapport lisible (pour la note de synthèse et le jury) : ce que l'indice tient, et ce qu'il ne tient pas."""
    L = ["# Diagnostics de l'indice", "",
         f"Généré le {meta['genere_le']} (pipeline {meta['version_pipeline']}). "
         "Ces mesures disent si le classement est COHÉRENT et STABLE ; elles ne prouvent ni causalité ni "
         "taux de décrochage.", ""]
    L += ["## 1. D'où vient le score", "", "| Tableau source | Part du poids |", "|---|---|"]
    L += [f"| {s} | {100 * p:.0f} % |" for s, p in meta["poids_par_source"].items()]
    top = next(iter(meta["poids_par_source"].items()), None)
    if top:
        L += ["", f"Source la plus pesante : **{top[0]}** ({100 * top[1]:.0f} %)."]
    L += ["", "## 2. Justification des poids", "", "| Indicateur | Poids | Raison |", "|---|---|---|"]
    for c, w in meta["ponderations"].items():
        L.append(f"| {c} | {100 * w:.0f} % | {meta['justification_poids'].get(c, '')} |")

    rob = meta["robustesse"]
    L += ["", "## 3. Le classement résiste-t-il aux choix de méthode ?", "",
          f"Normalisation retenue : **{meta['normalisation']}** ; niveaux = moyenne des "
          f"{meta['niveau_annees']} dernières années ; « prioritaire » = top {meta['sensibilite']['top_k']}.", "",
          "| Ce qu'on fait varier | Scénarios | Spearman moyen | Spearman min | Même top-k |", "|---|---|---|---|---|"]
    noms = {"poids": "Les poids (tirage aléatoire ±50 %)", "normalisation": "La méthode de normalisation",
            "annees": "Le nombre d'années de référence", "retrait": "Retrait d'un indicateur à la fois",
            "combine": "**Tout à la fois**"}
    for k, v in rob.items():
        L.append(f"| {noms.get(k, k)} | {v['n_scenarios']} | {v['spearman_moyen']:.2f} | "
                 f"{v['spearman_min']:.2f} | {100 * v['top_k_identique']:.0f} % |")
    g = rob["combine"]
    verdict = ("stable" if g["spearman_moyen"] >= 0.9 and g["top_k_identique"] >= 0.6
               else "assez stable : certaines régions changent de rang" if g["spearman_moyen"] >= 0.8
               else "FRAGILE : le classement dépend fortement des choix de méthode")
    L += ["", f"Verdict : **{verdict}**. Un Spearman de 1 = classement identique au classement de référence.", ""]

    L += ["## 4. Redondance entre indicateurs", ""]
    pr = meta["correlations"]["paires_redondantes"]
    if pr:
        L += [f"Paires dont la corrélation dépasse {meta['correlations']['seuil']} (double comptage possible) :", ""]
        L += [f"- `{p['a']}` et `{p['b']}` : ρ = {p['rho']}" for p in pr]
    else:
        L += [f"Aucune paire d'indicateurs ne dépasse {meta['correlations']['seuil']} : pas de double comptage évident."]

    v = meta["validation"]["convergente"]
    L += ["", "## 5. Validation", "", "**Cohérence convergente** (les résultats scolaires vont-ils avec les facteurs d'accès et de perturbation ?)", ""]
    L += [("- " + v["lecture"] + f" p (permutation) = {v['p_permutation']}.") if v.get("disponible")
          else f"- Non calculée : {v.get('raison', '')}."]
    a = meta["validation"]["attentes"]
    L += ["", "**Confrontation au terrain**", ""]
    if a.get("disponible"):
        L += [f"- {len(a['dans_top_k'])}/{len(a['regions_attendues'])} régions attendues comme vulnérables sont dans le "
              f"top {a['top_k']} : " + ", ".join(f"{c} (rang {r})" for c, r in a["rangs"].items()) + "."]
    else:
        L += [f"- Non réalisée : {a['raison']}. **À renseigner pour une validation externe.**"]

    h = meta["historique"]
    L += ["", "## 6. Stabilité dans le temps", ""]
    if h.get("disponible"):
        L += ["| Transition | Spearman |", "|---|---|"] + [f"| {t} | {r} |" for t, r in h["spearman_consecutifs"].items()]
        if h["sauts"]:
            L += ["", f"Changements de {h['seuil_saut']} rangs ou plus (à expliquer : rupture de données ou vrai changement) :", ""]
            L += [f"- {s['region']} : {s['variation_rang']:+d} rangs de {s['de']} à {s['vers']}" for s in h["sauts"]]
        else:
            L += ["", "Aucune région ne change brutalement de rang."]
    else:
        L += [f"Non calculée : {h.get('raison', '')}."]

    L += ["", "## 7. Limites", ""] + [f"- {x}" for x in meta["limites"]]
    if meta["tableaux_absents"]:
        L += ["", "Tableaux absents (indicateurs non calculés) : " + ", ".join(meta["tableaux_absents"]) + "."]
    return "\n".join(L) + "\n"


def executer(racine: Path, cfg: dict | None = None):
    racine = Path(racine)
    cfg = cfg or yaml.safe_load((racine / "data" / "config.yaml").read_text(encoding="utf-8"))
    proc = racine / "data" / "processed"
    export = racine / cfg.get("export_dir", "app/src/assets/data")
    export.mkdir(parents=True, exist_ok=True)
    (racine / "docs").mkdir(exist_ok=True)

    tables, absents = {}, []
    for cle, nom in FICHIERS.items():
        f = proc / f"{nom}.csv"
        if f.exists():
            tables[cle] = pd.read_csv(f)
        else:
            absents.append(nom)

    annee_choc = cfg.get("signaux_perturbation", {}).get("annee_choc", 2022)
    cfg_i = cfg["indice"]
    poids = cfg_i["ponderations"]
    norm = cfg_i.get("normalisation", "minmax")
    k_niv = cfg_i.get("niveau_annees", 2)
    cfg_r = cfg_i.get("robustesse", {})
    top_k = cfg.get("priorite_top_k", 4)

    ind = calculer_indicateurs(tables, annee_choc, k=k_niv)
    risque = ix.normaliser_risque(ind, norm)
    res = ix.calculer_indice(risque, poids)
    sens, rob = rb.ensemble(
        tables, annee_choc, poids, normalisation=norm, niveau_annees=k_niv,
        normalisations=cfg_r.get("normalisations", ["minmax", "robuste", "rang"]),
        niveaux=cfg_r.get("niveau_annees", [1, 2, 3]),
        amplitude=cfg_i["sensibilite"]["amplitude"], tirages=cfg_i["sensibilite"]["tirages"],
        tirages_par_variante=cfg_r.get("tirages_par_variante", 20), top_k=top_k)
    contrib = ix.contributions(risque, poids)
    prof = ix.profils(contrib, risque, ind.get("ecart_signe"))

    colonnes = [c for c in poids if c in risque.columns]
    corr = rb.correlations(risque[colonnes], cfg_r.get("seuil_redondance", 0.8))
    valid_conv = rb.validation_convergente(risque, poids)
    valid_att = rb.validation_attentes(res["rang"], (cfg.get("validation") or {}).get("regions_attendues_vulnerables"), top_k)
    hist = rb.historique(tables, annee_choc, poids, norm, k_niv, cfg_r.get("seuil_saut_rang", 4))

    n_annees = tables["achevement"]["annee"].nunique() if "achevement" in tables else None
    n = int(res["score"].notna().sum())
    classe = res.sort_values("rang")
    ecart_suivant = (classe["score"] - classe["score"].shift(-1)).to_dict()

    regions_out, profils_out, indic_out = [], [], {}
    for code in classe.index:
        r, s = res.loc[code], sens.loc[code]
        niveau, robuste = None, None
        if pd.notna(r["rang"]):
            niveau = ix.niveau_priorite(r["rang"], n, top_k)
            lo, hi = ix.bornes_niveau(r["rang"], n, top_k)
            robuste = bool(s["rang_p5"] >= lo and s["rang_p95"] <= hi)   # tout l'intervalle reste dans le niveau
        regions_out.append({
            "code": code, "region": REGIONS.get(code, code), "score": r["score"], "rang": r["rang"],
            "rang_p5": s["rang_p5"], "rang_p95": s["rang_p95"], "rang_median": s["rang_median"],
            "prob_prioritaire": s["prob_prioritaire"], "niveau": niveau,
            "classement_robuste": robuste,
            "ecart_score_au_suivant": ecart_suivant.get(code),
            "confiance": ix.niveau_confiance(r["couverture_poids"], n_annees),
            "couverture_poids": r["couverture_poids"],
        })
        p = prof.loc[code].to_dict()
        p.update({"code": code, "region": REGIONS.get(code, code), "contributions": contrib.loc[code].to_dict()})
        profils_out.append(p)
        indic_out[code] = {c: {"valeur": ind.loc[code, c], "risque": risque.loc[code, c] if c in risque.columns else None}
                           for c in ind.columns}

    series = {}
    if "achevement" in tables:
        for sexe in ("G", "F", "T"):
            for code, ligne in pivot(tables["achevement"], sexe).iterrows():
                series.setdefault(code, {}).setdefault("achevement", {})[sexe] = {
                    str(a): v for a, v in ligne.dropna().items()}
    if hist.get("disponible"):
        for code, rangs in hist["rang_par_annee"].items():
            series.setdefault(code, {})["rang_par_annee"] = rangs

    rapport_audit = {}
    f = racine / "docs" / "rapport_audit.json"
    if f.exists():
        rapport_audit = {k: v.get("ruptures_par_annee", {}) for k, v in json.loads(f.read_text(encoding="utf-8")).items()}

    par_source = rb.poids_par_source(poids, colonnes)
    limites = [
        "Unité d'analyse : 13 régions ; le classement est relatif et dépend des régions comparées.",
        "Facteurs associés, pas causes : aucune causalité n'est établie.",
        "Insécurité, pauvreté, enseignants et distances ne sont pas dans les données : "
        "le choc de 2022/23 (écoles, effectifs) sert de signal de perturbation indirect.",
        "Les taux bruts sont plafonnés à 100 ; le taux de réussite au CEP est calculé sur les candidats "
        "et peut masquer des sorties avant l'examen.",
        "Les données agrégées ne suivent pas les mêmes élèves : le score ne mesure pas des abandons.",
        "Les valeurs manquantes ne sont pas imputées ; les poids sont renormalisés. La confiance affichée décrit la couverture des données, pas une confiance statistique.",
    ]
    if any(v > 0.5 for v in par_source.values()):
        limites.append("Plus de la moitié du poids repose sur une seule source : le score est peu diversifié.")

    meta = {
        "version_pipeline": VERSION,
        "genere_le": dt.date.today().isoformat(),
        "lecture_du_score": "0 = risque le plus faible observé, 100 = le plus élevé, relatif aux régions. "
                            "Classement de vulnérabilité éducative, pas un taux de décrochage.",
        "lecture_confiance": "Indicateur descriptif de couverture des pondérations et de disponibilité temporelle ; "
                             "ce n'est pas un intervalle ni une probabilité statistique.",
        "normalisation": norm, "niveau_annees": k_niv,
        "ponderations": poids, "justification_poids": cfg_i.get("justification_poids", {}),
        "poids_par_source": par_source,
        "sensibilite": {"tirages": cfg_i["sensibilite"]["tirages"], "amplitude": cfg_i["sensibilite"]["amplitude"],
                        "top_k": top_k, "spearman_moyen": sens.attrs["spearman_moyen"],
                        "spearman_min": sens.attrs["spearman_min"]},
        "robustesse": rob,
        "correlations": corr,
        "validation": {"convergente": valid_conv, "attentes": valid_att},
        "historique": {k: v for k, v in hist.items() if k != "rang_par_annee"},
        "annee_choc": annee_choc,
        "indicateurs": {c: {**ix.INDICATEURS[c]} for c in ind.columns if c in ix.INDICATEURS},
        "tableaux_absents": absents,
        "ruptures_detectees_audit": rapport_audit,
        "limites": limites,
    }

    _ecrire(export / "indice.json", regions_out)
    _ecrire(export / "profils.json", profils_out)
    _ecrire(export / "indicateurs.json", indic_out)
    _ecrire(export / "series.json", series)
    _ecrire(export / "metadata.json", meta)

    tab = res.join(sens).join(prof[["profil"]])
    tab.insert(0, "region", [REGIONS.get(c, c) for c in tab.index])
    tab.sort_values("rang").to_csv(proc / "indice_regions.csv", encoding="utf-8-sig")

    dico = ["# Dictionnaire des indicateurs", "",
            "| Indicateur | Définition | Sens du risque | Poids | Source(s) | Avertissement |", "|---|---|---|---|---|---|"]
    for c, m in ix.INDICATEURS.items():
        sens_txt = "valeur basse = risque élevé" if m["sens"] == "bas" else "valeur haute = risque élevé"
        dico.append(f"| `{c}` | {m['label']} | {sens_txt} | {poids.get(c, 0)} | {', '.join(m['sources'])} | {m.get('note', '')} |")
    (racine / "docs" / "dictionnaire_indicateurs.md").write_text("\n".join(dico) + "\n", encoding="utf-8")
    (racine / "docs" / "diagnostics_indice.md").write_text(_rapport_diagnostics(meta), encoding="utf-8")
    return res, sens, prof, ind


if __name__ == "__main__":
    racine = RACINE
    res, sens, prof, ind = executer(racine)
    t = res.join(sens).join(prof[["profil"]]).sort_values("rang")
    print(f"{len(t)} régions classées. Stabilité globale (Spearman moyen) : {sens.attrs['spearman_moyen']:.2f}")
    print(t[["score", "rang", "rang_p5", "rang_p95", "prob_prioritaire", "profil"]].round(2).to_string())
    print("Détail : docs/diagnostics_indice.md")
