# eHome EMS — Instructions de développement

La version 0.2.4 ajoute le support F1ATB HTTP natif au suivi énergétique en observation. Les références produit sont [docs/CAHIER_DES_CHARGES.md](docs/CAHIER_DES_CHARGES.md) et [docs/ROADMAP.md](docs/ROADMAP.md).

- Développer une intégration Home Assistant distribuée via HACS / Marketplace ; réutiliser les intégrations HA existantes.
- Aucun serveur autonome ni matériel dédié n'est requis. Validation de référence sur HA avec RPi4 et SSD, sans exclusivité matérielle.
- Garder la documentation alignée sur les fonctions livrées. Ne pas changer la version pour une simple correction documentaire, sauf demande explicite de release.
- Aucune commande automatique en observation ou simulation. Les commandes manuelles On/Off sont autorisées sur clic administrateur, après association et activation explicites par équipement. Le pilotage automatique reste futur.
- Ne jamais modifier une instance HA réelle sans autorisation explicite.
- Ne pas committer de secrets, jetons, URL privées ou inventaires réels d'entités ; utiliser les jeux simulés.
- Distinguer W/kW, Wh/kWh, SOC, import/export, charge/décharge, stock/cumul, mesure/calcul/estimation et qualité.
- Conso Maison = solaire + réseau signé − charge + décharge. Cumulus et borne restent inclus. Éviter les doubles comptes et respecter les périmètres AC/DC.
- Ne jamais remplacer une source invalide ou absente par zéro, ni assimiler toute décharge batterie à du solaire.
- Préserver les identifiants, personnalisations, automatismes et régulations natives ; modifications de paramètres rechargeables sans redémarrage global.
- Backend Python asynchrone, interfaces HA publiques, unload/reload propres, fonctionnement local de base.
- Interface responsive et accessible ; français prioritaire et traductions anglaises cohérentes.
- Tests simulés significatifs : signes, unités, bilans, qualité, unités de stock, historique, changements d'heure, droits, conflits et migrations.
- Pour le code, lancer les tests appropriés et les contrôles CI HA/navigateur. Pour la documentation, vérifier liens, captures et cohérence ; aucun test matériel implicite.

- Les fiches photovoltaïques sont descriptives et ne doivent pas être agrégées implicitement dans le total solaire ou le bilan Maison.
- Le support F1ATB natif utilise HTTP local sans intégration supplémentaire, ou MQTT HA selon le transport choisi. Les commandes restent manuelles et activées explicitement. HTTP : sérialisation par routeur, configuration complète préservée, contrôle de conflit avant écriture persistante et relecture sans supposer un succès. MQTT : topic explicite, messages non retenus, aucun accusé de réception supposé ni identifiant de broker dupliqué.
