# Guide eHome EMS

**Installer, comprendre et retrouver chaque étape.**

Ce guide accompagne la construction d’un EMS résidentiel local sur Raspberry Pi 5 et SSD NVMe. Il est conçu pour une première installation et pour une réinstallation ultérieure.

> **État au 18 octobre 2026 :** cadrage et documentation disponibles ; application, images Docker et fichier Compose eHome EMS non encore livrés. Les procédures système peuvent être suivies dès maintenant, sous réserve de compatibilité du matériel. Elles n’ont pas été exécutées sur le RPi de l’utilisateur.

## Parcours conseillé

| Phase | Page | Résultat attendu |
| --- | --- | --- |
| 0 | [Introduction et architecture](01-Introduction.md) | Comprendre le périmètre et les versions |
| 1 | [Préparer le matériel](02-Preparation.md) | Identifier le RPi5, le HAT, le SSD et les accès |
| 2 | [Installer sur le SSD depuis Windows](03-Installation-RPi5-NVMe.md) | Démarrer Raspberry Pi OS Lite 64 bits sur NVMe |
| 3 | [Configurer le système et Docker](04-Configuration-systeme.md) | Disposer d’un hôte ARM64 accessible et vérifié |
| 4 | [Préparer le déploiement EMS](05-Deploiement-EMS.md) | Savoir ce qui est prêt et ce qui manque |
| 5 | [Configurer les sources et les mesures](06-Configuration-sources.md) | Préparer une intégration en lecture seule |
| 6 | [Valider la V1](07-Validation.md) | Vérifier les flux, les historiques et les erreurs |
| 7 | [Sauvegarder et reproduire](08-Sauvegarde-et-restauration.md) | Conserver les informations de reconstruction |
| Aide | [Dépannage](09-Depannage.md) | Retrouver les diagnostics courants |
| Suivi | [Journal d’installation](10-Journal-installation.md) | Noter les versions et les contrôles réellement effectués |

**Pour commencer maintenant :** suivre les phases 1 à 3, puis remplir une copie locale du journal. Les phases 4 à 6 décrivent la préparation et les critères du futur logiciel.

## Comment lire les instructions

- **Windows / PowerShell** : commandes sur le PC.
- **RPi / terminal SSH** : commandes sur le Raspberry Pi 5, jamais sur Home Assistant OS.
- Les noms `ehome-ems` et `emsadmin` sont des exemples proposés, à adapter.
- Une case non cochée signifie « à vérifier », pas « déjà fait ».
- Les paramètres applicatifs non implémentés sont explicitement signalés.

## Où est le Wiki ?

La documentation est versionnée ici, sur la branche `eHome`. Lors de la création, GitHub affichait « Upgrade or make this repository public to enable Wikis » pour ce dépôt privé. Ce guide fournit donc un parcours consultable sans changement d’offre ni de visibilité.

Si le Wiki natif devient disponible, ces pages pourront y être reprises ; garder une seule source éditoriale de référence et adapter les liens de pages. Voir la [documentation GitHub sur les wikis](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).

## Documents de référence

- [Cahier des charges](../CAHIER_DES_CHARGES.md)
- [Décision de déploiement RPi5](../DEPLOIEMENT_RPI5.md)
- [Présentation du projet](../../README.md)

La décision de déployer sur un RPi5 dédié précise le point d’hébergement encore ouvert dans le cahier des charges V0.1.
