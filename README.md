# Éclaireur — aide à la décision scolaire

Éclaireur analyse des indicateurs scolaires agrégés pour signaler les régions où plusieurs facteurs sont associés à une vulnérabilité éducative. Le projet comprend un pipeline Python d’audit et de calcul, des exports JSON et une application Angular.

> **Portée du résultat :** le score classe des régions selon des signaux indirects. Il ne mesure pas directement le décrochage, ne suit pas les parcours individuels et n’établit pas de causalité.

## Démarrer l’application

Prérequis : Node.js et npm.

```bash
cd eclaireur
npm ci
npm start
```

Ouvrir `http://localhost:4200/`. L’application lit les JSON présents dans `app/src/assets/data/`.

Pour compiler :

```bash
cd eclaireur
npm run build
```

## Pipeline de données

Prérequis : Python 3 et les dépendances listées dans `requirements.txt`.

Les principales étapes sont :

1. Source classeur : `data/raw/dataChallenge.xlsx`.
2. Ingestion, normalisation et audit : `data/ingestion.py`, `data/regions.py`, `data/audit.py` et `data/runAudit.py`.
3. Tables traitées : `data/processed/`.
4. Indice et analyses de robustesse : `data/statistique/`.
5. Exports consommés par l’application : `app/src/assets/data/` ; documentation et diagnostics : `docs/`.

La configuration centralisée se trouve dans `data/config.yaml`. Les données JSON peuvent être régénérées avec les scripts du répertoire `data/` ; consulter leurs options et `data/build_dashboard_json.py` avant exécution.

## Structure

- `data/raw/` : source brute utilisée par le pipeline.
- `data/processed/` : tables nettoyées et harmonisées.
- `data/statistique/` : calcul de l’indice et robustesse.
- `app/src/assets/data/` : données JSON utilisées par le tableau de bord.
- `docs/` : audit, dictionnaire des indicateurs, journal de traitement et diagnostics.
- `eclaireur/` : application Angular.

## Limites et validation

L’analyse porte sur 13 régions et dépend des indicateurs disponibles. La robustesse du classement aux hypothèses de calcul ne vaut pas validation prédictive. Une confrontation avec des observations indépendantes ou des retours terrain est nécessaire avant tout usage comme mesure du décrochage.

Voir [`docs/diagnostics_indice.md`](docs/diagnostics_indice.md) et [`docs/dictionnaire_indicateurs.md`](docs/dictionnaire_indicateurs.md).
