# Journal de traitement

Généré automatiquement par `data/runAudit.py`. Les valeurs conflictuelles à vérifier sont consignées séparément dans `docs/doublons_a_arbitrer.csv`.

## primaire_effectifs_region

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 420 lignes lues ; clés : region_brut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | coherence | National = somme des régions |  |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 1/13 séries, rupture localisée | 1 |
| INFO | sortie | 390 lignes propres exportées (sur 420) |  |

## primaire_effectifs_statut

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 90 lignes lues ; clés : statut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | sortie | 90 lignes propres exportées (sur 90) |  |

## primaire_effectifs_milieu

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 90 lignes lues ; clés : milieu, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | sortie | 90 lignes propres exportées (sur 90) |  |

## primaire_effectifs_niveau

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 450 lignes lues ; clés : statut, niveau, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | sortie | 450 lignes propres exportées (sur 450) |  |

## primaire_nouveaux_cp1_region

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 420 lignes lues ; clés : region_brut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | coherence | National = somme des régions |  |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 4/13 séries, rupture localisée | 4 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 1/13 séries, rupture localisée | 1 |
| INFO | sortie | 390 lignes propres exportées (sur 420) |  |

## primaire_tba_region

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 450 lignes lues ; clés : region_brut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| ALERTE | regions | Libellés non reconnus, lignes écartées : [libellé long masqué] | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2021/2022 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 4/13 séries, rupture localisée | 4 |
| INFO | sortie | 390 lignes propres exportées (sur 450) |  |

## primaire_tbs_region

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 420 lignes lues ; clés : region_brut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2021/2022 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 1/13 séries, rupture localisée | 1 |
| INFO | sortie | 390 lignes propres exportées (sur 420) |  |

## primaire_achevement_region

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 420 lignes lues ; clés : region_brut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| ALERTE | valeurs | Valeurs au-dessus de 100 (non modifiées) | 2 |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2020/2021 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 3/13 séries, rupture localisée | 3 |
| INFO | sortie | 390 lignes propres exportées (sur 420) |  |

## primaire_cep_region

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 420 lignes lues ; clés : region_brut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | « HAUT-BASSINS » rapproché de HAUTS-BASSINS (alias, score 1.0) : à valider |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2019/2020 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 1/13 séries, rupture localisée | 1 |
| INFO | sortie | 390 lignes propres exportées (sur 420) |  |

## primaire_ips_tba

| Niveau | Étape | Message | N |
|---|---|---|---|
| ALERTE | structure | Tableau vide ou illisible : ignoré |  |

## primaire_ips_tbs

| Niveau | Étape | Message | N |
|---|---|---|---|
| ALERTE | structure | Tableau vide ou illisible : ignoré |  |

## primaire_ips_tap

| Niveau | Étape | Message | N |
|---|---|---|---|
| ALERTE | structure | Tableau vide ou illisible : ignoré |  |

## primaire_ecoles_region

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 420 lignes lues ; clés : region_brut, statut ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | « HAUT-BASSINS » rapproché de HAUTS-BASSINS (alias, score 1.0) : à valider |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | coherence | National = somme des régions |  |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 4/39 séries, rupture localisée | 4 |
| ALERTE | ruptures | Variation > 30 % en 2019/2020 : 2/39 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2020/2021 : 4/39 séries, rupture localisée | 4 |
| ALERTE | ruptures | Variation > 30 % en 2021/2022 : 5/39 séries, rupture localisée | 5 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 10/39 séries, rupture localisée | 10 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 3/39 séries, rupture localisée | 3 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 1/39 séries, rupture localisée | 1 |
| INFO | sortie | 390 lignes propres exportées (sur 420) |  |

## prescolaire_T1

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 420 lignes lues ; clés : region_brut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | coherence | Garçons + filles = total partout |  |
| INFO | coherence | National = somme des régions |  |
| ALERTE | ruptures | Variation > 30 % en 2016/2017 : 4/13 séries, rupture localisée | 4 |
| ALERTE | ruptures | Variation > 30 % en 2017/2018 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 4/13 séries, rupture localisée | 4 |
| ALERTE | ruptures | Variation > 30 % en 2019/2020 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2020/2021 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 7/13 séries, rupture systémique (choc général ou changement de méthode) | 7 |
| INFO | sortie | 390 lignes propres exportées (sur 420) |  |

## prescolaire_T2

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 120 lignes lues ; clés : statut, sexe ; 10 années (2015/2016 à 2024/2025) |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | coherence | Garçons + filles = total partout |  |
| ALERTE | ruptures | Variation > 30 % en 2016/2017 : 2/4 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 1/4 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 1/4 séries, rupture localisée | 1 |
| INFO | sortie | 120 lignes propres exportées (sur 120) |  |

## prescolaire_T3

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 96 lignes lues ; clés : milieu, sexe ; 8 années (2017/2018 à 2024/2025) |  |
| INFO | doublons | Aucun doublon |  |
| ALERTE | manquants | Valeurs manquantes conservées (pas d'imputation) | 15 |
| INFO | coherence | Garçons + filles = total partout |  |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 1/4 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 1/4 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 1/4 séries, rupture localisée | 1 |
| INFO | sortie | 96 lignes propres exportées (sur 96) |  |

## prescolaire_T4

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 210 lignes lues ; clés : statut, sexe ; 9 années (2015/2016 à 2024/2025) |  |
| ALERTE | doublons | Valeurs contradictoires exclues en attente d'arbitrage ; détails dans doublons_a_arbitrer.csv | 42 |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | coherence | Garçons + filles = total partout |  |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 2/7 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 2/7 séries, rupture localisée | 2 |
| INFO | sortie | 168 lignes propres exportées (sur 210) |  |

## prescolaire_T5

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 420 lignes lues ; clés : region_brut, sexe ; 9 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 30 |
| INFO | regions | 13/13 régions trouvées |  |
| ALERTE | doublons | Valeurs contradictoires exclues en attente d'arbitrage ; détails dans doublons_a_arbitrer.csv | 78 |
| INFO | manquants | Aucune valeur manquante |  |
| ALERTE | ruptures | Variation > 30 % en 2016/2017 : 4/13 séries, rupture localisée | 4 |
| ALERTE | ruptures | Variation > 30 % en 2017/2018 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2020/2021 : 10/13 séries, rupture systémique (choc général ou changement de méthode) | 10 |
| ALERTE | ruptures | Variation > 30 % en 2021/2022 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 2/13 séries, rupture localisée | 2 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 1/13 séries, rupture localisée | 1 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 7/13 séries, rupture systémique (choc général ou changement de méthode) | 7 |
| INFO | sortie | 312 lignes propres exportées (sur 420) |  |

## prescolaire_T6

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 140 lignes lues ; clés : region_brut ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 10 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| INFO | sortie | 130 lignes propres exportées (sur 140) |  |

## prescolaire_T7

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 530 lignes lues ; clés : region_brut, statut ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 10 |
| INFO | regions | Totaux régionaux mis de côté (ils ne sont pas des régions supplémentaires) | 130 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| ALERTE | ruptures | Variation > 30 % en 2016/2017 : 30/39 séries, rupture systémique (choc général ou changement de méthode) | 30 |
| ALERTE | ruptures | Variation > 30 % en 2017/2018 : 16/39 séries, rupture localisée | 16 |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 14/39 séries, rupture localisée | 14 |
| ALERTE | ruptures | Variation > 30 % en 2019/2020 : 21/39 séries, rupture systémique (choc général ou changement de méthode) | 21 |
| ALERTE | ruptures | Variation > 30 % en 2020/2021 : 19/39 séries, rupture localisée | 19 |
| ALERTE | ruptures | Variation > 30 % en 2021/2022 : 9/39 séries, rupture localisée | 9 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 9/39 séries, rupture localisée | 9 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 13/39 séries, rupture localisée | 13 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 20/39 séries, rupture systémique (choc général ou changement de méthode) | 20 |
| INFO | sortie | 390 lignes propres exportées (sur 530) |  |

## prescolaire_T8

| Niveau | Étape | Message | N |
|---|---|---|---|
| INFO | structure | 530 lignes lues ; clés : region_brut, statut ; 10 années (2015/2016 à 2024/2025) |  |
| CORRECTION | regions | Lignes d'agrégat (national/total) mises de côté pour contrôle | 10 |
| INFO | regions | Totaux régionaux mis de côté (ils ne sont pas des régions supplémentaires) | 130 |
| INFO | regions | 13/13 régions trouvées |  |
| INFO | doublons | Aucun doublon |  |
| INFO | manquants | Aucune valeur manquante |  |
| ALERTE | ruptures | Variation > 30 % en 2016/2017 : 24/39 séries, rupture systémique (choc général ou changement de méthode) | 24 |
| ALERTE | ruptures | Variation > 30 % en 2017/2018 : 19/39 séries, rupture localisée | 19 |
| ALERTE | ruptures | Variation > 30 % en 2018/2019 : 16/39 séries, rupture localisée | 16 |
| ALERTE | ruptures | Variation > 30 % en 2019/2020 : 13/39 séries, rupture localisée | 13 |
| ALERTE | ruptures | Variation > 30 % en 2020/2021 : 11/39 séries, rupture localisée | 11 |
| ALERTE | ruptures | Variation > 30 % en 2021/2022 : 10/39 séries, rupture localisée | 10 |
| ALERTE | ruptures | Variation > 30 % en 2022/2023 : 10/39 séries, rupture localisée | 10 |
| ALERTE | ruptures | Variation > 30 % en 2023/2024 : 16/39 séries, rupture localisée | 16 |
| ALERTE | ruptures | Variation > 30 % en 2024/2025 : 16/39 séries, rupture localisée | 16 |
| INFO | sortie | 390 lignes propres exportées (sur 530) |  |
