# eHome EMS 0.2.7

- Clic sur les valeurs pour ouvrir l’historique 24 h / 7 jours dans tous les onglets, avec accès à la fiche HA d’origine.
- Situation actuelle remplacée par un commentaire automatique sur les flux mesurés.
- Total photovoltaïque indicatif de puissance et d’énergie quotidienne avec dédoublonnage, couverture et sources explicites.
- Configuration : raccourcis Réseau, Solaire, Conso Maison et Compteurs du jour mis en évidence ; suppression de la liste de boutons Modifier redondants. Les boutons Modifier restent dans les fiches des équipements.
- Dernier onglet Alertes et Notifications : import quotidien, puissance élevée et entité indisponible, durée minimale, destination HA et journal persistant avec anti-répétition.

Mettre à jour depuis HACS / Marketplace, redémarrer Home Assistant Core puis recharger le navigateur. Vérifier Interface 0.2.7 et Intégration 0.2.7. Associations et objectifs conservés. Aucune alerte ni commande automatique activée par la mise à jour.

Les tests utilisent des données et destinataires simulés. Aucun équipement personnel n’est commandé. Voir [le guide et les limites](ALERTES_HISTORIQUES.md), notamment les compteurs du jour, les hybrides et les sources à périmètres chevauchants.
