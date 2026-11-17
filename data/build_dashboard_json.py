"""Point d'entrée historique vers le pipeline statistique unique d'Éclaireur."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.statistique.runIndice import executer


def main() -> None:
    resultats, sensibilite, profils, _ = executer(ROOT)
    classement = resultats.join(sensibilite).join(profils[["profil"]]).sort_values("rang")
    print(f"Indice recalculé pour {len(classement)} régions dans data/config.yaml.")
    print("Exports canoniques : app/src/assets/data/ et docs/diagnostics_indice.md")


if __name__ == "__main__":
    main()
