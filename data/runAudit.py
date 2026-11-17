from __future__ import annotations
import json
import re
import unicodedata
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.audit import Journal, auditer_tableau, deviner_type
from data.ingestion import charger_feuille_multiple, charger_tableau

import yaml


def executer(chemin_config, racine=None):
    
    chemin_config = Path(chemin_config)
    cfg = yaml.safe_load(chemin_config.read_text(encoding="utf-8"))
    racine = Path(racine) if racine else chemin_config.resolve().parent.parent
    classeur = racine / cfg["classeur"]
    if not classeur.exists():
        raise FileNotFoundError(f"Classeur introuvable : {classeur}")
    
    annee_simple = cfg.get("annee_simple", "fin")
    periode = cfg.get("periode", {})
    premiere = periode.get("premiere_annee_scolaire")
    derniere = periode.get("derniere_annee_scolaire")
    annee_min = int(str(premiere).split("/")[0]) if premiere else periode.get("annee_debut")
    annee_max = int(str(derniere).split("/")[0]) if derniere else periode.get("annee_fin")
    sortie = racine / "data" / "processed"
    docs = racine / "docs"
    sortie.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)

    journal, rapports = Journal(), {}
    for nom, spec in cfg["feuilles"].items():
        try:
            if spec.get("multi"):
                tables = charger_feuille_multiple(classeur, spec["feuille"], annee_simple)
            else:
                tables = {nom: charger_tableau(classeur, spec["feuille"], annee_simple)}
        except Exception as e:  # feuille absente, en-tête introuvable...
            journal.log(nom, "ALERTE", "lecture", f"Feuille illisible : {type(e).__name__}: {e}")
            continue
        for titre, df in tables.items():
            if spec.get("multi"):
                m = re.search(r"Tableau\s*(\d+)", titre, re.I)
                nom_t = f"{nom}_T{m.group(1)}" if m else f"{nom}_{len(rapports)}"
            else:
                nom_t = nom
            options_table = cfg.get("tableaux", {}).get(nom_t, {})
            if options_table.get("renommage"):
                df = df.rename(columns=options_table["renommage"])
            if "annee" in df.columns:
                if annee_min is not None:
                    df = df[df["annee"] >= int(annee_min)]
                if annee_max is not None:
                    df = df[df["annee"] <= int(annee_max)]
            type_v = spec.get("type") or deviner_type(titre or nom)
            propre, rap = auditer_tableau(df, nom_t, type_v, journal)
            if propre is not None:
                propre.to_csv(sortie / f"{nom_t}.csv", index=False, encoding="utf-8-sig")
                rapports[nom_t] = rap

    (docs / "journal_traitement.md").write_text(journal.vers_markdown(), encoding="utf-8")
    (docs / "rapport_audit.json").write_text(json.dumps(rapports, ensure_ascii=False, indent=2), encoding="utf-8")
    arbitrages = docs / "doublons_a_arbitrer.csv"
    lignes = journal.arbitrages
    colonnes = list(dict.fromkeys(c for ligne in lignes for c in ligne)) or ["tableau", "decision"]
    with arbitrages.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(lignes)
    return rapports, journal


if __name__ == "__main__":
    racine = Path(__file__).resolve().parents[1]
    rapports, journal = executer(racine / "data" / "config.yaml", racine)
    alertes = [e for e in journal.entrees if e["niveau"] == "ALERTE"]
    print(f"{len(rapports)} tableaux traités, {len(alertes)} alertes. Voir docs/journal_traitement.md")
    for e in alertes:
        print(f" - [{e['tableau']}] {e['message']}" + (f" ({e['n']})" if e["n"] else ""))
