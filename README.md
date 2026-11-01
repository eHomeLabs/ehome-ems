# eHome EMS — Universal Energy Manager

![eHome EMS — Votre installation. Vos équipements. Votre énergie.](docs/assets/ehome-ems-banner.svg)

**Votre installation. Vos équipements. Votre énergie. Un EMS sur mesure.**

eHome EMS est une intégration Home Assistant qui rassemble les mesures de votre installation dans un dashboard énergétique : solaire, réseau, consommation de la maison, batteries et appareils suivis. Elle réutilise vos intégrations et capteurs existants.

**Version actuelle : [0.2.0b15 — préversion publique](https://github.com/eHomeLabs/ehome-ems/releases/tag/v0.2.0b15).** Le suivi fonctionne en observation, sans commande physique. Les priorités et scénarios de simulation restent distincts d’un pilotage réel.

[Installation](#installation) · [Découvrir le dashboard](#découvrir-le-dashboard) · [Conso Maison](#comprendre-conso-maison) · [Limites](#ce-qui-est-disponible-et-ce-qui-reste-à-développer) · [Notes b15](docs/RELEASE_0_2_0B15.md)

## Découvrir le dashboard

> Les captures ci-dessous proviennent du panneau b14 en fonctionnement avec des **données simulées**. Ce sont des captures de l’interface, pas des maquettes. Les noms, valeurs et états illustrent aussi les cas d’indisponibilité. Le thème et les équipements affichés dépendent de votre configuration Home Assistant.

### Vue d’ensemble : les puissances et les flux

Les mesures principales sont en haut, la maison et les flux au centre, la situation EMS à droite sur ordinateur, et les équipements secondaires en bas. Sur mobile, les sections s’empilent ; la navigation reste en haut.

![Vue d’ensemble eHome EMS : puissances, tendances, maison centrale, flux et situation EMS](docs/screenshots/overview.png)

- **Jaune : solaire ; rouge : import ; bleu : export ; vert : stockage.** Les usages conservent leurs couleurs dédiées.
- Les flux s’animent à partir de **10 W**. Une consommation de 1 W reste affichée sans animation et ne prouve pas qu’un appareil est arrêté.
- La maison passe automatiquement en mode **jour à 7 h** et **nuit à 19 h**, dans le fuseau de Home Assistant.
- Les tendances sont calculées **par pas de 15 minutes sur six heures**. Une flèche compare la moyenne d’un quart d’heure à celle du précédent. Sans données suffisantes, elle reste horizontale et explicitement neutre.
- Les valeurs utilisent au maximum deux décimales ; les **pourcentages sont affichés à l’entier**. La précision des calculs est conservée.

<details>
<summary>Voir le flux énergétique en détail</summary>

![Flux énergétique : solaire, réseau, batterie active, maison, cumulus, véhicule et batterie de secours séparée](docs/screenshots/energy-flow.png)

La batterie de secours est suivie séparément lorsqu’elle est hors du bilan actif. Les sous-compteurs cumulus et véhicule détaillent les usages : ils ne s’ajoutent pas une seconde fois à Conso Maison.

</details>

### Mes Appareils : puissance, énergie du jour et euros

Ajoutez, modifiez ou retirez les appareils directement depuis cet onglet : réfrigérateur, lave-linge, piscine, chauffage ou autre appareil disposant de capteurs HA. Retirer un suivi EMS ne supprime ni le capteur source ni l’équipement.

![Mes Appareils : puissance, tendances, énergie calculée du jour, cumul source et coût estimatif](docs/screenshots/appliances.png)

Pour un compteur cumulé, le panneau calcule l’énergie du jour depuis la référence conservée à minuit dans **History/Recorder**, dans le fuseau HA. Les remises à zéro sont prises en compte. Le cumul reste visible séparément.

**Exemple de la capture :** 1 524,81 kWh actuellement − 1 524 kWh à minuit = **0,81 kWh aujourd’hui**, soit environ **0,17 €** au tarif fixe de 0,215 €/kWh.

Sans référence valide à minuit, l’énergie et les euros du jour restent indisponibles. Une seule valeur cumulée ne permet pas de reconstituer le passé. Une énergie de session reste distincte d’une énergie journalière. Les euros sont un équivalent au tarif configuré, pas la facture réseau exacte d’un appareil pouvant consommer du solaire.

### Aujourd’hui : bilan, indicateurs et météo

Production, consommation, charge et restitution des batteries, import, export et cumulus se lisent sur des cartes de même format. La météo provient d’une entité `weather` déjà disponible dans HA : prévision journalière si fournie, sinon conditions actuelles explicitement identifiées.

![Aujourd’hui : énergies, équivalents en euros, météo, autonomie apparente et parts Import/Export](docs/screenshots/today.png)

L’autonomie et l’autoconsommation sont **apparentes** : les formules et hypothèses figurent dans le panneau. La charge batterie depuis le réseau, la variation du stock et un export depuis une batterie peuvent biaiser l’interprétation solaire. Toute décharge batterie n’est donc pas présentée comme du solaire.

### Stockage : batteries et eau chaude

Plusieurs batteries peuvent être suivies avec leur rôle **actif ou secours**, leur couplage AC/DC, leur charge, décharge, SOC et énergie restante mesurée. Le cumulus conserve une carte distincte : sa température n’est pas assimilée à une quantité d’énergie thermique stockée.

![Stockage : batterie active, batterie de secours et cumulus avec température et énergie du jour](docs/screenshots/storage.png)

L’énergie restante d’une batterie doit être un **stock**, pas un total d’énergie consommée. Si une intégration source classe mal ce stock comme `total` ou `total_increasing`, une confirmation explicite permet son utilisation. Le contrôle Wh/kWh et la limite de capacité déclarée + 10 % restent appliqués.

## Comprendre Conso Maison

**Conso Maison = Production solaire + Réseau − Charge batterie + Décharge batterie.**

| Terme | Convention |
| --- | --- |
| Production solaire | Puissance produite côté AC, ajoutée au bilan |
| Réseau signé | Positif en import, négatif en export |
| Deux capteurs réseau | Alternative équivalente : Réseau = Import − Export |
| Charge batterie | Retirée : cette électricité est mise en réserve dans la batterie électrique |
| Décharge batterie | Ajoutée : cette électricité alimente l’installation |

**Le cumulus, la borne de recharge, le chauffage et les appareils restent inclus.** Leurs sous-compteurs ne sont ni ajoutés ni soustraits au total. Le calcul additionne les batteries actives du même périmètre AC ; une batterie de secours hors de ce périmètre est exclue.

Exemple : solaire **2 000 W**, réseau **−300 W** (export), charge batterie **500 W**, décharge **0 W** → **Conso Maison = 1 200 W**, même sans achat au réseau.

Vous pouvez choisir un **capteur existant** représentant ce total, ou le **calcul automatique EMS**. Toutes les mesures du bilan doivent couvrir le même périmètre côté AC. Une puissance interne de pack/DC n’est pas interchangeable avec une puissance AC : les pertes de conversion et les mesures décalées peuvent expliquer des écarts.

<details>
<summary>Voir le diagnostic du calcul</summary>

![Détail Conso Maison : contributions signées, sources, ancienneté et qualité](docs/screenshots/home-balance.png)

Le détail s’ouvre automatiquement si le calcul est indisponible. Il affiche les contributions, les sources, leur âge et le motif du blocage. En observation, les rapports anciens sont signalés sans masquer un bilan numérique valide ; le mode Strict reste disponible. Une source manquante, invalide ou indisponible ne devient jamais zéro. Un bilan négatif est signalé.

</details>

## Installation

**Prérequis :** Home Assistant **2026.9.1 minimum**, des capteurs déjà présents dans HA et Marketplace/HACS pour l’installation recommandée. History/Recorder doit enregistrer les sources pour les tendances et le calcul journalier depuis les cumuls.

1. Dans **Marketplace/HACS → Dépôts personnalisés**, ajouter `https://github.com/eHomeLabs/ehome-ems` avec la catégorie **Intégration**.
2. Installer la préversion **0.2.0b15** ; afficher les versions bêta si nécessaire.
3. Redémarrer Home Assistant une fois, puis ouvrir **Paramètres → Appareils et services → Ajouter une intégration → eHome EMS**.
4. Associer réseau, solaire, Conso Maison et les équipements présents dans l’assistant. Confirmer les unités et le périmètre des mesures.
5. Ouvrir **eHome EMS** dans la barre latérale. Aucun YAML ni carte HACS tierce n’est requis pour ce panneau.

**Déjà installé ?** Conserver l’entrée et les associations, mettre à jour, redémarrer HA puis recharger le panneau. Les modifications suivantes via le dashboard rechargent l’intégration sans redémarrage complet de HA.

Le [guide d’installation et de retour arrière](docs/INSTALLATION_BETA.md) détaille aussi l’installation par ZIP. Un dépôt personnalisé installable ne signifie pas que l’intégration est référencée officiellement dans le catalogue Marketplace.

## Configurer après la première installation

| Onglet | Utilisation |
| --- | --- |
| Vue d’ensemble | Puissances, tendances, flux et état des données |
| Mes Appareils | Ajout et modification des appareils suivis, énergie du jour et euros |
| Stockage | Batteries, rôles actif/secours, SOC, stock et cumulus |
| Usages | Routeur solaire/ECS, borne VE et autres usages |
| Historique | Accès aux fiches et historiques natifs HA |
| Aujourd’hui | Compteurs du jour, ratios apparents, météo et échanges réseau |
| Stratégie | Priorités et scénarios de simulation à budget hypothétique, sans commande |
| Configuration | Raccourcis réseau, solaire, maison, batteries, usages, appareils, compteurs, tarif et météo |

![Configuration : raccourcis par rubrique, versions chargées et comparaison des sources avec les mesures EMS](docs/screenshots/configuration.png)

Les actions de modification sont réservées aux **administrateurs**. Un appui prolongé ou Entrée sur une mesure permet de changer sa source. La roue crantée de l’intégration conserve l’accès à l’assistant complet.

Pour la météo : **Configuration → Compteurs du jour et tarif**. Pour un stock restant mal classé, utiliser **Modifier la batterie**, puis la confirmation dédiée uniquement s’il s’agit bien d’un stock.

## Ce qui est disponible et ce qui reste à développer

| Disponible dans la b14 | Suite du projet |
| --- | --- |
| Assistant, mesures normalisées et réglages directs | Analyses énergétiques et coûts tarifaires plus avancés |
| Flux, tendances, suivi de plusieurs batteries et appareils | Prévisions énergétiques et planification |
| Énergie quotidienne depuis l’historique des cumuls, météo HA et ratios apparents | Conseils et optimisation tenant compte de l’origine du stock |
| Priorités et scénarios manuels de simulation | Pilotage coordonné avec activation explicite par équipement |

L’intégration **ne commande pas** les batteries, le routeur F1ATB ou la borne et ne modifie pas les automatisations existantes. Les régulations restent assurées par vos équipements et intégrations. Le socle fonctionne localement sans serveur autonome ni abonnement eHome EMS ; les intégrations sources peuvent dépendre du cloud.

Le projet reste une bêta : **V2 désigne le périmètre produit visé, pas une version 2.0 livrée**. Les copies natives personnelles existantes sont conservées ; l’export par `ehome_ems.generate_dashboard` reste disponible, sans écrasement d’un dashboard existant.

## Documentation et contribution

- [Notes et limites de la b15](docs/RELEASE_0_2_0B15.md)
- [Installation et retour arrière](docs/INSTALLATION_BETA.md)
- [Priorités et simulation](docs/SIMULATION.md)
- [Cahier des charges V2](docs/CAHIER_DES_CHARGES.md) et [feuille de route](docs/ROADMAP.md)
- [Rapport de vérification visuelle](design-qa.md)
- [Signaler un problème](https://github.com/eHomeLabs/ehome-ems/issues)

Pour un retour de test, préciser les versions HA et eHome EMS, le résultat attendu et le motif affiché dans le diagnostic. Masquer les URL privées, jetons et informations personnelles dans les captures et journaux.

Les tests couvrent les calculs, schémas de configuration, unités, signes, identifiants stables, rechargements et droits d’accès. La CI valide HA **2026.9.1** et **2026.11.0b0**, ainsi que le panneau Chromium sur ordinateur et mobile avec des données simulées. Ces validations ne remplacent pas les essais sur votre matériel.

Les anciens guides du serveur autonome RPi5 et le prototype V0.1 sont historiques. Le développement actuel concerne exclusivement l’intégration Home Assistant.

### Tendances, icônes et historique

Chaque carte conserve une seule flèche : hausse, baisse ou stabilité, calculée par pas de 15 minutes sur les six dernières heures. Sans données, elle reste horizontale. Elle est rouge lorsqu’une charge consomme une puissance positive, bleue sinon ; la production solaire, l’export et la décharge restent bleus. Les cartes gardent les mêmes alignements.

Les icônes natives Home Assistant sont choisies selon le nom du produit ; le menu « Modifier » permet aussi de choisir une icône. « Énergie Totale » désigne le compteur source, distinct de la consommation quotidienne calculée depuis minuit.

Sur le cumulus, « Température non associée » ou « Température indisponible » concerne uniquement la température de l’eau ; la puissance et l’énergie restent affichées séparément.

L’onglet Historique affiche les 24 dernières heures sur chaque ligne, avec les unités de la source et les interruptions de données. Cliquer sur le nom ouvre le détail natif Home Assistant. History/Recorder doit conserver ces sources.

![Historique des puissances sur 24 heures, données de démonstration](docs/screenshots/history.png)

La confirmation de l’assistant arrive après les raccourcis de correction. Les mesures valides apparaissent en vert, les autres en rouge. Aucun flux ne relie Conso Maison aux sous-compteurs : ceux-ci sont déjà inclus dans le total.
