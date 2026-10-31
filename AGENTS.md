# eHome EMS — Instructions de développement V2

La référence produit est [docs/CAHIER_DES_CHARGES.md](docs/CAHIER_DES_CHARGES.md), complétée par [docs/ROADMAP.md](docs/ROADMAP.md).

- Développer exclusivement une intégration Home Assistant distribuable via HACS / Marketplace ; réutiliser les intégrations HA existantes.
- Le serveur autonome RPi5, FastAPI, React et SQLite comme pile imposée sont abandonnés.
- Le code existant reste le prototype V0.1 ; ne pas présenter la V2 comme livrée et ne pas changer sa version pour une modification documentaire.
- Priorité au lot A en lecture seule : assistant, normalisation, flux, jauges et statistiques.
- Aucun pilotage en observation ou simulation. Activation explicite par équipement pour le futur mode automatique.
- Ne jamais modifier une instance HA réelle sans autorisation explicite.
- Ne jamais committer de secrets, jetons, URL privées ni inventaires réels d'identifiants d'entités.
- Distinguer W/kW, Wh/kWh, SOC, import/export, charge/décharge, mesure/calcul/estimation et qualité des données.
- Prévenir les doubles comptes, respecter les topologies AC/DC et afficher les valeurs indisponibles ou périmées.
- Ne pas assimiler toute décharge batterie à du solaire. Séparer surplus exporté et puissance réallouable.
- Préserver les personnalisations du dashboard, les automatismes existants et les régulations natives.
- Backend Python asynchrone, frontend adapté à HA, interfaces publiques, reload/unload propres et identifiants stables.
- Fonctionnement local de base, aucun solveur lourd ni IA distante obligatoire ; cible de validation RPi4 avec SSD.
- Interface responsive et accessible, français prioritaire et structure de traduction anglaise.
- Utiliser des données simulées pour les tests significatifs : signes, unités, bilans, statistiques, arbitrage, migrations et repli.
- Vérifier les liens et la cohérence pour les modifications documentaires ; ne pas lancer des tests matériels pour celles-ci.
