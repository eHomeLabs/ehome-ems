# 02 — Prérequis et préparation

[Accueil](Home.md) · [Suite : installation](03-Installation-Home-Assistant.md)

Utiliser Home Assistant existant, version 2026.9.1 minimum. La référence de validation comprend un RPi4 avec SSD, sans matériel imposé par EMS. Les appareils doivent déjà fournir leurs entités via leurs intégrations habituelles.

| Source | Unité et précaution |
| --- | --- |
| Solaire | Total AC en W/kW ; ne pas additionner total et sous-ensembles |
| Réseau | Signé : import positif, export négatif ; ou deux capteurs séparés |
| Maison existante | Total réel des usages ; pas uniquement l'arrivée réseau |
| Batterie | Charge et décharge séparées, SOC %, stock restant Wh/kWh |
| Appareil | Puissance réelle et, si disponible, compteur d'énergie avec période connue |
| Météo | Entité `weather` HA avec prévisions quotidiennes si disponibles |

Activer la conservation des sources dans History/Recorder pour les courbes et la référence de minuit des cumuls. Prévoir une sauvegarde HA et noter les périodes des compteurs avant de lancer l'assistant. Ne pas publier les identifiants de votre installation dans le dépôt.

[Guide d'installation](../INSTALLATION.md)
