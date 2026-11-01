# Revue du dépôt — 0.2.1

Passe du 1er novembre 2026, après confirmation utilisateur du fonctionnement de la b15. La 0.2.1 consolide ce socle d'observation ; ce rapport ne certifie ni chaque matériel, ni le futur pilotage, ni une validation officielle HACS.

## Périmètre relu

| Ensemble | Points examinés et décision |
| --- | --- |
| Entrée HA et capteurs | Setup/unload, écoute des états, options prioritaires, identifiants conservés ; aucune modification du schéma b15 |
| Mesures et bilan | W/kW, Wh/kWh, stock/SOC, signes, absence de zéro artificiel, réseau signé ou séparé, cumulus inclus, contraintes AC |
| Assistant et réglages | Validation des sources, rejet des boucles EMS, droits administrateur, révision contre les écrasements concurrents, confirmation finale |
| Dashboard et frontend | Tendance unique, icônes produit, historique 24 h, calcul quotidien depuis cumul, météo facultative, jour/nuit et lecture seule |
| Simulation | Budget explicite borné, priorités, absence de double allocation, journal borné à 20 scénarios, aucune commande physique |
| Distribution | Manifest/HACS, ressources locales, versions backend/frontend, archive déterministe et SHA-256, publication ordinaire 0.2.1 |
| Documentation et wiki | Suppression du parcours autonome, réécriture des guides périmés, illustrations affichées, captures et liens locaux vérifiés |

## Corrections de consolidation

Le README, l'installation, l'assistant, le modèle Conso Maison, les usages, le panneau et la feuille de route décrivent désormais les fonctions effectivement livrées. Les textes qui présentaient encore le dépôt comme un prototype sans dashboard, imposaient deux capteurs réseau ou annonçaient le bouton de copie ont été corrigés. Les anciens guides système et déploiement séparé ont été supprimés ; les documents V0.1 restants redirigent vers les guides courants.

Les illustrations de jour et nuit sont visibles dans leur page dédiée, le README et le wiki versionné `docs/wiki`. Les captures sont générées depuis le panneau réel avec des données simulées, pas reprises d'une installation privée. Leur reproduction est disponible avec `node scripts/capture_readme.cjs` après installation des dépendances navigateur de la CI.

Le workflow de publication distingue une version ordinaire comme 0.2.1 d'une version `b…` marquée préversion. Aucun changement des clés, identifiants ou formules du socle b15 n'est introduit par cette consolidation.

## Vérifications de release

Les commandes locales de référence sont :

```sh
python -m unittest discover -s tests -q
python -m compileall -q custom_components tests scripts
python scripts/check_documentation.py
node --test tests/test_panel_frontend.mjs
node scripts/validate_panel_browser.cjs
python scripts/build_test_package.py
```

La suite de référence comporte 143 tests Python et 18 tests JavaScript, complétés par les parcours navigateur desktop/mobile. La CI de la release exécute en plus des instances temporaires HA 2026.9.1 et 2026.11.0b0 sous Python 3.14. Le résultat effectif est consultable dans les contrôles du commit/tag de publication ; les captures et tests simulés ne remplacent pas les mesures physiques.

## Limites conservées et explicites

- Bilan automatique limité à un périmètre AC cohérent ; les actifs DC demandent une source maison adaptée.
- History/Recorder et la référence de minuit conditionnent les calculs quotidiens depuis un cumul. Les requêtes de panneau sont bornées à 100 sources ; aucune reconstruction d'une énergie manquante n'est prétendue.
- Autonomie et autoconsommation sont apparentes : l'origine du stock batterie n'est pas tracée.
- Tarif fixe estimatif, hors abonnement et revente ; pas de calcul multi-tarifs avancé.
- Prévision météo HA facultative ; pas de prévision énergétique ni de pilotage matériel.
- Une qualité numérique valide ne prouve pas le bon emplacement physique d'une mesure ; les écarts de synchronisation et âges doivent être examinés.
- Une nouvelle version Python nécessite le redémarrage de HA Core ; les réglages courants se rechargent sans redémarrage global.

[Notes 0.2.1](RELEASE_0_2_1.md) · [Feuille de route](ROADMAP.md) · [Wiki](wiki/Home.md)
