from __future__ import annotations

import difflib
import re
import unicodedata
from pathlib import Path


REGIONS = {
    "BMH": "BOUCLE DU MOUHOUN",
    "CAS": "CASCADES",
    "CEN": "CENTRE",
    "CES": "CENTRE-EST",
    "CNO": "CENTRE-NORD",
    "COU": "CENTRE-OUEST",
    "CSU": "CENTRE-SUD",
    "EST": "EST",
    "HBS": "HAUTS-BASSINS",
    "NOR": "NORD",
    "PCL": "PLATEAU-CENTRAL",
    "SAH": "SAHEL",
    "SOU": "SUD-OUEST",
}


def normaliser(s) -> str:
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Za-z0-9]+", " ", s).upper().strip()
    return re.sub(r"\s+", " ", s)


_NORM_CANON = {normaliser(nom): code for code, nom in REGIONS.items()}
_ALIAS = {
    "BOUCLE DE MOUHOUN": "BMH",
    "BOUCLE MOUHOUN": "BMH",
    "MOUHOUN": "BMH",
    "HAUT BASSINS": "HBS",
    "HAUTS BASSIN": "HBS",
    "PLATEAU CENTRALE": "PCL",
}
_AGREGATS = {
    normaliser(x)
    for x in ["BURKINA FASO", "BURKINA", "NATIONAL", "TOTAL", "ENSEMBLE",
              "TOTAL NATIONAL", "TOTAL GENERAL", "TOUTES LES REGIONS", "NATION", "BF"]
}


def harmoniser_region(brut) -> dict:
    """Retourne un code et une méthode, en séparant les totaux régionaux et nationaux."""
    n = normaliser(brut)
    if n in _AGREGATS:
        return {"code": None, "region": None, "methode": "agregat", "score": 1.0}
    if n.startswith("TOTAL "):
        cible = n.removeprefix("TOTAL ").strip()
        code = _NORM_CANON.get(cible) or _ALIAS.get(cible)
        if code:
            return {"code": code, "region": REGIONS[code], "methode": "agregat_region", "score": 1.0}
    if n in _NORM_CANON:
        c = _NORM_CANON[n]
        return {"code": c, "region": REGIONS[c], "methode": "exact", "score": 1.0}
    if n in _ALIAS:
        c = _ALIAS[n]
        return {"code": c, "region": REGIONS[c], "methode": "alias", "score": 1.0}
    proche = difflib.get_close_matches(n, list(_NORM_CANON), n=1, cutoff=0.85)
    if proche:
        c = _NORM_CANON[proche[0]]
        score = difflib.SequenceMatcher(None, n, proche[0]).ratio()
        return {"code": c, "region": REGIONS[c], "methode": "approx", "score": round(score, 2)}
    return {"code": None, "region": None, "methode": "inconnu", "score": 0.0}
