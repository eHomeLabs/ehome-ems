# eHome EMS — Universal Energy Manager
## Cahier des charges V0.2 — Home Assistant / HACS

**Votre installation. Vos équipements. Votre énergie. Un EMS sur mesure.**

> Statut : conception. Les fonctions ci-dessous sont des objectifs et non des fonctionnalités déjà livrées.

## 1. Vision et décision

eHome EMS est **exclusivement une intégration personnalisée Home Assistant distribuable via HACS**. L'architecture autonome sur Raspberry Pi 5, FastAPI, React, SQLite et Docker est **abandonnée**. Aucun serveur supplémentaire n'est nécessaire : les données proviennent des entités des intégrations HA existantes (Zigbee, MQTT, Wi-Fi, Modbus, API locales/cloud, etc.).

Principes : multimarque, local-first, open source, modulaire, extensible, installation guidée, transparence des calculs et commandes sécurisées. Pas de cloud eHome EMS imposé ; certaines intégrations tierces peuvent dépendre du cloud.

## 2. Parcours utilisateur

1. Installer depuis HACS et ajouter l'intégration dans Home Assistant.
2. Choisir les modules présents : réseau, maison, PV, batteries, eau chaude, chauffage/climatisation, borne VE et autres charges.
3. Découvrir les entités candidates via les registres et métadonnées HA (device_class, state_class, unité, domaine, fabricant, nom).
4. Confirmer ou corriger les associations, avec sélection manuelle toujours disponible.
5. Configurer les conventions de signe, capacités, limites et sources de mesure ; diagnostiquer les données incohérentes.
6. Générer un dashboard Lovelace adapté, personnalisable et évolutif.
7. Proposer ultérieurement des scénarios d'optimisation à valider explicitement.

L'absence d'un module ne bloque pas les autres. Les options permettent d'ajouter ou retirer des équipements sans recommencer la configuration.

## 3. Modules fonctionnels

| Module | Mesures visées | Pilotage futur si disponible |
| --- | --- | --- |
| Réseau | Import/export, puissance, énergie, tarifs | Seuils et priorités |
| Maison | Consommation, énergie et bilans | Délestage ciblé |
| PV | Production et énergie | Optimisation du surplus |
| Batteries | SOC, capacité, charge/décharge, énergie | Consignes et limites |
| Eau chaude | Puissance, énergie, température, état | Marche/arrêt et consignes |
| Chauffage/clim | Température, consigne, mode, énergie | Consignes et modes |
| Borne VE | Puissance, énergie, état, courant | Activation et courant |
| Autres charges | Puissance, énergie, état | Priorités et délestage |

Des profils optionnels faciliteront la configuration des équipements Linky/ZLinky, Shelly, NodOn, Hoymiles, Zendure, Aferiy et autres, sans rendre ces marques obligatoires.

## 4. Modèle énergétique

Normaliser W, Wh, %, °C et horodatages. Distinguer import et export, charge et décharge ; définir explicitement les conventions de signe. Conserver provenance et qualité des données ; séparer mesure, estimation et calcul. Contrôler les valeurs inconnues, absentes ou périmées et les changements d'unités.

Vérifier la cohérence du bilan énergétique et prévenir les doubles comptages (par exemple, charges déjà comprises dans la consommation maison). Ne pas afficher de valeurs déduites sans hypothèses explicites.

## 5. Dashboard

Créer automatiquement une interface Home Assistant responsive avec flux, jauges, bilans, historiques, états et alertes qualité. **Préserver les personnalisations utilisateur** lors des mises à jour ou régénérations. Privilégier les cartes natives ; envisager une carte frontend dédiée si nécessaire. Toute modification d'un dashboard existant exige confirmation et sauvegarde préalable.

## 6. Stratégies et IA

- **Manuel** : consultation et commandes volontaires sur équipements compatibles.
- **Règles** : surplus PV, chauffe-eau, batteries, heures creuses, recharge VE, délestage.
- **IA facultative** : analyse, prévisions et recommandations, sans dépendance pour le fonctionnement normal.

Toute commande exige une activation explicite, des limites de puissance/courant/température, temporisations, hystérésis, traitement des pannes de communication, journalisation et possibilité de retour manuel. L'IA ne contourne jamais les protections déterministes.

## 7. Architecture technique

```text
Équipements → Intégrations Home Assistant
                     ↓
          eHome EMS / HACS
          ├─ config_flow et options_flow
          ├─ découverte et profils
          ├─ normalisation / qualité
          ├─ calculs et entités EMS
          └─ stratégies et garde-fous futurs
                     ↓
       Dashboard Lovelace + services HA
```

Intégration Python asynchrone, API publiques HA, configuration gérée par HA, Recorder/Statistics pour l'historique lorsque pertinent. Tests automatisés, diagnostics, traductions, nettoyage des abonnements, gestion des erreurs et rechargements. Aucune base externe, aucun port Internet ni serveur indépendant imposés.

## 8. Feuille de route et acceptation

| Version | Objectif | Critère de validation |
| --- | --- | --- |
| V0.1 | HACS, assistant, réseau/PV/maison, lecture seule | Associations modifiables, mesures cohérentes, diagnostics, aucune commande |
| V0.2 | Dashboard automatique | Responsive, personnalisations préservées |
| V0.3 | Batteries, eau chaude, HVAC, VE | Modules indépendants, entités manquantes gérées |
| V0.4 | Pilotage par règles | Autorisation, garde-fous, journal, arrêt et retour manuel testés |
| V0.5 | Prévisions et IA optionnelle | EMS opérationnel sans IA ni cloud propre |

## 9. Banc d'essai eHome Labs

Home Assistant OS sur RPi4 ; ZLinky/Linky, Shelly Pro 3EM, modules Zigbee NodOn, photovoltaïque Hoymiles, stockage Zendure SolarFlow AC 2400 et Aferiy P210, routeur F1ATB/cumulus, borne VE 20 A. Ces produits servent aux tests et ne constituent pas une liste de compatibilité garantie.

Tester les unités, signes, bilans, valeurs indisponibles, changements d'entités, redémarrages, restauration, profils et conservation des personnalisations.

## 10. Hors périmètre

Serveur RPi5 autonome, Raspberry Pi OS dédié, Docker Compose, FastAPI, API matérielles parallèles à HA, cloud eHome EMS obligatoire, commandes non autorisées.

## 11. Prochaines décisions

Définir les métriques minimales V0.1, le schéma de configuration, les règles de découverte et la stratégie de génération Lovelace.

[Retour au README](../README.md)
