# eHome EMS 0.2.1

La 0.2.1 consolide le socle de la b15 validé en usage : observation énergétique, Conso Maison, appareils, stockage, tendances, historique 24 h et scénarios manuels. Aucune commande physique n'est ajoutée.

## Cette version

- Version commune 0.2.1 pour backend, panneau, tests, archive et publication ; sortie du canal de préversion, périmètre d'observation inchangé.
- Documentation et wiki réécrits pour l'intégration HA actuelle ; anciens parcours de serveur autonome supprimés.
- Illustrations maison jour/nuit visibles dans leur page, le README et le wiki ; captures réelles de l'interface avec données simulées.
- Guides corrigés : réseau signé ou séparé, cumul vers énergie quotidienne, température du cumulus, icônes natives, tendance unique et courbes 24 h.
- Règles de rechargement explicites : réglages sans redémarrage global ; installation ou nouvelle version Python avec redémarrage de HA Core.

## Mettre à jour depuis la b15

Installer 0.2.1 en conservant l'entrée existante, redémarrer Home Assistant Core une fois, puis recharger le navigateur. Les associations et identifiants sont préservés ; aucun changement de schéma de configuration. Vérifier Interface 0.2.1 et Intégration 0.2.1 dans Configuration.

[Installation et retour arrière](INSTALLATION.md) · [Revue et validation](REVUE_0_2_1.md) · [Wiki illustré](wiki/Home.md)

Le suivi de l'origine solaire du stock batterie, les tarifs avancés, les prévisions énergétiques et le pilotage coordonné restent à développer. La release ordinaire 0.2.1 ne vaut pas validation officielle HACS / Marketplace.
