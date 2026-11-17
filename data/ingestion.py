from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path

import pandas as pd


RE_PLAGE = re.compile(r"^\s*(\d{4})\s*[/\-–]\s*(\d{2,4})")
RE_SIMPLE = re.compile(r"^\s*(\d{4})(?:\.0+)?\s*$")

SEXE_MAPPING = {
    "G" : "G", "GARÇON" : "G", "GARCONs" : "G",
    "F" : "F", "FILLE" : "F", "FILLES" : "F",
    "T": "T", "TOTAL" : "T", "ENSEMBLE" : "T",
}


NA_TEXTES = {
    "", "-", "-", "-", "ND", "nd", "n.d", "N/A", "NA", "na",
    "n.a", "n.a.", "N.A.", "N.A", "..."
}


def _sans_accents(s:str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _vide(c) -> bool:
    if c is None:
        return True
    if isinstance(c, float) and math.isnan(c):
        return True
    return str(c).strip() == ""

def _vers_nombre(x) -> float:
    
    if _vide(x):
        return float("nan")
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    s = str(x).strip().replace(",", ".").replace(" ", "")
    if s in NA_TEXTES:
        return float("nan")
    s = s.replace("%", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")
    

def _sexe(c):
    if _vide(c):
        return None
    return SEXE_MAPPING.get(str(c).strip().upper())

def _annee(c, annee_simple:str = "fin"):
    
    if _vide(c):
        return None
    if isinstance(c, (int, float)) and not isinstance(c, bool):
        if not float(c).is_integer():
            return None
        s = str(int(c))
    else:
        s = str(c)
    m = RE_PLAGE.match(s)
    if m:
        debut = int(m.group(1))
    else:
        m = RE_SIMPLE.match(s)
        if not m:
            return None
        y = int(m.group(1))
        debut = y - 1 if annee_simple == "fin" else y
    return f"{debut}/{debut+1 % 100:02d}", debut


def _nom_cle(c) -> str:
    if _vide(c):
        return "region_brut"
    s = _sans_accents(str(c).strip().lower())
    if s.startswith("region"):
        return "region_brut"
    return re.sub(r"\W+", "_", s).strip("_") or "cle"


def lire_grille(chemin: str | Path, feuille: int |str = 0) -> list[list]:
    
    if chemin.suffix.lower() in { ".xlsx", ".xls", ".xlsm" }:
        df = pd.read_excel(chemin, sheet_name=feuille, header=None, dtype=object)
        
    else:
        texte = chemin.read_text(encoding="utf-8")
        premiere_ligne = texte.splitlines()[0] if texte else ""
        separateur = "\t" if "\t" in premiere_ligne else (";" if ";" in premiere_ligne else ",")
        lignes = [l.split(separateur) for l in texte.splitlines()]
        largeur = max(len(l) for l in lignes)
        df = pd.DataFrame([l + [""] * (largeur - len(l)) for l in lignes], dtype=object)
        
    return df.where(df.notna(), None).values.tolist()


def decouper_tableaux(grille: list[list]) -> list[tuple[str, list[list]]]:
    debuts = []
    
    for i, ligne in enumerate(grille):
        premiere_cellule = next((c for c in ligne if not _vide(c)), None)
        if isinstance(premiere_cellule, str) and re.match(r"^\s*Tableau\s+\d+", premiere_cellule, re.I):
            
            debuts.append((i, premiere_cellule.strip()))
            
    if not debuts:
        return [("", grille)]
    fins = [d[0] for d in debuts[1:]] + [len(grille)]
    return [(titre, grille[a:b]) for (a, titre), b in zip(debuts, fins)]

def parser_tableau(grille: list[list], annee_simple:str = "fin") -> pd.DataFrame:
    
    i_h = None
    for i, ligne in enumerate(grille[:15]):
        if sum(_annee(c, annee_simple) is not None for c in ligne) >= 2:
            i_h = i
            break
    if i_h is None:
        raise ValueError("Ligne d'en-tête (années) introuvable.")
    entete = grille[i_h]
    cols_annee = [j for j, c in enumerate(entete) if _annee(c, annee_simple)]

    # 2) ligne de sexes (G/F/T) juste après ? -> format large
    i_s = None
    for k in range(i_h + 1, min(i_h + 4, len(grille))):
        if sum(_sexe(c) is not None for c in grille[k]) >= 3:
            i_s = k
            break

    if i_s is not None:
        return _parser_large(grille, i_h, i_s, annee_simple)
    return _parser_long(grille, i_h, cols_annee, annee_simple)



def _parser_large(grille, i_h, i_s, annee_simple) -> pd.DataFrame:
    entete, ligne_sexe = grille[i_h], grille[i_s]
    nom_cle = _nom_cle(entete[0] if entete else None)
    annees, courante = [], None
    for c in entete:
        a = _annee(c, annee_simple)
        if a:
            courante = a
        annees.append(courante)
    enregistrements = []
    for ligne in grille[i_s + 1:]:
        if not ligne or _vide(ligne[0]):
            continue
        nom = str(ligne[0]).strip()
        for j in range(1, len(ligne)):
            if j >= len(ligne_sexe) or annees[j] is None or _sexe(ligne_sexe[j]) is None:
                continue
            enregistrements.append({
                nom_cle: nom,
                "annee_scolaire": annees[j][0],
                "annee": annees[j][1],
                "sexe": _sexe(ligne_sexe[j]),
                "valeur": _vers_nombre(ligne[j]),
            })
    return pd.DataFrame(enregistrements)


def _parser_long(grille, i_h, cols_annee, annee_simple) -> pd.DataFrame:
    entete = grille[i_h]
    n_cles = cols_annee[0]
    noms = [_nom_cle(c) for c in entete[:n_cles]]
    idx_sexe = noms.index("sexe") if "sexe" in noms else None
    dernier = [None] * n_cles
    enregistrements = []
    for ligne in grille[i_h + 1:]:
        cles = [None if _vide(c) else str(c).strip() for c in (list(ligne) + [None] * n_cles)[:n_cles]]
        valeurs = {j: _vers_nombre(ligne[j]) for j in cols_annee if j < len(ligne)}
        # la cellule de sexe peut être décalée dans une cellule de clé vide
        if idx_sexe is not None and cles[idx_sexe] is None:
            for p in range(n_cles):
                if p != idx_sexe and cles[p] and _sexe(cles[p]):
                    cles[idx_sexe], cles[p] = cles[p], None
                    break
        # report des clés fusionnées (sauf le sexe)
        for p in range(n_cles):
            if p == idx_sexe:
                continue
            if cles[p] is not None:
                dernier[p] = cles[p]
                for q in range(p + 1, n_cles):
                    if q != idx_sexe:
                        dernier[q] = None
            else:
                cles[p] = dernier[p]
        if all(math.isnan(v) for v in valeurs.values()):
            continue  # ligne de titre/région sans valeurs
        if all(c is None for c in cles):
            continue
        for j, v in valeurs.items():
            a = _annee(entete[j], annee_simple)
            rec = dict(zip(noms, cles))
            if idx_sexe is not None:
                rec["sexe"] = _sexe(cles[idx_sexe]) or cles[idx_sexe]
            rec.update({"annee_scolaire": a[0], "annee": a[1], "valeur": v})
            enregistrements.append(rec)
    return pd.DataFrame(enregistrements)


def charger_tableau(chemin: str | Path, feuille: int | str = 0, annee_simple:str = "fin") -> pd.DataFrame:
    grille = lire_grille(chemin, feuille)
    return parser_tableau(grille, annee_simple)


def charger_feuille_multiple(chemin: str | Path, feuille: int | str = 0, annee_simple:str = "fin") -> dict[str, pd.DataFrame]:
    grille = lire_grille(chemin, feuille)
    tableaux = decouper_tableaux(grille)
    return {
        
        titre: parser_tableau(sous, annee_simple)
        for titre, sous in tableaux
    
        }