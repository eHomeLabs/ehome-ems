# eHome EMS 0.2.8 — Objectifs lisibles et forçage manuel

- Objectif atteint prioritaire, avertissement de rapport ancien séparé et absence d’heure de complément inutile.
- Énergie du jour (minuit) séparée de l’énergie du cycle (échéance précédente), avec historique source accessible.
- Cumul à vie retiré des fiches Usages/Appareils ; le compteur reste utilisé pour les calculs.
- Sélection d’entités par recherche et boutons tactiles, en remplacement des suggestions natives peu fiables.
- Forçage administrateur F1ATB HTTP « 1 h à 100 % », depuis Stratégie et Usages. L’ouverture de marche forcée est réglée et reste à 100 % ; elle est confirmée avant l’ordre de 60 minutes. La commande manuelle suspend l’objectif EMS sur le cycle en cours, même après retour Auto du routeur.

Mise à jour HACS / Marketplace, redémarrage HA Core puis rechargement du navigateur. Interface et Intégration : 0.2.8. Associations, alertes et objectifs conservés. Aucun appareil personnel commandé par les tests ni par la mise à jour.

[Principe, fonctionnement et limites](OBJECTIFS_ENERGIE.md)
