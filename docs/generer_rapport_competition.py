"""Génère le rapport Éclaireur en HTML, PDF et DOCX à partir des exports JSON."""
from __future__ import annotations

import base64
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = ROOT / "app" / "src" / "assets" / "data"
OUT = DOCS / "rapport_competition"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


scores = load("indice.json")
profiles = {p["code"]: p for p in load("profils.json")}
meta = load("metadata.json")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
fig, ax = plt.subplots(figsize=(8.5, 5.1))
fig.patch.set_facecolor("#f8f7f3")
ax.set_facecolor("#f8f7f3")
ordered = list(reversed(scores))
labels = [r["region"].title() for r in ordered]
values = [r["score"] for r in ordered]
colors = ["#c85a17" if r["rang"] <= 4 else "#6f89a8" if r["rang"] <= 8 else "#c3cbd4" for r in ordered]
bars = ax.barh(labels, values, color=colors, height=.66)
ax.set_xlim(0, 100)
ax.set_xlabel("Score relatif de vulnérabilité (0–100) · pas un pourcentage de décrochage", color="#334155", labelpad=11)
ax.set_title("Classement régional — données 2024/25", color="#0f172a", fontsize=15, weight="bold", loc="left", pad=15)
ax.grid(axis="x", color="#d9dee5", linewidth=.8)
ax.set_axisbelow(True)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color("#aab4c1")
ax.tick_params(axis="y", length=0, colors="#26354b", labelsize=9)
ax.tick_params(axis="x", colors="#526174")
for bar, value in zip(bars, values):
    ax.text(value + 1, bar.get_y() + bar.get_height()/2, f"{value:.1f}".replace(".", ","), va="center", color="#26354b", fontsize=9, weight="bold")
fig.tight_layout(pad=1.8)
chart = DOCS / "classement_regions.png"
fig.savefig(chart, dpi=190, facecolor=fig.get_facecolor(), bbox_inches="tight")
plt.close(fig)
chart_data = base64.b64encode(chart.read_bytes()).decode("ascii")

score_rows = "".join(
    f"<tr class='{ 'top' if r['rang'] <= 4 else '' }'><td>{int(r['rang'])}</td><td>{r['region'].title()}</td><td>{r['score']:.1f}</td><td>{r['niveau'].title()}</td><td>{r['rang_p5']:.0f}–{r['rang_p95']:.0f}</td></tr>".replace(f"{r['score']:.1f}", f"{r['score']:.1f}".replace(".", ","))
    for r in scores
)

weight_labels = {
    "achevement_niveau": "Achèvement récent du primaire",
    "achevement_tendance": "Évolution de l’achèvement depuis l’avant-choc",
    "ecart_genre_achevement": "Écart filles-garçons d’achèvement",
    "reussite_cep": "Réussite au CEP",
    "choc_ecoles_effectifs": "Perturbation des écoles et des effectifs",
    "entrees_cp1": "Évolution des entrées au CP1",
    "scolarisation_tbs": "Scolarisation brute au primaire",
    "presco_acces": "Accès au préscolaire",
}
weight_rows = "".join(
    f"<tr><td>{weight_labels.get(k,k)}</td><td>{v*100:.0f} %</td></tr>"
    for k, v in meta["ponderations"].items()
)

region_cards = "".join(
    f"<article class='region-card'><div class='region-head'><span class='rank'>0{int(r['rang'])}</span><div><h3>{r['region'].title()}</h3><span>Score relatif : <b>{r['score']:.1f}/100</b> · rang {int(r['rang'])}/13</span></div></div><p><b>Profil dominant :</b> {profiles[r['code']]['profil']}. {profiles[r['code']]['recommandation']}</p><p class='tiny'>Fourni comme piste de discussion : à confirmer avec les équipes et les données locales avant toute décision.</p></article>".replace(f"{r['score']:.1f}", f"{r['score']:.1f}".replace(".", ","))
    for r in scores[:4]
)

rob_rows = "".join(
    f"<tr><td>{label}</td><td>{v['n_scenarios']:,}</td><td>{v['spearman_moyen']:.3f}</td><td>{v['spearman_min']:.3f}</td><td>{v['top_k_identique']*100:.1f} %</td></tr>".replace(f"{v['n_scenarios']:,}", f"{v['n_scenarios']:,}".replace(",", " ")).replace(f"{v['spearman_moyen']:.3f}", f"{v['spearman_moyen']:.3f}".replace(".", ",")).replace(f"{v['spearman_min']:.3f}", f"{v['spearman_min']:.3f}".replace(".", ",")).replace(f"{v['top_k_identique']*100:.1f}", f"{v['top_k_identique']*100:.1f}".replace(".", ","))
    for label, v in [
        ("Poids modifiés aléatoirement (±50 %)", meta["robustesse"]["poids"]),
        ("Méthode de normalisation", meta["robustesse"]["normalisation"]),
        ("Nombre d’années moyennées", meta["robustesse"]["annees"]),
        ("Retrait d’un indicateur à la fois", meta["robustesse"]["retrait"]),
        ("Variations combinées", meta["robustesse"]["combine"]),
    ]
)

html = r'''<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>Éclaireur — Rapport de compétition</title>
<style>
@page { size:A4; margin:15mm 17mm 15mm 17mm; }
* { box-sizing:border-box; }
body { margin:0; color:#172235; font:10pt/1.42 Arial, Helvetica, sans-serif; background:white; }
.page { position:relative; page-break-after:always; break-after:page; min-height:250mm; padding-bottom:13mm; }
.page:last-child { page-break-after:auto; break-after:auto; }
.cover { margin:-15mm -17mm; padding:25mm 20mm 18mm; min-height:297mm; color:#f5f4ee; background:#0f172a; }
.cover::before { content:""; display:block; width:24mm; height:3mm; margin-bottom:22mm; background:#c85a17; border-radius:3mm; }
.brand { color:#e8a06f; font-size:11pt; font-weight:bold; letter-spacing:2px; text-transform:uppercase; }
h1 { margin:10mm 0 5mm; max-width:165mm; font-size:35pt; line-height:1.08; color:inherit; }
.cover h2 { margin:0; max-width:150mm; color:#d5deea; font-size:18pt; font-weight:normal; line-height:1.3; }
.cover .lead { margin-top:28mm; padding:9mm; max-width:158mm; background:#1b2941; border:1px solid #34435c; border-radius:4mm; font-size:13pt; line-height:1.5; }
.cover .lead strong { color:#ffb181; }
.cover .meta { margin-top:22mm; color:#c6d0dd; font-size:10pt; line-height:1.8; }
.cover .disclaimer { margin-top:24mm; padding-top:7mm; border-top:1px solid #46546a; color:#c6d0dd; font-size:9.5pt; }
h2 { margin:0 0 5mm; color:#1e3a5f; font-size:21pt; line-height:1.18; }
h3 { margin:5mm 0 2mm; color:#1e3a5f; font-size:12pt; }
p { margin:0 0 3.3mm; }
.kicker { margin-bottom:2mm; color:#c85a17; font-size:8pt; font-weight:bold; letter-spacing:1.25px; text-transform:uppercase; }
.dek { margin:0 0 6mm; color:#526174; font-size:11pt; line-height:1.45; }
.callout { margin:4mm 0; padding:4mm 5mm; border-left:3px solid #c85a17; border-radius:2mm; background:#f6f1e8; }
.callout.blue { border-left-color:#1e3a5f; background:#eef2f7; }
.callout strong { color:#1e3a5f; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:4mm; }
.card { padding:4mm; border:1px solid #d7dde4; border-radius:3mm; background:#fbfbfa; }
.card h3 { margin:0 0 2mm; }
.card p:last-child { margin-bottom:0; }
.steps { margin:3mm 0; padding:0; list-style:none; }
.steps li { position:relative; margin:0 0 3mm; padding:3mm 4mm 3mm 13mm; border-radius:2mm; background:#f2f4f7; }
.steps li::before { content:attr(data-n); position:absolute; left:4mm; color:#c85a17; font-weight:bold; }
table { width:100%; margin:3mm 0 4mm; border-collapse:collapse; font-size:8.5pt; }
th { padding:2.4mm 2.5mm; color:white; background:#1e3a5f; text-align:left; }
td { padding:2.1mm 2.5mm; border-bottom:1px solid #dce1e7; vertical-align:top; }
tr:nth-child(even) td { background:#f6f7f8; }
tr.top td { background:#fff1e7; }
.small { color:#556477; font-size:8.5pt; }
.tiny { color:#5b6777; font-size:8pt; }
.chart { display:block; width:100%; max-height:104mm; object-fit:contain; margin:1mm auto 2mm; }
.region-card { margin:0 0 3mm; padding:3.5mm 4mm; border:1px solid #d7dde4; border-radius:3mm; background:#fbfbfa; }
.region-head { display:flex; align-items:center; gap:3mm; }
.rank { display:grid; width:9mm; height:9mm; place-items:center; border-radius:50%; color:white; background:#c85a17; font-size:10pt; font-weight:bold; }
.region-head h3 { display:inline; margin:0 3mm 0 0; }
.region-head span { font-size:8.5pt; color:#475569; }
.region-card p { margin:2mm 0 0; font-size:9pt; }
.region-card .tiny { margin-top:1mm; }
.footer { position:absolute; right:0; bottom:0; left:0; padding-top:2.2mm; border-top:1px solid #dce1e7; color:#667386; font-size:8pt; }
.footer span { float:right; }
.pill { display:inline-block; margin:1mm 1mm 0 0; padding:1.4mm 2.5mm; border-radius:8mm; color:#1e3a5f; background:#eaf0f6; font-size:8.5pt; font-weight:bold; }
.equation { margin:4mm 0; padding:4mm; border-radius:2mm; color:#f5f4ee; background:#172235; font-size:12pt; text-align:center; }
.bar { height:5mm; margin:1mm 0 3mm; overflow:hidden; border-radius:4mm; background:#e5e9ee; }
.bar i { display:block; height:100%; background:#c85a17; }
ul { margin:2mm 0 3mm; padding-left:6mm; }
li { margin:0 0 1.5mm; }
.glossary td:first-child { width:33%; color:#1e3a5f; font-weight:bold; }
a { color:#1e3a5f; }
</style></head><body>
<section class="page cover">
  <div class="brand">Éclaireur · Burkina Faso</div>
  <h1>Repérer les signaux de vulnérabilité scolaire</h1>
  <h2>Outil d’aide à la décision pour cibler la prévention du décrochage, région par région</h2>
  <div class="lead"><strong>Réponse en bref.</strong> Dans les données de référence 2024/25, les signaux les plus élevés apparaissent dans la Boucle du Mouhoun, l’Est, le Sahel et le Centre-Nord.</div>
  <div class="meta"><b>Rapport de candidature au défi</b><br>Territoire : 13 régions du Burkina Faso<br>Période analysée : 2015/16–2024/25<br>Données et pipeline : version 0.2.0 · export du 16 novembre 2026</div>
  <div class="disclaimer"><b>À lire avant tout :</b> Éclaireur classe des signaux régionaux indirects. Le score n’est ni le taux de décrochage, ni la probabilité qu’un élève quitte l’école.</div>
</section>

<section class="page">
  <div class="kicker">1 · Le défi</div><h2>Passer d’un grand tableau à une priorité compréhensible</h2>
  <p class="dek">Les statistiques scolaires décrivent plusieurs réalités à la fois. Les décideurs ont besoin d’une lecture simple pour repérer les territoires à examiner en premier, sans confondre un signal avec une preuve.</p>
  <h3>La question du défi</h3><div class="callout"><strong>« Où le risque de décrochage est-il le plus fort, par région, et comment l’anticiper ? »</strong></div>
  <p>Le classeur fournit des données agrégées par région et par année scolaire : achèvement du primaire, réussite au CEP, inscriptions, effectifs, écoles et accès préscolaire. Il ne contient pas d’historique nominatif des élèves ni de décompte direct des abandons.</p>
  <h3>Notre réponse et son périmètre</h3>
  <div class="grid2"><article class="card"><h3>Ce que nous faisons</h3><p>Nous assemblons plusieurs indicateurs, donnons plus de poids aux résultats proches de la fin du cycle, calculons un score relatif et rendons visibles les facteurs dominants par région.</p></article><article class="card"><h3>Ce que nous ne prétendons pas faire</h3><p>Nous ne prédisons pas le parcours d’un élève, ne calculons pas un taux d’abandon et n’identifions pas la cause d’une difficulté régionale.</p></article></div>
  <h3>À qui l’outil sert-il ?</h3><p>Aux équipes de planification, responsables éducatifs et partenaires qui doivent comparer les régions, décider où approfondir le diagnostic et suivre les signaux au fil des mises à jour.</p>
  <div class="callout blue"><strong>Principe de prudence :</strong> un rang élevé doit déclencher une vérification locale et un dialogue avec les acteurs éducatifs, pas une décision automatique de sanction ou de financement.</div>
  <div class="footer">Éclaireur · Rapport de compétition <span>02 / 10</span></div>
</section>

<section class="page">
  <div class="kicker">2 · Les données</div><h2>Des statistiques scolaires couvrant dix années</h2>
  <p class="dek">Le classeur de travail rassemble des tableaux du primaire et du préscolaire. L’analyse compare les 13 régions administratives.</p>
  <table><thead><tr><th>Élément</th><th>Contenu utilisé</th><th>À quoi cela sert</th></tr></thead><tbody>
    <tr><td>Période</td><td>2015/16 à 2024/25 (selon disponibilité des séries)</td><td>Lire le niveau récent et le comparer à l’avant-choc 2022/23.</td></tr>
    <tr><td>Échelle</td><td>13 régions ; données agrégées</td><td>Comparer des territoires, pas suivre des personnes.</td></tr>
    <tr><td>Résultats</td><td>Achèvement du primaire, réussite au CEP</td><td>Repérer des difficultés de progression et de fin de cycle.</td></tr>
    <tr><td>Accès et perturbations</td><td>Entrées au CP1, scolarisation, effectifs, écoles, préscolaire</td><td>Ajouter des signaux d’accès et de continuité de l’offre.</td></tr>
    <tr><td>Ventilation</td><td>Filles, garçons et total dans les tableaux où ces colonnes existent</td><td>Repérer des écarts entre filles et garçons lorsque la donnée le permet.</td></tr>
  </tbody></table>
  <h3>Pourquoi prendre 2022/23 comme année repère ?</h3>
  <p>Ce repère est fixé manuellement dans la configuration du modèle : il n’a pas été détecté automatiquement comme le début exact d’une crise. Il sert à comparer une situation « avant » à des indicateurs récents. Ce choix correspond à une forte période de perturbation scolaire : l’UNICEF rapportait 6 134 écoles fermées en février 2023, soit 44 % de plus qu’en mai 2022. Mais la crise avait commencé plus tôt : au Sahel dès 2019, et les fermetures ont fortement augmenté dans l’Est et la Boucle du Mouhoun à partir de 2021/22 (<a href="https://www.unicef.org/burkinafaso/communiques-de-presse/le-burkina-faso-abrite-pres-de-la-moitie-des-ecoles-fermees">UNICEF, 2023</a> ; <a href="https://www.unicef.org/innocenti/media/10456/file/UNICEF-Innocenti-DMS-Burkina-Faso-Brief-2-FR-2025.pdf">UNICEF Innocenti, 2025</a>).</p>
  <table><thead><tr><th>Avant le repère</th><th>Année repère</th><th>Moyenne récente</th></tr></thead><tbody><tr><td>2015/16 à 2021/22, selon les années disponibles pour chaque indicateur</td><td>2022/23 ; comparée à 2021/22 pour les écoles et les effectifs</td><td>2022/23 à 2024/25 ; cette moyenne inclut donc l’année repère</td></tr></tbody></table>
  <p class="small">Ainsi, « choc 2022/23 » désigne ici un point de comparaison du modèle, pas un événement unique ni la date de début de la crise. L’audit signale des variations importantes à plusieurs dates ; il ne choisit pas l’année repère. Les résultats n’ont pas encore été comparés à d’autres dates de référence.</p>
  <h3>Source et prudence</h3><p>Source de travail : classeur fourni pour le défi, `data/raw/dataChallenge.xlsx` ; feuilles Feuil1 à Feuil13 et feuille PRESCOLAIRE. Les exports traités et JSON sont inclus dans le dépôt GitHub.</p>
  <p>La couverture n’est pas identique pour chaque tableau ou année. Certains indicateurs ont des valeurs manquantes ou des ruptures. Le score repose donc sur les données disponibles et affiche une couverture de poids.</p>
  <div class="grid2"><article class="card"><h3>Avantage</h3><p>Plusieurs familles de données sont rapprochées dans une même lecture régionale et documentée.</p></article><article class="card"><h3>Limite</h3><p>Une valeur régionale moyenne peut cacher des écarts importants entre provinces, communes, écoles ou groupes d’élèves.</p></article></div>
  <div class="footer">Éclaireur · Rapport de compétition <span>03 / 10</span></div>
</section>

<section class="page">
  <div class="kicker">3 · La préparation</div><h2>Contrôler avant de calculer</h2>
  <p class="dek">Le pipeline transforme le classeur en tables cohérentes, puis garde une trace des corrections et des anomalies.</p>
  <ol class="steps"><li data-n="1."><b>Lire les tableaux</b> : repérer les feuilles, les années, les régions, les catégories filles/garçons/total et les valeurs.</li><li data-n="2."><b>Uniformiser</b> : harmoniser les libellés des régions et le format des années scolaires ; convertir les nombres et les valeurs manquantes.</li><li data-n="3."><b>Écarter les agrégats qui fausseraient la comparaison</b> : les lignes « national » ou « total » ne sont pas comptées comme des régions.</li><li data-n="4."><b>Contrôler les doublons et la cohérence</b> : supprimer les répétitions exactes ; placer les conflits non résolus dans un registre à arbitrer.</li><li data-n="5."><b>Signaler les ruptures</b> : les variations annuelles supérieures à 30 % sont marquées pour examen, sans conclure automatiquement à une erreur.</li></ol>
  <h3>Règles appliquées au calcul</h3><ul><li>Les valeurs manquantes ne sont pas inventées : le poids des seuls indicateurs disponibles est recalculé.</li><li>Les taux d’achèvement, de scolarisation brute et de réussite au CEP sont plafonnés à 100 avant calcul, pour éviter qu’une valeur supérieure à 100 soit interprétée comme une meilleure protection.</li><li>Les lignes avec des valeurs contradictoires sont exclues en attente d’un arbitrage dans le classeur source.</li></ul>
  <div class="callout"><strong>Anomalies documentées :</strong> le journal recense 42 lignes contradictoires dans le tableau préscolaire T4 et 78 dans T5. Ces valeurs ne sont pas choisies arbitrairement ; elles sont conservées dans `docs/doublons_a_arbitrer.csv` pour vérification.</div>
  <p>Le rapport d’audit est conservé dans `docs/rapport_audit.json` et son résumé lisible dans `docs/journal_traitement.md`. Cela permet de comprendre d’où vient une table propre et pourquoi certaines lignes en ont été écartées.</p>
  <div class="footer">Éclaireur · Rapport de compétition <span>04 / 10</span></div>
</section>

<section class="page">
  <div class="kicker">4 · La méthode</div><h2>Construire un signal régional lisible</h2>
  <p class="dek">Chaque indicateur est d’abord orienté dans le même sens : 100 signifie une valeur plus préoccupante parmi les régions comparées, 0 une valeur moins préoccupante.</p>
  <div class="grid2"><article class="card"><h3>1 · Résumer</h3><p>Les niveaux récents utilisent la moyenne des trois dernières années disponibles. La tendance d’achèvement compare le niveau récent avec la période avant le choc 2022/23.</p></article><article class="card"><h3>2 · Mettre sur une échelle commune</h3><p>La normalisation robuste borne les valeurs extrêmes aux 10e et 90e centiles, puis ramène les résultats sur une échelle de 0 à 100.</p></article></div>
  <div class="equation">Score régional = moyenne des signaux × leurs poids</div>
  <p>Si une donnée manque, elle ne compte pas dans cette région et les autres poids sont ajustés. Le score reste donc comparable à l’intérieur de cette méthode, mais dépend des régions et des données disponibles.</p>
  <h3>Les huit composantes et leurs poids</h3>
  <table><thead><tr><th>Indicateur en mots simples</th><th>Poids</th></tr></thead><tbody>''' + weight_rows + r'''</tbody></table>
  <p class="small">Les poids totalisent 100 %. Les niveaux faibles d’achèvement, de réussite, d’accès ou d’entrées au CP1 augmentent le signal ; une forte perturbation des écoles/effectifs et un écart filles-garçons plus important l’augmentent également.</p>
  <div class="callout blue"><strong>Exemple de lecture :</strong> un score de 80 indique une position élevée sur l’échelle relative de vulnérabilité de ces 13 régions. Cela ne veut pas dire que 80 % des élèves décrochent.</div>
  <div class="footer">Éclaireur · Rapport de compétition <span>05 / 10</span></div>
</section>

<section class="page">
  <div class="kicker">4 · La méthode · contrôle</div><h2>Vérifier si le classement tient</h2>
  <p class="dek">Un classement peut changer si l’on modifie les poids ou les choix de calcul. Nous avons répété l’analyse sous plusieurs hypothèses.</p>
  <table><thead><tr><th>Variation testée</th><th>Scénarios</th><th>Rang moyen proche<br>(corrélation)</th><th>Top 4 identique</th></tr></thead><tbody>''' + rob_rows + r'''</tbody></table>
  <p>Une corrélation de rang de 1 signifie que les régions gardent exactement le même ordre ; proche de 1 signifie que l’ordre reste voisin. Dans les variations combinées, le rang moyen reste fortement associé au classement de référence (0,961) et le même groupe de quatre ressort dans 99,3 % des scénarios.</p>
  <h3>Ce que ce contrôle nous apprend</h3><p>Le groupe de régions à examiner en premier résiste généralement aux changements testés. Certaines régions du milieu de classement bougent davantage ; il faut donc regarder leur intervalle de rang et éviter de traiter les places voisines comme une différence certaine. Dans le tableau des résultats, l’intervalle indique les 5e–95e centiles des rangs observés dans les simulations ; ce n’est pas un intervalle statistique sur le décrochage.</p>
  <p><b>Les deux premières régions sont presque à égalité :</b> la Boucle du Mouhoun et l’Est ne sont séparées que de 0,35 point. Le classement les ordonne, mais cet écart ne justifie pas de conclure que l’une est nettement plus vulnérable que l’autre.</p>
  <h3>Ce qu’il ne prouve pas</h3><div class="callout"><strong>La stabilité n’est pas une preuve de prédiction.</strong> Elle signifie seulement que les choix méthodologiques testés ne bouleversent pas trop l’ordre. La confrontation à des observations de terrain et à des résultats mesurant directement les abandons n’a pas été faite.</div>
  <p>Une vérification interne trouve aussi une association de rang de 0,92 entre les résultats scolaires (achèvement/CEP) et certains signaux d’accès ou de perturbation, sur 13 régions. C’est une cohérence entre indicateurs disponibles, pas une validation prédictive indépendante ni une preuve de cause.</p>
  <p class="small">Période : les rangs successifs de 2022/23 à 2023/24 puis 2023/24 à 2024/25 ont une corrélation de 1,00 et 0,98. Les séries ne suivent pas les mêmes élèves d’une année à l’autre.</p>
  <div class="footer">Éclaireur · Rapport de compétition <span>06 / 10</span></div>
</section>

<section class="page">
  <div class="kicker">5 · Les résultats</div><h2>Où les signaux sont-ils les plus élevés ?</h2>
  <p class="dek">Classement relatif pour l’année de référence 2024/25. Les quatre premières régions forment le groupe « prioritaire » défini avant l’analyse.</p>
  <img class="chart" src="data:image/png;base64,''' + chart_data + r'''" alt="Diagramme horizontal des scores des 13 régions, les quatre premières en orange">
  <table><thead><tr><th>Rang</th><th>Région</th><th>Score /100</th><th>Lecture</th><th>Intervalle de rang testé</th></tr></thead><tbody>''' + score_rows + r'''</tbody></table>
  <div class="footer">Éclaireur · Rapport de compétition <span>07 / 10</span></div>
</section>

<section class="page">
  <div class="kicker">5 · Les résultats · lecture régionale</div><h2>Des signaux différents appellent des vérifications différentes</h2>
  <p class="dek">Le profil dominant résume la dimension la plus dégradée dans le modèle. Les pistes ci-dessous sont des suggestions générales générées par les profils ; elles doivent être vérifiées localement.</p>
  ''' + region_cards + r'''
  <h3>Lire la « probabilité prioritaire » correctement</h3>
  <p>Dans l’export, la valeur associée à « probabilité prioritaire » est la part des simulations de variation des poids où la région se trouve dans le top 4. Par exemple, 1,00 signifie qu’elle est restée dans le top 4 dans toutes les simulations testées. <b>Ce n’est pas la probabilité qu’un élève décroche.</b></p>
  <div class="callout blue"><strong>À faire ensuite :</strong> pour chaque région du top 4, discuter les facteurs dominants avec les équipes de terrain, vérifier les données récentes et identifier les écoles/communes où une action ciblée est réalisable.</div>
  <div class="footer">Éclaireur · Rapport de compétition <span>08 / 10</span></div>
</section>

<section class="page">
  <div class="kicker">6 · La réponse au défi</div><h2>Un système de repérage et de suivi, pas un verdict</h2>
  <p class="dek">Éclaireur aide à anticiper en rapprochant plusieurs signaux régionaux, en montrant leur évolution et en proposant une liste courte de territoires à examiner.</p>
  <ol class="steps"><li data-n="1."><b>Repérer</b> : consulter le tableau de bord, la carte et le classement pour voir où les signaux se cumulent.</li><li data-n="2."><b>Comprendre</b> : ouvrir la fiche régionale et lire les facteurs qui contribuent au score, la couverture et la plage de rang.</li><li data-n="3."><b>Vérifier</b> : demander une confirmation auprès des services régionaux et des écoles ; compléter avec les informations locales absentes des données.</li><li data-n="4."><b>Agir</b> : envisager une action adaptée au problème observé — maintien scolaire, soutien aux fins de cycle, accès au CP1 ou continuité éducative.</li><li data-n="5."><b>Suivre</b> : mettre à jour les données et regarder si les signaux s’améliorent, en documentant les ruptures de collecte ou de méthode.</li></ol>
  <h3>Exemples de pistes suggérées par les profils</h3>
  <div class="grid2"><article class="card"><h3>Achèvement faible</h3><p>Examiner le maintien jusqu’au CM2, le soutien scolaire et la préparation au CEP.</p></article><article class="card"><h3>Accès fragile</h3><p>Examiner les entrées au CP1, l’accès au préscolaire et la proximité des établissements.</p></article><article class="card"><h3>Perturbation scolaire</h3><p>Vérifier l’ouverture des écoles et les options de continuité éducative.</p></article><article class="card"><h3>Écart filles-garçons</h3><p>Confirmer le groupe en retrait et comprendre les causes locales avant de choisir une mesure.</p></article></div>
  <p class="small">L’outil n’attribue ni budget ni sanction. Il structure la discussion et aide à poser les prochaines questions.</p>
  <div class="footer">Éclaireur · Rapport de compétition <span>09 / 10</span></div>
</section>

<section class="page">
  <div class="kicker">7 · Reproduction</div><h2>Relancer et contrôler la solution</h2>
  <p class="dek">Le code, les fichiers de données utilisés et les consignes sont disponibles dans le dépôt. Une mise à jour doit garder la même configuration et documenter toute modification.</p>
  <h3>Application en ligne</h3><p><b>Démonstration :</b> <a href="https://some7odilon.github.io/DataChallenge/">https://some7odilon.github.io/DataChallenge/</a><br><b>Dépôt :</b> <a href="https://github.com/some7odilon/DataChallenge">github.com/some7odilon/DataChallenge</a></p>
  <h3>Relancer l’analyse des données</h3><p>Prérequis : Python 3 et les dépendances listées dans `requirements.txt`, puis exécuter depuis la racine du dépôt :</p>
  <div class="equation" style="font-size:10pt">python -m venv .venv<br>source .venv/bin/activate<br>pip install -r requirements.txt<br>python data/runAudit.py<br>python data/statistique/runIndice.py</div>
  <p>Le premier script relit le classeur et produit les tables nettoyées et les journaux d’audit. Le second recalcule l’indice, les profils et les JSON utilisés par l’application.</p>
  <h3>Relancer l’application</h3><p>Prérequis : Node.js et npm :</p><div class="equation" style="font-size:10pt">cd eclaireur<br>npm ci<br>npm start</div>
  <p>Ouvrir `http://localhost:4200`. Pour publier une modification, créer un commit et l’envoyer sur `main` ; le workflow GitHub Actions reconstruit le site Pages.</p>
  <h3>Glossaire rapide</h3><table class="glossary"><tbody><tr><td>Score relatif</td><td>Position sur l’échelle créée pour comparer ces régions ; ce n’est pas un taux.</td></tr><tr><td>Top 4</td><td>Groupe prioritaire défini pour orienter la première vérification.</td></tr><tr><td>Corrélation de rang</td><td>Mesure si deux classements gardent un ordre similaire.</td></tr><tr><td>Donnée agrégée</td><td>Total regroupé par région ; ne décrit pas la trajectoire de chaque élève.</td></tr></tbody></table>
  <div class="callout"><strong>Prochaine amélioration prioritaire :</strong> confronter les signaux à des résultats directs de maintien/abandon et aux retours de terrain, puis tester le modèle sur une période ou un jeu de données tenu à part.</div>
  <div class="footer">Éclaireur · Rapport de compétition · pipeline 0.2.0 <span>10 / 10</span></div>
</section>
</body></html>'''

OUT.with_suffix(".html").write_text(html, encoding="utf-8")
print(f"Écrit : {OUT.with_suffix('.html')}")
