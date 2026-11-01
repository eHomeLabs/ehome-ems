# eHome EMS — Instructions de développement

La version 0.2.1 consolide le suivi énergétique en observation. Les références produit sont [docs/CAHIER_DES_CHARGES.md](docs/CAHIER_DES_CHARGES.md) et [docs/ROADMAP.md](docs/ROADMAP.md).

- Développer une intégration Home Assistant distribuée via HACS / Marketplace ; réutiliser les intégrations HA existantes.
- Aucun serveur autonome ni matériel dédié n'est requis. Validation de référence sur HA avec RPi4 et SSD, sans exclusivité matérielle.
- Garder la documentation alignée sur les fonctions livrées. Ne pas changer la version pour une simple correction documentaire, sauf demande explicite de release.
- Aucun pilotage en observation ou simulation. L'automatique reste futur et devra être explicitement activé par équipement.
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
