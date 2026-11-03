# eHome EMS 0.2.9 — Consommation quotidienne dans la vue d’ensemble

Chaque carte Usages et équipements affiche désormais l’énergie consommée depuis minuit en kWh et sa valorisation estimée en euros, en plus de la puissance et de la tendance sur 15 minutes.

Les calculs réutilisent le compteur associé à l’appareil : valeur du jour, ou différence depuis minuit pour un compteur cumulé avec historique Recorder. Le coût utilise le tarif fixe configuré dans Compteurs du jour et tarif ; il s’agit d’une valorisation de toute l’énergie consommée, pas de la facture d’import ni d’un coût d’achat solaire. Les valeurs manquantes ne deviennent jamais zéro ; un compteur de session ne devient pas un compteur du jour. Les kWh restent cliquables pour ouvrir l’historique source.

Mise à jour HACS / Marketplace, redémarrage HA Core puis rechargement du navigateur. Interface et Intégration : 0.2.9. Aucun changement des associations ni des commandes.
