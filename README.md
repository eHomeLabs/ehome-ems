# eHome EMS — Universal Energy Manager

![eHome EMS](docs/assets/ehome-ems-banner.svg)

**Votre installation. Vos équipements. Votre énergie. Un EMS sur mesure.**

eHome EMS vise à transformer les données déjà présentes dans Home Assistant en un gestionnaire énergétique guidé : configurer, visualiser, comprendre, prévoir, puis piloter.

**Statut : cadrage V2, développement à poursuivre.** Cette documentation remplace le cadrage V0.1. Le code présent dans `custom_components/ehome_ems` reste le prototype V0.1 de lecture seule ; les fonctions V2 décrites ici ne sont pas encore livrées. V2 désigne le périmètre produit, pas une release logicielle 2.0.

## Où en est le projet ? — Repères au 31 octobre 2026

| Élément | État actuel |
| --- | --- |
| Code disponible | Prototype V0.1 en lecture seule, conservé dans `custom_components/ehome_ems` |
| Cadrage du projet | Cahier des charges V2, qui remplace les anciennes orientations |
| Assistant pas à pas | Réseau, solaire, maison et vérification codés sur cette branche de développement ; validation HA réelle à faire |
| Dashboard V2 et stockage | À développer |
| Prévisions, conseils et pilotage V2 | Prévus dans les lots suivants ; pas encore livrés |
| Prochaine étape | Développer et valider le lot A : assistant, mesures fiables, flux, jauges et statistiques |
| Ancien serveur autonome RPi5 | Abandonné ; ses guides sont historiques |

**V2 est la vision produit en préparation. Elle n'est pas une version installable du logiciel à ce stade.**

### Quel document consulter ?

- **Comprendre ce que nous allons construire :** [cahier des charges V2](docs/CAHIER_DES_CHARGES.md).
- **Suivre l'ordre de développement et la validation :** [feuille de route](docs/ROADMAP.md).
- **Installer ou tester uniquement le prototype existant :** [installation V0.1](docs/INSTALLATION_V0_1.md) et [validation V0.1](docs/VALIDATION_V0_1.md).

Les instructions d'installation V0.1 ne donnent pas accès au dashboard V2. Pour la suite du développement, les références sont le cahier des charges V2 et la feuille de route.

## Premier incrément du lot A — en développement

Cette branche prépare la normalisation des puissances et le premier assistant.
Elle ne constitue pas une livraison complète du lot A ni une release HACS.

- Conversion W/kW vers W.
- Capteur réseau global signé conservé ; export présenté comme une magnitude
  positive, y compris si le compteur source le publie en négatif.
- Valeur négative sur import, solaire ou maison signalée indisponible.
- Attributs `data_quality`, `source_unit` et `value_origin` sur les capteurs.
- Donnée absente, unité incorrecte ou valeur non finie : aucune substitution par zéro.

L'assistant sépare réseau, solaire, maison, aperçu et confirmation. Depuis
l'aperçu, chaque étape peut être corrigée. Les réglages V0.1 sont proposés
à nouveau dans les options ; un champ effacé reste effacé. Aucun changement
n'est enregistré avant la validation finale. Les sources absentes, les unités
autres que W/kW, les doublons et les capteurs miroirs eHome EMS sont refusés.
Une source temporairement indisponible avec une unité valide reste configurable,
avec un avertissement dans l'aperçu.

La fraîcheur des sources, le bilan multi-équipements,
le stockage et le dashboard restent à développer. Les identifiants uniques
existants sont conservés. Les automatismes utilisant le signe du miroir
d'export doivent tenir compte de sa nouvelle convention positive.

Installation des dépendances de test : `python -m pip install -r requirements-test.txt`.
Tests de calcul et de parcours :
`python -m unittest discover -s tests -v`.
La CI vérifie aussi la syntaxe Python. Les tests du parcours utilisent les
vrais schémas Voluptuous et des doubles des API HA ; ils ne remplacent pas
un test de chargement/rechargement dans Home Assistant.
Voir le [plan de validation de l'assistant](docs/VALIDATION_ASSISTANT.md).

## Documentation de référence

- **[Cahier des charges complet V2](docs/CAHIER_DES_CHARGES.md)**
- [Feuille de route et critères de validation](docs/ROADMAP.md)
- [Accueil de la documentation](docs/wiki/Home.md)

## Une intégration Home Assistant

Distribution cible via HACS / Marketplace, configuration pas à pas et dashboard adapté aux équipements réellement présents. Les données et commandes utilisent les intégrations HA existantes, quels que soient leurs protocoles ou fabricants.

Le socle fonctionne localement, sans serveur autonome ni abonnement eHome EMS. Les sources tierces peuvent dépendre du cloud. Une IA éventuelle reste facultative.

## Installation guidée cible

1. Choisir les modules présents.
2. Associer les mesures réseau, photovoltaïque et maison.
3. Ajouter les batteries et leurs rôles.
4. Déclarer les usages et les commandes disponibles.
5. Configurer tarifs, objectifs, contraintes et réserves.
6. Ajouter les prévisions disponibles, facultativement.
7. Vérifier unités, signes, fraîcheur et bilan.
8. Prévisualiser puis générer le dashboard en observation.

Suggestions d'entités modifiables, reprise du parcours et réglages rechargeables sans redémarrage complet de HA. La première installation et certaines mises à jour peuvent nécessiter un redémarrage.

## Modules

| Module | Fonctions cibles |
| --- | --- |
| Photovoltaïque | Plusieurs sources, production, énergie, prévisions |
| Réseau | Import/export, tarifs, coûts et limites |
| Maison | Consommation, talon, historique et bilan |
| Stockage | Plusieurs batteries, SOC, réserve, charge/décharge et rôle secours |
| Surplus | Export mesuré, allocations en cours et puissance réallouable |
| Usages | ECS/routeur, VE, piscine, chauffage/PAC et autres charges |
| Analyse | Autoconsommation, autonomie, anomalies, coûts et comparaison réel/prévu |

L'absence d'un module ne bloque pas les autres.

## Dashboard cible

- Flux animé solaire/maison/réseau/batteries/usages, inspiré de la lisibilité Zendure.
- Jauges de puissance W/kW et d'énergie kWh avec période explicite.
- Vues Synthèse, Aujourd'hui, Historique, Stockage, Usages, Prévisions, Conseils et Réglages.
- Adaptation mobile, tablette et PC ; valeurs et sens compréhensibles sans couleur.
- Personnalisation conservée et copie librement éditable sans écrasement par une régénération.

La génération et le conditionnement des ressources frontend seront validés par prototype.

## Mesures et décisions explicables

Les mesures, calculs et estimations sont distingués. Les unités, signes, topologies AC/DC et doubles comptes sont contrôlés. Une source indisponible n'est jamais remplacée arbitrairement par zéro.

L'injection réseau seule ne représente pas tout le surplus réallouable. La décharge d'une batterie ne doit pas être assimilée automatiquement à du solaire, notamment après charge en heures creuses.

Les conseils indiquent hypothèses, contraintes et gains estimés. Les prévisions présentent leur fraîcheur et leurs erreurs ; les économies simulées restent distinctes des résultats mesurés.

## Modes de fonctionnement cibles

| Mode | Comportement |
| --- | --- |
| Observation | Mesurer, afficher et analyser, sans commande |
| Conseil | Proposer une action et sa justification |
| Simulation | Journaliser les décisions sans les exécuter |
| Automatique | Commander uniquement les équipements explicitement activés |

Un arbitre coordonne stockage et usages selon leurs priorités, réserves, échéances et limites. Il doit coopérer avec les régulations existantes, dont F1ATB, et respecter les reprises manuelles et les données périmées.

## Développement progressif

| Lot | Livrable |
| --- | --- |
| A — Socle visuel | Assistant, mesures fiables, flux, jauges et statistiques en lecture seule |
| B — Compréhension | Tarifs, analyses, prévisions et conseils |
| C — Orchestration | Simulation puis pilotage coordonné |
| D — Optimisation | Profils, scénarios et planification avancée facultative |

**Première priorité : lot A sur le banc de validation RPi4 avec SSD.** Aucun solveur lourd obligatoire. Les interfaces des lots B et C doivent être anticipées.

## Inspirations

PV Pilot pour la simplicité et le surplus ; Home Assistant Energy pour les statistiques ; Predbat pour la batterie prévisionnelle ; EMHASS pour la planification ; evcc pour la recharge solaire. Les liens et limites de l'étude figurent dans le [cahier des charges](docs/CAHIER_DES_CHARGES.md). Aucun de ces projets n'est une dépendance obligatoire.

## Prototype et historique

Le [guide V0.1](docs/INSTALLATION_V0_1.md) et le [plan de validation V0.1](docs/VALIDATION_V0_1.md) concernent uniquement le prototype existant. Ils ne permettent pas d'installer les fonctions V2.

Les pages numérotées de l'ancien guide RPi5 sont historiques et obsolètes. Le serveur autonome est abandonné ; consulter la [note correspondante](docs/DEPLOIEMENT_RPI5.md).

Cette branche contient du code en développement. Aucune installation Home Assistant
réelle n'a été modifiée pendant son développement.
