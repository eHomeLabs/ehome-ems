# 01 — Introduction et architecture

[Accueil](Home.md) · [Suite : préparation](02-Preparation.md)

## Pourquoi eHome EMS ?

Rassembler les mesures d’énergie de la maison dans une interface graphique française : observer les flux, comprendre les usages et, plus tard, optimiser le fonctionnement.

Le cœur est **local-first et indépendant de Home Assistant**. HA est un adaptateur optionnel ; il peut servir de première source sans devenir le moteur de calcul de l’EMS.

## Architecture cible

```text
PV / batteries / réseau / usages
             │
HA WebSocket/REST · MQTT · API locales ou cloud selon disponibilité
             │
Adaptateurs → Mesures normalisées → Calculs → SQLite local
                                                │
                                      FastAPI → Interface React
```

Le RPi5 dédié hébergera Raspberry Pi OS Lite 64 bits, Docker Compose, Python/FastAPI, React/TypeScript et SQLite sur SSD NVMe. Le RPi4 sous Home Assistant OS reste distinct.

## Progression fonctionnelle

| Version | But | Périmètre |
| --- | --- | --- |
| V1 | Observer, en lecture seule | Flux temps réel, PV, maison, import/export, batteries, chauffe-eau et recharge VE ; historique 24 h, bilans journaliers, mapping HA, alertes et simulation |
| V2 | Piloter après validation explicite | Priorités, modes et délestage sécurisé |
| V3 | Anticiper | Prévisions solaires, consommation et optimisation tarifaire |

Aucune commande aux équipements en V1. Les connexions directes MQTT/API seront ajoutées progressivement ; la compatibilité de chaque appareil reste à vérifier.

## Équipements envisagés

| Famille | Équipements |
| --- | --- |
| Photovoltaïque | Hoymiles |
| Stockage | Zendure SolarFlow AC 2400, Aferiy P210 |
| Mesure | Shelly Pro 3EM, Zlinky |
| Équipements associés et usages | NodOn Zigbee, routeur solaire F1ATB, chauffe-eau, borne VE 20 A |

Cette liste décrit la cible, pas des intégrations déjà fonctionnelles.

## Décisions encore ouvertes

Mesures de référence, conventions de signe, cadence d’acquisition, rétention, authentification de l’interface et accès distant éventuel. Le modèle exact du HAT, la capacité du SSD et la RAM devront être consignés avant de conclure à la reproductibilité matérielle.
