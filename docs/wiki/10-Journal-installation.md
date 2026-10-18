# 10 — Journal d’installation à conserver localement

[Accueil](Home.md) · [Précédent : dépannage](09-Depannage.md)

Copier ce modèle hors du dépôt avant de le remplir. **Ne pas committer la version remplie si elle contient des adresses internes, identifiants d’équipements ou autres informations privées.** Ne jamais y écrire les secrets eux-mêmes.

## Fiche de l’installation

| Champ | Valeur à remplir |
| --- | --- |
| Date et opérateur | |
| Modèle RPi5 / RAM | |
| Alimentation / refroidissement | |
| HAT : marque, modèle, révision, notice | |
| HAT+ confirmé ? | |
| SSD : modèle, capacité | |
| Adaptateur USB NVMe | |
| Image OS : nom, date, provenance | |
| Version Imager | |
| Nom d’hôte / compte Linux | |
| Ethernet ou Wi-Fi | |
| Réservation DHCP | À conserver uniquement localement |
| Méthode SSH / emplacement de sauvegarde des clés | Référence seulement, pas la clé |
| OS / noyau / architecture | |
| EEPROM : version et BOOT_ORDER | |
| Réglages PCIe nécessaires | |
| Racine et partition de démarrage | |
| Versions Docker / Compose | |
| Commit eHome EMS | |
| Version images / configuration | À compléter quand disponibles |
| Emplacement des données et sauvegardes | À compléter quand disponibles |
| Dernière restauration testée | |

## Contrôles effectués

| Contrôle | Date | Résultat / observation |
| --- | --- | --- |
| Écriture du SSD et vérification Imager | | |
| Démarrage sur NVMe sans microSD | | |
| Second démarrage et SSH | | |
| Architecture ARM64 | | |
| Horloge synchronisée | | |
| Test Docker et Compose | | |
| Prototype simulé | | Non disponible à la création du guide |
| Lecture HA validée | | À faire après implémentation |
| Signes / unités / doubles comptages | | |
| Sauvegarde hors SSD | | |
| Restauration sur copie | | |

## Décisions à prendre

| Sujet | Décision / justification / date |
| --- | --- |
| Source de référence réseau et maison | |
| Convention charge/décharge et import/export | |
| Fréquence par source | |
| Délai de péremption | |
| Rétention des historiques | |
| Fréquence et conservation des sauvegardes | |
| Authentification de l’interface | |
| Accès distant éventuel | |

## Historique des changements

| Date | Changement | Version avant / après | Vérification | Retour arrière |
| --- | --- | --- | --- | --- |
| | | | | |

## Reproduire une installation

- [ ] Disposer du matériel compatible et de la notice du HAT.
- [ ] Retrouver l’image OS et les versions consignées.
- [ ] Refaire les phases 2 et 3 sur un disque identifié.
- [ ] Restaurer le logiciel et les données selon leur version.
- [ ] Refaire la recette.
- [ ] Noter les différences, même si elles semblent mineures.
