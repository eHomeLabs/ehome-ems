# eHome EMS — Cahier des charges V0.1

## Vision
EMS résidentiel local, indépendant de Home Assistant, multi-marques et multi-protocoles. Interface web très graphique pour observer, comprendre et ultérieurement piloter l'énergie.

## Architecture
Sources (Home Assistant WebSocket/REST, MQTT, API locales/cloud) → adaptateurs → normalisation → moteur de calcul → stockage local → API → interface web.

## V1 — Lecture seule
- Vue des flux énergétiques en temps réel.
- Production PV, consommation maison, import/export réseau.
- Batteries : SOC, puissance de charge/décharge et énergie.
- Chauffe-eau, borne VE et consommateurs.
- Historiques 24 h, bilans journaliers.
- Mapping configurable des entités HA vers des métriques métier.
- Alertes de données absentes, périmées ou incohérentes.
- Démonstration avec données simulées.

## Matériel envisagé
Hoymiles PV, Zendure SolarFlow AC 2400, Aferiy P210, Shelly Pro 3EM, Zlinky, NodOn Zigbee, routeur solaire F1ATB, borne VE 20 A.

## V2
Pilotage sécurisé, priorités, modes de fonctionnement et délestage après validation explicite.

## V3
Prévisions solaires, anticipation de consommation, optimisation tarifaire.

## Points à décider
Hébergement RPi4/HA OS ou serveur indépendant ; mesures de référence et conventions de signe ; fréquence et rétention ; accès distant et authentification.
