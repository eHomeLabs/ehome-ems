# eHome EMS 0.2.6 — Objectifs énergétiques avant échéance

Définissez l’énergie à fournir au cumulus, l’heure d’échéance et un créneau autorisé pour le complément réseau. Exemple : 3 kWh visés, 1 kWh reçu, 2 kWh manquants, soit environ 67 minutes à 1 800 W.

- Cycle conservant les apports avant minuit ; référence issue du compteur cumulé dédié et de Recorder.
- Observation par défaut ; complément automatique F1ATB HTTP uniquement après activation explicite.
- Forçages courts de 1 à 2 minutes, retour Auto à la cible, priorité manuelle, suspension sur données absentes, anciennes ou compteur remis à zéro.
- Configurations existantes conservées. Aucun objectif personnel activé par la mise à jour.

Mettre à jour depuis HACS / Marketplace, redémarrer Home Assistant Core puis recharger le navigateur. Vérifier Interface 0.2.6 et Intégration 0.2.6. Ne pas supprimer l’entrée existante.

Validation de la fonctionnalité : 185 tests Python, 19 tests frontend, parcours desktop/mobile, Home Assistant 2026.9.1 et 2026.11.0b0, Recorder SQLite temporaire et routeur simulé. Aucun essai matériel réel. L’objectif mesure l’énergie électrique consommée, sans garantir la réserve d’eau chaude restante.

[Guide et limites](OBJECTIFS_ENERGIE.md) · [Installation](INSTALLATION.md)
