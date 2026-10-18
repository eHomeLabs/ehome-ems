# 04 — Configurer le système et Docker

[Accueil](Home.md) · [Précédent](03-Installation-RPi5-NVMe.md) · [Suite : déploiement EMS](05-Deploiement-EMS.md)

**Prérequis :** RPi5 démarré sur NVMe, SSH fonctionnel, accès Internet sortant pour les paquets. Toutes les commandes ci-dessous s’exécutent sur le **RPi5**, pas sur le PC ni sur HA OS.

## 1. État du système

```bash
cat /etc/os-release
dpkg --print-architecture
timedatectl
hostnamectl
```

Noter la version de Raspberry Pi OS et son nom de code Debian. L’architecture attendue est `arm64`.

Mettre à jour, installer les outils de base puis redémarrer :

```bash
sudo apt update
sudo apt full-upgrade
sudo apt install git curl ca-certificates
sudo reboot
```

Après reconnexion, si nécessaire :

```bash
sudo timedatectl set-timezone Europe/Paris
timedatectl status
```

Une horloge synchronisée est nécessaire pour les historiques et la détection des données périmées. [Configuration officielle Raspberry Pi](https://www.raspberrypi.com/documentation/computers/configuration.html).

## 2. Réseau et accès

Dans le routeur, réserver une adresse DHCP pour le RPi5 ; conserver la correspondance dans le journal local. Vérifier SSH après un redémarrage. Garder le mot de passe ou la clé privée dans le gestionnaire de mots de passe, jamais dans Git.

L’installation cible reste en LAN. Le choix d’une méthode d’accès distant et de l’authentification de l’interface EMS sera traité séparément.

## 3. Installer Docker Engine et Compose

Pour **Raspberry Pi OS 64 bits**, suivre la filière Debian ARM64. Les commandes ci-dessous sont prévues pour un système neuf avec une version Debian prise en charge ; au contrôle documentaire, Bookworm et Trixie sont listés. En cas de version différente ou de Docker déjà installé, vérifier d’abord la [procédure officielle Docker](https://docs.docker.com/engine/install/debian/).

### Dépôt de paquets

```bash
sudo install -d -m 0755 /etc/apt/keyrings
sudo curl --fail --silent --show-error --location \
  https://download.docker.com/linux/debian/gpg \
  --output /etc/apt/keyrings/docker.asc
sudo chmod 0644 /etc/apt/keyrings/docker.asc

. /etc/os-release
printf 'Version Debian à vérifier : %s\n' "$VERSION_CODENAME"
dpkg --print-architecture
```

**Avant de continuer :** vérifier que le nom de code correspond à une version Debian prise en charge et que l’architecture est `arm64`. Ne pas substituer au hasard un autre nom de version.

```bash
printf 'Types: deb\nURIs: https://download.docker.com/linux/debian\nSuites: %s\nComponents: stable\nArchitectures: arm64\nSigned-By: /etc/apt/keyrings/docker.asc\n' \
  "$VERSION_CODENAME" | sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-buildx-plugin
```

### Contrôles

```bash
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
sudo docker run --rm hello-world
```

Attendus : versions client/serveur, version Compose et message de réussite du conteneur de test. Ce test nécessite un téléchargement et **ne lance pas eHome EMS**.

Ce guide conserve `sudo` pour Docker : l’ajout au groupe `docker` n’est pas nécessaire. Lors du futur déploiement, vérifier les ports publiés ; Docker peut contourner certaines règles UFW. [Source Docker](https://docs.docker.com/engine/install/debian/).

## 4. Point d’arrêt

- [ ] Linux ARM64, NVMe et horloge vérifiés.
- [ ] SSH accessible après redémarrage.
- [ ] Docker et Compose fonctionnels.
- [ ] Versions notées.
- [ ] Aucun service EMS présenté comme installé à ce stade.

Passer au [déploiement EMS](05-Deploiement-EMS.md) pour connaître les livrables encore nécessaires.
