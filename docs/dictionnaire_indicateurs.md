# Dictionnaire des indicateurs

| Indicateur | Définition | Sens du risque | Poids | Source(s) | Avertissement |
|---|---|---|---|---|---|
| `achevement_niveau` | Taux d'achèvement récent (moyenne des dernières années, plafonné à 100) | valeur basse = risque élevé | 0.25 | primaire_achevement_region |  |
| `achevement_tendance` | Écart de l'achèvement récent par rapport à la période d'avant le choc 2022/23 (points) | valeur basse = risque élevé | 0.1 | primaire_achevement_region |  |
| `ecart_genre_achevement` | Écart filles-garçons d'achèvement (valeur absolue) | valeur haute = risque élevé | 0.1 | primaire_achevement_region | Mesure la disparité, pas un désavantage présumé des filles : le sens de l'écart est conservé à part. |
| `choc_ecoles_effectifs` | Perte d'élèves et d'écoles liée au choc 2022/23 (pic et déficit résiduel) | valeur haute = risque élevé | 0.15 | primaire_effectifs_region, primaire_ecoles_region | Signal de perturbation scolaire : une baisse d'effectifs ou d'écoles ne prouve pas à elle seule des abandons. |
| `entrees_cp1` | Évolution des nouveaux inscrits en CP1 par rapport à avant le choc | valeur basse = risque élevé | 0.1 | primaire_nouveaux_cp1_region |  |
| `reussite_cep` | Taux de réussite au CEP récent | valeur basse = risque élevé | 0.1 | primaire_cep_region | Calculé sur les candidats : une forte sortie avant le CEP peut le masquer. À lire avec prudence. |
| `scolarisation_tbs` | Taux brut de scolarisation au primaire (plafonné à 100) | valeur basse = risque élevé | 0.15 | primaire_tbs_region | Un TBS supérieur à 100 reflète aussi des élèves hors âge et des redoublants ; il est plafonné à 100. |
| `presco_acces` | TBS du préscolaire (accès précoce) | valeur basse = risque élevé | 0.05 | prescolaire_T5 | Lien indirect avec le primaire : poids faible. |
