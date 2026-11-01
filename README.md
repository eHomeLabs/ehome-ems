<p align="center"><img src="docs/assets/ehome-ems-banner.svg" alt="eHome EMS — Universal Energy Manager" width="100%"></p>

# eHome EMS — Universal Energy Manager

**Votre installation. Vos équipements. Votre énergie. Un EMS sur mesure.**

Une intégration Home Assistant pour comprendre la production solaire, la consommation réelle de la maison, les échanges réseau, le stockage et les appareils. Elle utilise les entités déjà présentes dans HA et fournit son panneau sans YAML à recopier.

**[Version 0.2.2](https://github.com/eHomeLabs/ehome-ems/releases/tag/v0.2.2)** — suivi en observation, scénarios sans exécution et commandes manuelles On/Off facultatives. Cette version consolide le fonctionnement de la b15 validé en usage ; elle ne livre pas encore le pilotage automatique.

[Installer](docs/INSTALLATION.md) · [Wiki illustré](docs/wiki/Home.md) · [Conso Maison](docs/CONSOMMATION_MAISON.md) · [Notes 0.2.2](docs/RELEASE_0_2_2.md) · [Feuille de route](docs/ROADMAP.md)

## Découvrir le dashboard

Les captures proviennent de la véritable interface avec **des données simulées**, sans connexion à une installation personnelle. Le thème et les équipements dépendent de votre configuration HA.

![Vue d'ensemble : puissances, tendances et flux](docs/screenshots/overview.png)

### Puissances et flux

Une seule flèche par carte : hausse, baisse ou stabilité entre moyennes de quarts d'heure sur les six dernières heures. Sans données suffisantes, flèche horizontale et mention explicite. Rouge lorsqu'une charge consomme une puissance positive, bleue sinon ; solaire, export et décharge restent bleus. Les valeurs sont affichées avec deux décimales maximum, les pourcentages sans décimales.

Import rouge et Export bleu sont distingués. Les flux s'animent à partir de 10 W ; les faibles puissances restent visibles. Les sous-compteurs sont inclus dans le total maison et n'ont pas de flux supplémentaire depuis la maison centrale.

![Flux énergétique avec maison de jour](docs/screenshots/energy-flow.png)

### Comprendre Conso Maison

**Conso Maison = Production solaire + Réseau − Charge batterie + Décharge batterie.**

Réseau positif en import, négatif en export. Avec deux capteurs, Réseau = Import − Export ; EMS ne cumule jamais réseau signé et paire séparée. Cumulus, borne, chauffage et appareils restent inclus dans le total.

Exemple : 2 000 W solaire − 300 W export − 500 W charge batterie = **1 200 W consommés par la maison**. Le calcul exige un périmètre AC cohérent ; une source maison existante adaptée reste disponible comme autre mode.

![Diagnostic des contributions au bilan maison](docs/screenshots/home-balance.png)

[Signes, topologies, fraîcheur et données manquantes](docs/CONSOMMATION_MAISON.md)

### Mes Appareils et usages

Ajouter, modifier ou retirer directement un appareil. Les icônes natives HA sont choisies selon le produit, avec sélection manuelle possible. Un compteur total permet de calculer l'énergie du jour depuis la référence de minuit conservée par History/Recorder. Sans référence exploitable, le coût du jour reste indisponible ; une énergie de session reste une énergie de session.

![Appareils : icônes, tendance unique, énergie du jour et cumul source](docs/screenshots/appliances.png)

**Énergie Totale** indique le compteur source. Dans l'exemple : 1 524,81 − 1 524 = **0,81 kWh aujourd'hui**, soit environ **0,17 €** au tarif fixe de 0,215 €/kWh. Les coûts sont estimatifs, hors abonnement et revente.

Sur le cumulus, « Température non associée » ou « Température indisponible » concerne l'eau, pas la puissance électrique. [Détails des usages et périodes](docs/USAGES_OBSERVATION.md).

### Stockage

Batteries suivies séparément : actif ou secours, AC/DC, charge/décharge, SOC et stock restant. Le SOC n'est pas présenté comme un stock mesuré. La confirmation d'un capteur réellement représentant le stock, mais mal classé par HA, ne désactive pas le contrôle de cohérence de capacité.

![Batteries et énergie restante](docs/screenshots/storage.png)

### Historique et Aujourd'hui

Chaque ligne Historique présente les **24 dernières heures**, avec unités, interruptions de données et accès au détail natif HA. History/Recorder doit conserver les sources.

![Courbes historiques sur 24 heures](docs/screenshots/history.png)

Aujourd'hui rassemble les compteurs quotidiens associés, les coûts estimatifs, les parts Import/Export, les ratios apparents d'autonomie/autoconsommation et la météo HA facultative. Ces ratios ne prouvent pas l'origine solaire de la décharge batterie ; la météo n'est pas une prévision de production photovoltaïque.

![Bilan du jour et résumé météo](docs/screenshots/today.png)

### Illustrations maison

Le flux commute automatiquement, dans le fuseau HA : **jour à 07:00**, **nuit à 19:00**. Les images sont incluses dans le paquet.

| Jour | Nuit |
| --- | --- |
| ![Maison de jour](custom_components/ehome_ems/frontend/assets/house-day.webp) | ![Maison de nuit](custom_components/ehome_ems/frontend/assets/house.webp) |

[Voir les illustrations et leur fonctionnement](docs/HOUSE_ASSETS.md)

### Configuration et assistant

Les raccourcis ouvrent directement chaque groupe de réglages. Les mesures valides sont vertes, les autres qualités rouges. La confirmation arrive en dernier dans le résumé de l'assistant.

![Configuration et qualité des associations](docs/screenshots/configuration.png)

## Installation et mises à jour

Home Assistant **2026.9.1 minimum**. Ajouter `https://github.com/eHomeLabs/ehome-ems` comme dépôt personnalisé HACS / Marketplace, catégorie **Intégration**, puis installer **0.2.2**. L'installation par dépôt personnalisé ne signifie pas validation officielle au catalogue.

**Première installation ou nouveau code Python :** redémarrer Home Assistant Core, puis ajouter l'intégration ou recharger le navigateur après mise à jour. **Réglages courants :** enregistrer suffit, sans redémarrage global. Recharger seulement l'entrée ne remplace pas les modules Python déjà chargés.

Depuis la b15, conserver l'entrée et ses associations. Aucun serveur supplémentaire n'est nécessaire. [Guide complet et retour arrière](docs/INSTALLATION.md).

## Navigation et périmètre livré

| Position | Onglet |
| --- | --- |
| 1 | Vue d'ensemble |
| 2 | Mes Appareils |
| 3 | Stockage |
| 4 | Usages |
| 5 | Historique |
| 6 | Aujourd'hui |
| 7 | Stratégie |
| 8 | Configuration |

| Disponible en 0.2.2 | Suite du projet |
| --- | --- |
| Assistant et réglages ciblés, normalisation et bilan AC | Topologies hybrides/DC avancées |
| Flux, tendances, historique 24 h, stockage et appareils | Analyses historiques et comparaisons |
| Compteurs du jour, cumuls, tarif fixe et météo HA | Tarification avancée et prévisions énergétiques |
| Scénarios sans exécution et commandes On/Off manuelles activées explicitement | Conseils puis pilotage automatique |

Le bouton de création de copie a été retiré. Les dashboards personnels déjà exportés restent préservés et indépendants. Le service `ehome_ems.generate_dashboard` génère une configuration sans écraser un dashboard existant.

## Documentation et validation

- [Wiki et parcours illustré](docs/wiki/Home.md)
- [Installer et mettre à jour](docs/INSTALLATION.md)
- [Panneau et historique](docs/DASHBOARD_AUTOMATIQUE.md)
- [Conso Maison](docs/CONSOMMATION_MAISON.md)
- [Appareils et usages](docs/USAGES_OBSERVATION.md)
- [Simulation sans commande](docs/SIMULATION.md)
- [Assistant et tests](docs/VALIDATION_ASSISTANT.md)
- [Revue du dépôt 0.2.2](docs/REVUE_0_2_2.md)
- [Cahier des charges](docs/CAHIER_DES_CHARGES.md) et [feuille de route](docs/ROADMAP.md)

La CI contrôle les calculs, les paramètres, le cycle reload/unload, le navigateur desktop/mobile et HA 2026.9.1 / 2026.11.0b0 sous Python 3.14. Elle produit une archive déterministe avec SHA-256. Ces tests ne certifient pas toutes les installations ni le futur pilotage matériel.

## Nouveautés 0.2.2

- Libellé uniforme **Tendance sur 15 mn** ; flèche horizontale si les données sont insuffisantes. Le calcul compare des moyennes de quarts d’heure, avec historique récent disponible.
- Petites puissances négatives d’un appareil corrigées en 0 W dans une tolérance configurable, **5 W par défaut**. La valeur brute et l’indication de correction restent dans les attributs du capteur EMS. La source originale, le réseau signé et le calcul Maison ne sont pas modifiés. Une valeur sous la tolérance reste indisponible.
- Dans **Modifier** un appareil ou usage : choisir une **Entité de commande On/Off** puis cocher **Activer la commande manuelle**. Domaines pris en charge : switch, input_boolean, light et fan. Les boutons affichent l’état réel HA ; un clic administrateur envoie l’action opposée. Aucun capteur de puissance n’est transformé en actionneur.
- Configurer l’**Objectif énergie quotidien (kWh)** depuis Usages ou Modifier le cumulus dans Stockage. **2,16 kWh / 3 kWh = 72 %**. La silhouette est remplie selon cet objectif ; la température reste indiquée séparément. Ce pourcentage représente l’énergie consommée aujourd’hui, **pas la chaleur restante**, ni le SOC d’une batterie. Le remplissage sature à 100 %, mais le pourcentage affiché peut dépasser l’objectif.

[Notes et configuration de la 0.2.2](docs/RELEASE_0_2_2.md)
