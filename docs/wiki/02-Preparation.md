# 02 — Préparer le matériel et les accès

[Accueil](Home.md) · [Suite : installation](03-Installation-RPi5-NVMe.md)

## Ce que nous savons

- Raspberry Pi 5 dédié.
- SSD **NVMe** monté sur HAT PCIe.
- PC Windows et adaptateur USB pour le SSD disponibles.
- Home Assistant OS sur un RPi4 distinct.
- Références exactes du SSD, du HAT, de l’alimentation et quantité de RAM non encore renseignées.

## Avant de commencer

- [ ] Relever la marque, le modèle et la capacité du SSD.
- [ ] Vérifier que l’adaptateur USB accepte le NVMe, et pas seulement les SSD SATA M.2.
- [ ] Retrouver la notice du HAT : format de SSD accepté, montage de la nappe, alimentation et conformité HAT+.
- [ ] Prévoir une alimentation adaptée au RPi5, au HAT et au SSD, ainsi qu’un refroidissement adapté.
- [ ] Prévoir un câble Ethernet pour le premier démarrage si possible.
- [ ] Garder une microSD de secours et son lecteur pour régler le démarrage si nécessaire.
- [ ] Sauvegarder toute donnée déjà présente sur le SSD : l’écriture de l’OS l’effacera.
- [ ] Débrancher du PC les autres disques externes non nécessaires pour réduire le risque de confusion.

## Choix à consigner

| Élément | Exemple proposé / valeur à choisir |
| --- | --- |
| Nom du RPi5 | `ehome-ems` |
| Compte Linux | `emsadmin` — exemple, pas un compte existant |
| Fuseau horaire | `Europe/Paris` si adapté au lieu d’installation |
| Réseau | Ethernet au départ ; Wi-Fi si nécessaire |
| Adresse stable | Réservation DHCP dans le routeur |
| Accès SSH | Clé publique recommandée ; mot de passe possible pour démarrer |
| Accès Internet entrant | Aucun prévu |

Ne pas inscrire de mot de passe, de clé privée, d’URL interne réelle ou de jeton dans le dépôt. Conserver les détails de l’installation dans une copie locale du [journal](10-Journal-installation.md).

## Outils

Télécharger [Raspberry Pi Imager pour Windows](https://www.raspberrypi.com/software/). PowerShell servira ensuite à la connexion SSH. Git et Docker seront installés sur le RPi5 à la phase 3.

Le guide ne modifie pas Home Assistant et ne nécessite aucune intervention sur le câblage électrique des équipements énergétiques.
