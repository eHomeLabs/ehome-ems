# 05 — Appareils, stockage et usages

[Accueil](Home.md) · [Sources](06-Configuration-sources.md)

## Mes Appareils

Ajouter directement depuis l'onglet, puis utiliser Modifier ou Retirer du suivi. L'icône est déduite du nom du produit, avec sélection manuelle MDI disponible. Les noms et identifiants sont conservés lors des modifications.

![Cartes appareils](../screenshots/appliances.png)

Énergie Totale désigne le compteur source. Un cumul permet de calculer l'énergie quotidienne à partir de la référence de minuit ; sans cette référence, le coût du jour reste indisponible. Une énergie de session garde sa période propre.

## Stockage

Le rôle actif AC participe au bilan maison. Le rôle secours et les mesures DC restent suivis séparément. Le SOC ne remplace pas un capteur de stock restant. Un capteur Wh/kWh classé comme cumul n'est accepté comme stock qu'après confirmation explicite de sa nature réelle ; le contrôle de capacité reste appliqué.

![Batteries distinctes](../screenshots/storage.png)

## Cumulus et borne

Les sous-comptages restent inclus dans Conso Maison. Le libellé « Température indisponible » du cumulus concerne uniquement la température de l'eau. La puissance est affichée séparément. L'illustration thermique ne mesure pas une énergie stockée.

[Sources et périodes détaillées](../USAGES_OBSERVATION.md)

## On/Off manuel et objectif

Dans Modifier, choisir l’entité On/Off et activer explicitement la commande manuelle. Le bouton affiche l’état réel et un clic administrateur commande l’entité choisie ; aucun scénario n’exécute cette action. Les sources non commandables restent des mesures.

Pour le cumulus, configurer l’objectif quotidien, également accessible depuis sa carte Stockage : 2,16 kWh sur 3 kWh donnent 72 %. C’est une progression de consommation quotidienne, pas une mesure de chaleur disponible. La température reste séparée. Les batteries électriques gardent leur SOC mesuré.

La tolérance négative des appareils vaut 5 W par défaut : −1 à −5 W peuvent donc afficher 0 W avec traçabilité de la valeur brute. Au-delà, la mesure est signalée comme incohérente.
