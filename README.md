# eHome EMS — Universal Energy Manager

![eHome EMS — Universal Energy Manager, intégration Home Assistant](docs/assets/ehome-ems-banner.svg)

**Votre installation. Vos équipements. Votre énergie. Un EMS sur mesure.**

> **Statut : V0.1 pilote, non encore testée sur une instance Home Assistant réelle.** Configuration manuelle de cinq sources de puissance, capteurs de lecture seule et rechargement des associations. Avant tout essai sur l'installation principale, effectuer une sauvegarde complète.

## Essayer la V0.1

**[Guide d'installation et de validation sur Home Assistant](docs/INSTALLATION_V0_1.md)**

- Intégration Python dans [`custom_components/ehome_ems`](custom_components/ehome_ems), métadonnées HACS à la racine.
- Assistant de sélection manuelle de **cinq** sources : réseau signé, import, injection, solaire, maison.
- Cinq capteurs EMS de lecture seule, reprenant les valeurs HA (W ou conversion kW → W), sans commandes.
- Options de modification avec rechargement de l'intégration, sans redémarrage du Raspberry Pi.
- Traductions française et anglaise.
- **Limites :** aucun dashboard ni pilotage, pas de validation en conditions réelles à ce stade. HACS peut ne pas accéder au dépôt privé ; la copie manuelle est documentée.

## Vision

**eHome EMS** ambitionne de rendre la gestion énergétique résidentielle accessible aux utilisateurs de Home Assistant, sans imposer de fabricant, de protocole ni de serveur supplémentaire.

L'utilisateur installe l'intégration depuis HACS, puis un assistant l'accompagne pour découvrir, sélectionner et associer ses entités Home Assistant aux fonctions énergétiques de son installation. eHome EMS construit ensuite un **dashboard énergétique personnalisable et évolutif** et peut proposer des stratégies d'optimisation ou des automatisations à valider.

**Périmètre : exclusivement Home Assistant.** eHome EMS réutilise les équipements et données déjà exposés par les intégrations HA (Zigbee, MQTT, Wi-Fi, Modbus, API locales/cloud, etc.). Il n'est **pas** prévu de développer un serveur EMS autonome, une application indépendante ni des connecteurs matériels parallèles à HA. Un Raspberry Pi dédié n'est pas nécessaire.

## Principes fondateurs

- **Universel dans l'écosystème Home Assistant** : indépendant des marques, fondé sur des fonctions énergétiques communes.
- **Installation guidée** : aucune configuration YAML obligatoire pour les fonctions de base.
- **Détection assistée** : propositions automatiques de correspondances, toujours vérifiables et modifiables.
- **Local-first** : calcul, configuration et pilotage exécutés dans HA ; pas de cloud eHome EMS requis. Certaines intégrations HA peuvent elles-mêmes dépendre du cloud.
- **Progressif** : utilisable pour une installation simple, extensible aux installations complexes.
- **Transparent** : données, hypothèses, règles et actions compréhensibles.
- **Sécurisé** : lecture seule au démarrage ; aucune commande d'équipement sans autorisation explicite.
- **Open source** : architecture documentée, contributions et profils d'équipements communautaires encouragés.

## Parcours utilisateur envisagé

1. **Installer** eHome EMS depuis HACS, puis ajouter l'intégration dans Home Assistant.
2. **Choisir les modules** présents dans l'installation : réseau, photovoltaïque, batteries, chauffe-eau, chauffage/climatisation, recharge VE, autres charges.
3. **Découvrir les entités** : l'assistant propose des correspondances à partir des métadonnées et capacités HA ; l'utilisateur peut rechercher, confirmer ou corriger chaque association.
4. **Valider les mesures** : unités, signes, sources, fraîcheur, capacités, limites et risques de doubles comptages.
5. **Générer le dashboard EMS** : vues et indicateurs adaptés aux modules configurés ; personnalisation et évolutions sans perdre les choix de l'utilisateur.
6. **Optimiser à la demande** : scénarios suggérés, simulation si disponible, validation explicite et activation réversible.

## Modules fonctionnels

| Module | Données ou capacités visées |
| --- | --- |
| Réseau électrique | Puissance, import/export, énergies cumulées, tarifs |
| Maison | Consommation totale, bilans, historique |
| Photovoltaïque | Production instantanée et cumulée |
| Batteries | État de charge, capacité, puissance de charge/décharge, limites, commandes si disponibles |
| Eau chaude | Température, puissance, énergie, consigne ou marche/arrêt si disponibles |
| Chauffage et climatisation | Températures, modes, consignes, consommations et commandes |
| Recharge VE | État de charge, puissance, courant maximal, énergie et pilotage si disponibles |
| Autres charges | Mesure, classification, priorités et délestage si possible |

L'absence d'un module ne doit pas bloquer les autres.

## Architecture cible

```text
Équipements et services
  Zigbee · MQTT · Wi-Fi · Modbus · API · Cloud (via HA)
                       ↓
         Intégrations Home Assistant
                       ↓
      eHome EMS (custom integration / HACS)
      ├─ Découverte et association d'entités
      ├─ Modèle énergétique normalisé
      ├─ Contrôle de qualité des données
      ├─ Configuration et profils d'équipements
      ├─ Calculs, bilans et indicateurs
      └─ Moteur de stratégies et de sécurité
                       ↓
       Dashboard Home Assistant / Lovelace
                       +
       Automatisations et services HA
```

Le **modèle énergétique** sépare le rôle d'un équipement de sa marque. Une batterie Zendure, EcoFlow ou Victron doit pouvoir être décrite par les mêmes concepts (SOC, puissance, énergie, capacité), sous réserve des entités réellement disponibles. Les profils fabricants pourront faciliter l'association, sans devenir obligatoires.

La configuration devra prendre en compte les unités (W, kW, Wh, kWh, %), les conventions de signe, l'horodatage, la qualité des mesures, les données manquantes et les doubles comptages. Les valeurs déduites devront être distinguées des valeurs mesurées.

### Interface et personnalisation

L'objectif est de produire automatiquement un dashboard Home Assistant lisible (flux énergétiques, jauges, bilans, historiques, états des équipements), qui reste **modifiable et évolutif**. L'architecture de génération devra préserver les personnalisations lors des mises à jour ou de l'ajout de modules. Le choix entre vues Lovelace natives et cartes frontend dédiées sera validé par prototype.

### Automatisations et IA

Trois niveaux sont envisagés :

1. **Manuel** : consultation et commande volontaire des équipements compatibles.
2. **Règles** : stratégies configurables (surplus PV, chauffe-eau, batterie, heures creuses, recharge VE, délestage) avec validation préalable.
3. **Assistance intelligente facultative** : recommandations fondées sur les historiques, prévisions et tarifs ; l'IA propose, mais ne remplace pas les sécurités déterministes.

Les commandes devront respecter les limites matérielles, les priorités, les conditions d'arrêt et les possibilités de retour au pilotage manuel. Une perte de données ou de communication ne doit pas entraîner de commandes dangereuses.

## Feuille de route prévisionnelle

| Version | Objectif | Livrables envisagés |
| --- | --- | --- |
| **V0.1 — Fondations** | Intégration HACS et lecture seule | Config flow, découverte/association manuelle, réseau, PV, consommation maison, normalisation et diagnostics |
| **V0.2 — Visualisation** | Dashboard généré | Flux, historiques, indicateurs, personnalisation conservée |
| **V0.3 — Équipements** | Étendre la couverture | Batteries, eau chaude, chauffage/climatisation, borne VE |
| **V0.4 — Pilotage** | Automatisations sûres | Scénarios, règles, confirmations, désactivation et contrôles |
| **V0.5 — Intelligence** | Optimisation facultative | Prévisions, recommandations, assistance IA optionnelle |

Les versions et fonctionnalités pourront évoluer en fonction des tests.

## Banc d'essai initial : eHome Labs

L'installation eHome Labs servira de référence pour tester des équipements et situations variés déjà intégrés dans Home Assistant :

- **Mesure** : Linky/ZLinky, Shelly Pro 3EM, modules Zigbee NodOn.
- **Photovoltaïque** : micro-onduleurs Hoymiles.
- **Stockage** : Zendure SolarFlow AC 2400 et Aferiy P210.
- **Eau chaude** : routeur solaire F1ATB et cumulus.
- **Recharge** : borne VE 20 A.
- **Protocoles via HA** : Zigbee, MQTT, Wi-Fi et autres intégrations.

Ces équipements constituent un **terrain de validation**, et non une liste exclusive de compatibilité.

## Pistes techniques

- Intégration personnalisée Python sous `custom_components/ehome_ems`.
- Assistant de configuration Home Assistant (`config_flow` et options).
- Sélection d'entités existantes, sans dupliquer leurs intégrations.
- Capteurs et diagnostics eHome EMS lorsque nécessaire.
- Dashboard Lovelace généré et/ou cartes dédiées selon les contraintes de personnalisation.
- Tests automatisés, données simulées, documentation et traductions (français prioritaire, anglais envisagé).

## Prochaines étapes

1. Valider le modèle de données énergétiques et les conventions de signe.
2. Définir le parcours de configuration et les règles de découverte d'entités.
3. Prototyper une V0.1 en lecture seule sur une installation Home Assistant de test.
4. Vérifier la cohérence des bilans et l'absence de doubles comptages.
5. Prototyper le dashboard généré, puis le mécanisme de personnalisation durable.

## Documentation existante

Les documents historiques du dépôt décrivent encore l'**ancien concept de serveur autonome sur Raspberry Pi 5** et doivent être révisés ou archivés avant d'être utilisés comme référence d'implémentation :

- [Cahier des charges Home Assistant](docs/CAHIER_DES_CHARGES.md)
- [Note d'abandon du déploiement RPi5](docs/DEPLOIEMENT_RPI5.md)
- [Accueil de la documentation](docs/wiki/Home.md)
- [Plan de validation V0.1](docs/VALIDATION_V0_1.md)

---

**eHome EMS — Universal Energy Manager**  
*Votre installation. Vos équipements. Votre énergie. Un EMS sur mesure.*
