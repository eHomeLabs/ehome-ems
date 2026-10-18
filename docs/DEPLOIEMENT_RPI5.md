# Déploiement cible — Raspberry Pi 5

> Pour la procédure détaillée, suivre le [guide pas à pas](wiki/Home.md), puis [l’installation RPi5/NVMe depuis Windows](wiki/03-Installation-RPi5-NVMe.md).

## Décision validée
eHome EMS sera hébergé sur un Raspberry Pi 5 dédié, distinct du Raspberry Pi 4 qui héberge Home Assistant OS.

## Architecture cible
- Raspberry Pi 5 : Raspberry Pi OS Lite 64 bits, Docker Engine et Docker Compose.
- Stockage SSD recommandé pour le système, les historiques et les sauvegardes.
- Backend : Python/FastAPI ; frontend : React/TypeScript compilé et servi localement.
- Stockage initial : SQLite persistant sur volume dédié.
- Connexion en lecture seule à Home Assistant (RPi4) via API WebSocket/REST et, si utile, MQTT.
- Les adaptateurs directs (MQTT/API locales) seront ajoutés progressivement pour réduire la dépendance à HA.

## Sécurité
- Pas d'ouverture de ports Internet par défaut.
- Secrets dans des variables d'environnement locales non versionnées.
- Jeton HA limité aux besoins, avec prudence sur les permissions réellement offertes par HA.
- Commandes aux équipements interdites en V1.
- Sauvegardes locales, healthchecks et journalisation sans secrets.

## Étapes
1. Développer un prototype autonome avec données simulées.
2. Préparer les conteneurs et le déploiement Docker Compose pour ARM64.
3. Déployer sur RPi5 en LAN.
4. Connecter Home Assistant en lecture seule.
5. Vérifier les mesures, conventions de signe, données périmées et doubles comptages.

## À confirmer
Capacité RAM du RPi5, SSD disponible, mode de connexion Ethernet/Wi-Fi, éventuel besoin d'accès distant.
