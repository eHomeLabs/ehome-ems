# eHome EMS 0.2.10 — Flux quotidien et fiches compactes

- Alertes enregistrées résumées sur une ligne repliable, avec nom personnalisable dans les réglages, les notifications et le journal. Renommer ne réarme pas l’alerte. Les anciennes règles restent compatibles.
- Énergie quotidienne en kWh sur le flux : solaire, maison, import/export, charge/décharge et usages, sans montant en euros. Les compteurs journaliers doivent être associés ; aucune puissance ou énergie restante n’est convertie en consommation supposée. Pour une seule batterie active, les compteurs globaux de charge/décharge sont utilisés ; avec plusieurs batteries, les valeurs ne sont pas attribuées arbitrairement à chaque batterie.
- Photovoltaïque : maximum déclaré depuis les puissances nominales des sources suivies (pas un pic mesuré), puis économie potentielle estimée à partir des kWh produits et du tarif fixe. Ce montant n’est pas une économie réelle d’autoconsommation : les exports ne sont pas déduits. Un maximum incomplet ou un tarif manquant est signalé.
- F1ATB : synthèse visuelle cumulus avec puissance, kWh du jour, progression et coût estimé avant les cartes Ouverture et Forçage restant, comme la synthèse de la borne VE. La progression représente un objectif électrique, pas une réserve de chaleur.

Mise à jour HACS / Marketplace, redémarrage HA Core puis rechargement du navigateur. Interface et Intégration : 0.2.10. Associations, alertes et objectifs conservés ; aucune commande déclenchée par la mise à jour.
