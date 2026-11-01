# Validation backend eHome EMS 0.2.0b1

Préparation du 31 octobre 2026. Cibles exécutées : Home Assistant Core 2026.9.1
et 2026.11.0b0, Python 3.14.8, Linux. Environnements temporaires distincts de toute
installation utilisateur, sans équipement ni automatisation physique.
La cible actuelle communiquée par l'utilisateur est 2026.11.0b0.

## Vérifications exécutées

- 48 tests de calculs, parcours, entités et génération du dashboard : réussis,
  également avec les dépendances HA 2026.11.0b0.
- Chargement du domaine puis de l'entrée dans un vrai moteur HA : réussi.
- Parcours réel réseau → solaire → maison → batterie → aperçu → confirmation.
- Sérialisation HTTP du formulaire batterie avec le sérialiseur HA : réussie.
- Création des miroirs, conversion kW → W et Wh → kWh, SOC en %.
- Propagation d'une source indisponible puis rétablie.
- Renommage d'un miroir dans le registre et résolution par l'action dashboard.
- Appel réel de ehome_ems.generate_dashboard avec réponse : quatre vues retournées.
- Modification par le parcours d'options réel et rechargement de l'entrée.
- Déchargement de l'intégration, absence de mise à jour active après déchargement,
  puis rechargement avec conservation de l'identifiant unique.
- Rechargement avec données au format V0.1, sans batteries : réussi.
- Construction du ZIP, contrôle des chemins et fichiers, somme SHA-256.

Les scénarios automatisés sont reproductibles avec
scripts/validate_home_assistant.py et scripts/build_test_package.py.
Le workflow Home Assistant beta package refait la validation des deux versions
avant de conserver le paquet comme artefact. Consulter l'exécution correspondant
au commit téléchargé.

## Corrections détectées par le test réel

Le déchargement du prototype appelait ConfigEntry.async_unload depuis le
gestionnaire de déchargement de cette même entrée. Cela provoquait un échec du
rechargement des options. L'intégration ne décharge maintenant que ses plateformes ;
HA exécute lui-même les callbacks enregistrés sur l'entrée.

Le validateur Python personnalisé du champ capacité n'était pas sérialisable
pour le formulaire HTTP de HA. Le champ utilise maintenant un schéma numérique
sérialisable ; le contrôle de capacité finie reste appliqué avant enregistrement.

## Portée des résultats

Les moteurs HA et leurs API sont réels. Les sources sont des états simulés ;
ce test ne valide ni les mesures matérielles, ni Zigbee2MQTT, ni les intégrations
constructeurs. Il ne valide pas le rendu dans un navigateur ou l'application mobile.

Les données antérieures de l'intégration restent au format version 1. Le numéro
logiciel 0.2.0b1 distingue le paquet ; les associations V0.1 sont conservées.
Au déchargement ou après retrait d'un miroir, HA peut conserver son entrée de
registre en état indisponible : cela ne signifie pas qu'un abonnement est actif.

Le message HA indiquant qu'une intégration personnalisée n'a pas été testée par
Home Assistant est l'avertissement standard des custom_components. Ce travail
ne constitue pas une validation officielle par Home Assistant ou HACS.

La bêta reste en observation : pas de commandes, de bilan journalier, de flux
animé, d'attribution solaire de la décharge batterie ou de prévision.
Le guide INSTALLATION_BETA.md décrit l'installation et le retour arrière.
