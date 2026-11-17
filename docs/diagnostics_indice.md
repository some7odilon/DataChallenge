# Diagnostics de l'indice

Généré le 2026-11-16 (pipeline 0.2.0). Ces mesures disent si le classement est COHÉRENT et STABLE ; elles ne prouvent ni causalité ni taux de décrochage.

## 1. D'où vient le score

| Tableau source | Part du poids |
|---|---|
| primaire_achevement_region | 45 % |
| primaire_tbs_region | 15 % |
| primaire_cep_region | 10 % |
| primaire_nouveaux_cp1_region | 10 % |
| primaire_effectifs_region | 8 % |
| primaire_ecoles_region | 8 % |
| prescolaire_T5 | 5 % |

Source la plus pesante : **primaire_achevement_region** (45 %).

## 2. Justification des poids

| Indicateur | Poids | Raison |
|---|---|---|
| achevement_niveau | 25 % | Résultat le plus proche du décrochage disponible : poids le plus élevé. |
| achevement_tendance | 10 % | Mesure la dégradation par rapport à avant le choc ; poids limité pour éviter le double comptage de l'achèvement. |
| ecart_genre_achevement | 10 % | Mesure la disparité filles-garçons ; le sens de l'écart est conservé séparément. |
| reussite_cep | 10 % | Résultat de fin de cycle, calculé sur les candidats : poids modéré. |
| choc_ecoles_effectifs | 15 % | Signal indirect de perturbation scolaire ; ne prouve pas l'abandon. |
| entrees_cp1 | 10 % | Mesure l'évolution des entrées dans le cycle par rapport à l'avant-choc. |
| scolarisation_tbs | 15 % | Mesure l'accès au primaire ; taux plafonné à 100 pour l'indice. |
| presco_acces | 5 % | Accès préscolaire, lien indirect avec le primaire : poids faible. |

## 3. Le classement résiste-t-il aux choix de méthode ?

Normalisation retenue : **robuste** ; niveaux = moyenne des 3 dernières années ; « prioritaire » = top 4.

| Ce qu'on fait varier | Scénarios | Spearman moyen | Spearman min | Même top-k |
|---|---|---|---|---|
| Les poids (tirage aléatoire ±50 %) | 1000 | 0.99 | 0.93 | 100 % |
| La méthode de normalisation | 2 | 0.99 | 0.98 | 100 % |
| Le nombre d'années de référence | 2 | 0.99 | 0.98 | 100 % |
| Retrait d'un indicateur à la fois | 8 | 0.98 | 0.97 | 100 % |
| **Tout à la fois** | 1620 | 0.96 | 0.80 | 99 % |

Verdict : **stable**. Un Spearman de 1 = classement identique au classement de référence.

## 4. Redondance entre indicateurs

Paires dont la corrélation dépasse 0.8 (double comptage possible) :

- `achevement_niveau` et `achevement_tendance` : ρ = 0.89
- `achevement_niveau` et `choc_ecoles_effectifs` : ρ = 0.81
- `achevement_niveau` et `scolarisation_tbs` : ρ = 0.93
- `achevement_tendance` et `choc_ecoles_effectifs` : ρ = 0.8
- `ecart_genre_achevement` et `scolarisation_tbs` : ρ = -0.81
- `choc_ecoles_effectifs` et `scolarisation_tbs` : ρ = 0.85

## 5. Validation

**Cohérence convergente** (les résultats scolaires vont-ils avec les facteurs d'accès et de perturbation ?)

- Association forte entre les résultats (achèvement et CEP) et les facteurs d'accès/perturbation (Spearman 0.92, 13 régions). Une association n'est pas une cause. p (permutation) = 0.0002.

**Confrontation au terrain**

- Non réalisée : aucune région attendue renseignée dans config.yaml (validation.regions_attendues_vulnerables). **À renseigner pour une validation externe.**

## 6. Stabilité dans le temps

| Transition | Spearman |
|---|---|
| 2022/23 -> 2023/24 | 1.0 |
| 2023/24 -> 2024/25 | 0.98 |

Aucune région ne change brutalement de rang.

## 7. Limites

- Unité d'analyse : 13 régions ; le classement est relatif et dépend des régions comparées.
- Facteurs associés, pas causes : aucune causalité n'est établie.
- Insécurité, pauvreté, enseignants et distances ne sont pas dans les données : le choc de 2022/23 (écoles, effectifs) sert de signal de perturbation indirect.
- Les taux bruts sont plafonnés à 100 ; le taux de réussite au CEP est calculé sur les candidats et peut masquer des sorties avant l'examen.
- Les données agrégées ne suivent pas les mêmes élèves : le score ne mesure pas des abandons.
- Les valeurs manquantes ne sont pas imputées ; les poids sont renormalisés. La confiance affichée décrit la couverture des données, pas une confiance statistique.
