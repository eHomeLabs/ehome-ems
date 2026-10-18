# 03 — Installer Raspberry Pi OS sur NVMe depuis Windows

[Accueil](Home.md) · [Précédent](02-Preparation.md) · [Suite : configuration système](04-Configuration-systeme.md)

**Objectif :** système et données sur le SSD du HAT PCIe. La microSD n’est qu’un secours éventuel.

## A. Écrire le système — Windows

1. Brancher le SSD au PC avec l’adaptateur USB.
2. Ouvrir Raspberry Pi Imager ; choisir **Raspberry Pi 5**, puis **Raspberry Pi OS Lite (64-bit)**.
3. Choisir le SSD en vérifiant son modèle et sa capacité. **L’écriture efface ce disque.**
4. Personnaliser : nom `ehome-ems`, compte `emsadmin` ou autre, fuseau horaire, SSH, et Wi-Fi si nécessaire. Utiliser uniquement la clé **publique** pour une authentification par clé.
5. Lancer l’écriture et attendre la vérification.
6. Si Windows propose de formater une partition Linux, annuler. Éjecter le SSD proprement.

Les libellés d’Imager peuvent évoluer. [Procédure officielle Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html#install-an-operating-system).

## B. Monter et essayer

RPi éteint et alimentation débranchée : monter le SSD et la nappe selon la notice du HAT. Retirer l’adaptateur USB, brancher Ethernet puis alimenter le RPi5, sans microSD. Attendre quelques minutes pour le premier démarrage.

**Windows / PowerShell**, avec le compte choisi :

```powershell
ssh emsadmin@ehome-ems.local
```

Si le nom ne répond pas, utiliser l’adresse indiquée par le routeur. Vérifier l’empreinte SSH à la première connexion si elle est disponible sur une console locale. Une connexion SSH réussie ne prouve pas encore que le système est sur NVMe : faire les contrôles de la section D.

## C. Si le NVMe ne démarre pas : préparer le bootloader

### 1. Démarrer un système de secours

Écrire Raspberry Pi OS Lite 64 bits sur une **microSD de secours**, avec un nom distinct tel que `ehome-setup` et SSH activé. Éteindre le RPi, retirer temporairement le SSD du HAT, puis démarrer sur cette carte. Ne pas écraser le SSD préparé.

### 2. Mettre à jour — terminal du RPi sur microSD

```bash
sudo apt update
sudo apt full-upgrade
sudo rpi-eeprom-update
```

Si une mise à jour EEPROM est disponible sur le canal configuré :

```bash
sudo rpi-eeprom-update -a
sudo reboot
```

Se reconnecter après redémarrage. Garder le canal stable/default ; ne pas utiliser `rpi-update` pour cette installation.

[Référence : mises à jour et configuration du bootloader](https://www.raspberrypi.com/documentation/computers/configuration.html#update-the-bootloader).

### 3. Configurer le démarrage PCIe

Afficher puis éditer la configuration :

```bash
rpi-eeprom-config
sudo rpi-eeprom-config --edit
```

Remplacer la ligne existante, sans dupliquer :

```ini
BOOT_ORDER=0xf416
```

Cet ordre essaie NVMe, microSD, USB, puis recommence. Pour un adaptateur **non HAT+**, ajouter aussi :

```ini
PCIE_PROBE=1
```

Enregistrer, redémarrer pour appliquer, puis éteindre :

```bash
sudo reboot
# Après reconnexion :
rpi-eeprom-config
sudo poweroff
```

Sur le **SSD cible**, pour un adaptateur non HAT+, ajouter sous la section `[all]` de son fichier `config.txt` :

```ini
dtparam=pciex1
```

Depuis Windows, ce fichier se trouve sur la partition de démarrage lisible du SSD reconnecté en USB ; sous Linux démarré sur le SSD, son chemin est `/boot/firmware/config.txt`. Modifier le fichier de la microSD seule ne configure pas le SSD. Les HAT+ compatibles sont détectés automatiquement. Garder la vitesse PCIe par défaut.

[Référence : PCIe et démarrage NVMe](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#raspberry-pi-connector-for-pcie).

### 4. Refaire l’essai

Débrancher l’alimentation, retirer la microSD, remettre le SSD sur le HAT et démarrer. Utiliser cette fois le nom et le compte configurés sur le SSD.

## D. Confirmer le résultat — terminal du RPi

```bash
uname -m
dpkg --print-architecture
findmnt -no SOURCE /
findmnt /boot/firmware
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
df -h /
```

Attendus :

- `aarch64` et `arm64` pour l’architecture.
- La racine `/` et la partition de démarrage correspondent au disque NVMe ; généralement `nvme0n1p2` et `nvme0n1p1`.
- Une racine sur `mmcblk0` correspond à la microSD ; sur `sdX`, à un autre disque, potentiellement USB.
- La capacité utilisable correspond au SSD, à la place du système près.

Les noms peuvent varier : croiser `findmnt` et `lsblk`, ne pas se fier au seul exemple.

- [ ] Connexion SSH réussie.
- [ ] Architecture ARM64 confirmée.
- [ ] Racine et démarrage sur NVMe confirmés.
- [ ] Second démarrage réussi sans microSD.
- [ ] Résultats notés dans le journal local.

**En cas d’échec :** consulter le [dépannage](09-Depannage.md) avant toute nouvelle écriture du SSD.
