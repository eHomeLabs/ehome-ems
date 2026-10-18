# 09 — Dépannage

[Accueil](Home.md) · [Précédent](08-Sauvegarde-et-restauration.md) · [Suite : journal](10-Journal-installation.md)

Commencer par relever le symptôme et la dernière étape réussie. Ne pas reformater le SSD comme premier diagnostic.

| Symptôme | Vérifications |
| --- | --- |
| SSD absent dans Imager | Compatibilité NVMe de l’adaptateur USB, câble, port et alimentation ; comparer modèle/capacité |
| Windows propose de formater | Annuler : Windows ne lit pas normalement la partition Linux |
| RPi inaccessible après écriture | Attendre le premier démarrage, contrôler alimentation, Ethernet et bail DHCP |
| Nom `.local` introuvable | Utiliser l’IP trouvée dans le routeur ; vérifier que PC et Pi sont sur un réseau communicant |
| SSH « Connection refused » | Vérifier l’adresse cible et l’activation SSH dans Imager ; utiliser une console locale si nécessaire |
| SSH « Permission denied » | Compte choisi dans Imager, mot de passe ou clé correspondante ; ne pas supposer un compte `pi` |
| Alerte de clé SSH changée | Vérifier d’abord qu’il s’agit bien du RPi réinstallé et contrôler sa nouvelle empreinte ; ne pas ignorer aveuglément l’alerte |
| Démarrage sur microSD | Voir la phase NVMe : bootloader, SSD cible, configuration du HAT ; retirer la carte seulement après arrêt |
| NVMe absent sous Linux | Arrêter et débrancher avant de vérifier nappe et montage ; consulter la notice exacte du HAT |
| NVMe détecté mais sans démarrage | Vérifier l’OS écrit sur le SSD, l’ordre EEPROM et les réglages non-HAT+ |
| Redémarrages ou disque instable | Contrôler alimentation, température, nappe et journaux ; conserver PCIe à sa vitesse par défaut |
| Dépôt Docker introuvable | Vérifier accès Internet/DNS, nom de code Debian et architecture ; ne pas forcer une suite incompatible |
| Docker « permission denied » | Utiliser `sudo docker …` comme dans ce guide |
| Aucun fichier Compose | Normal au stade actuel : le logiciel EMS reste à développer |
| Source HA inaccessible | Vérifier le réseau, l’adresse locale, l’état de HA et les permissions du compte |
| Totaux incohérents | Vérifier unités, signes, timestamps, périmètre et sous-compteurs déjà inclus |

## Relevé de diagnostic — sur le RPi5

```bash
findmnt -no SOURCE /
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
df -h /
timedatectl status
sudo systemctl status ssh --no-pager
sudo systemctl status docker --no-pager
sudo journalctl -b -p warning --no-pager -n 80
```

Ces sorties peuvent contenir des détails locaux. Les relire et masquer les informations sensibles avant de les partager. Ne jamais publier de jetons ou de configuration contenant des secrets.

## Retour à une base connue

Si le SSD ne démarre pas, utiliser la microSD de secours pour diagnostiquer. Si une modification de configuration a déclenché l’erreur, revenir à la copie précédente du **bon support**, puis refaire un seul changement à la fois.

La [procédure NVMe](03-Installation-RPi5-NVMe.md) distingue le réglage de l’EEPROM du réglage propre au SSD ; confondre ces deux niveaux peut laisser le problème inchangé.

## Demander de l’aide utilement

Fournir : modèle RPi/HAT/SSD, version OS, dernière étape réussie, message exact, résultat des contrôles pertinents et changement récent. Utiliser des valeurs anonymisées pour les adresses et ne pas joindre l’inventaire réel des entités HA.
