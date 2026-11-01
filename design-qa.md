# eHome EMS 0.2.2 — contrôle de l'interface

Les captures desktop/mobile sont générées avec des données simulées depuis le panneau réel. Les cartes conservent des emplacements alignés pour le titre, la valeur et la tendance ; les appareils réservent aussi énergie, état et actions.

Une seule flèche indique la comparaison des moyennes des derniers quarts d'heure sur six heures. Sans données suffisantes, elle reste horizontale avec une mention explicite. Une charge positive est rouge ; production, export, décharge et absence de consommation sont bleus. Il n'y a plus de grille de 24 petites flèches ni de liaison maison vers les sous-compteurs.

Les produits ont des icônes natives MDI déduites de leur nom ou sélectionnées dans les réglages. L'historique présente une courbe 24 h par ligne et conserve les interruptions. Le cumulus distingue température non associée/indisponible et puissance électrique.

Les contrôles navigateur couvrent l'alignement, les couleurs lors d'une variation de puissance, les droits et formulaires, les onglets, la météo, le calcul du jour depuis cumul, les liens natifs d'historique et les illustrations jour/nuit. Les pourcentages visibles sont entiers. Les tests ne certifient pas les sources physiques d'une installation personnelle.

[Captures du panneau](docs/DASHBOARD_AUTOMATIQUE.md) · [Revue de release](docs/REVUE_0_2_1.md)

La 0.2.2 affiche « Tendance sur 15 mn » sur toutes les cartes. La carte cumulus utilise l’objectif quotidien déclaré et présente température et énergie séparément. Les boutons On/Off ne deviennent actifs qu’après association et activation manuelles ; le rendu utilise l’état HA réel, sans l’inventer après un ordre. Les fixtures comprennent un cumulus à 2,16 / 3 kWh (72 %) et une commande de frigo simulée.
