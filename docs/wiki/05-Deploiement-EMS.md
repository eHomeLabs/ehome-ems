# 05 — Préparer le déploiement eHome EMS

[Accueil](Home.md) · [Précédent](04-Configuration-systeme.md) · [Suite : sources](06-Configuration-sources.md)

> **Phase en préparation.** À la rédaction, le dépôt contient la documentation et le visuel ; il ne fournit pas encore de backend, frontend, image Docker, fichier Compose ni exemple de configuration exécutable.

## Ce que l’on peut faire maintenant

Sur le RPi, récupérer le dépôt avec un accès GitHub autorisé :

```bash
mkdir -p ~/projets
cd ~/projets
git clone --branch eHome https://github.com/eHomeLabs/ehome-ems.git
cd ehome-ems
git log -1 --oneline
git status --short
```

Le dépôt est privé. Si l’authentification échoue, configurer un accès GitHub prévu pour cette machine ; ne pas intégrer de jeton à l’URL, au wiki ou à une commande conservée dans l’historique. Le mot de passe du compte GitHub ne remplace pas une méthode d’authentification Git. [Authentification GitHub en ligne de commande](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#authenticating-with-the-command-line).

Si le dossier existe déjà, ne pas recloner dessus. Examiner les modifications locales avant toute mise à jour.

## Livrables nécessaires avant le premier lancement

| Livrable | Exigence |
| --- | --- |
| Prototype | Démonstration autonome avec données simulées |
| Backend | API Python/FastAPI et calculs normalisés |
| Frontend | React/TypeScript, français, responsive et accessible |
| Conteneurs | Images compatibles ARM64, versions identifiables |
| Compose | Services, volumes persistants, redémarrage, contrôles de santé et ports documentés |
| Configuration | Exemple sans secrets ; paramètres réellement pris en charge |
| Données | Emplacement SQLite, migrations, rétention et procédure de sauvegarde |
| Recette | Tests de calcul, qualité des mesures et absence de commandes en V1 |

## Séquence du futur premier déploiement

1. Choisir une version ou un commit identifié.
2. Vérifier la documentation de cette version et son exemple de configuration.
3. Créer les secrets uniquement sur le RPi ; limiter leurs permissions.
4. Vérifier les volumes persistants sur NVMe et les ports accessibles.
5. Démarrer **en simulation**, avec les commandes réellement livrées avec l’application.
6. Faire la [recette V1](07-Validation.md).
7. Activer ensuite les sources réelles en lecture seule et vérifier les différences.

Les noms de services, ports, chemins de base de données, variables et commandes de lancement restent à définir. Un simple `docker compose up` ne fonctionnera pas dans le dépôt actuel.

## Quand le logiciel sera livré

Compléter cette page avec le fichier Compose exact, la version des images, l’URL locale d’accès, les paramètres obligatoires, les résultats attendus des contrôles et une procédure de retour à la version précédente. Mettre également à jour le [journal](10-Journal-installation.md).
