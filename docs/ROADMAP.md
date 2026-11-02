# Feuille de route après la 0.2.3

La 0.2.3 consolide le socle d'observation validé avec la b15. Le numéro 0.2.3 ne signifie pas que tout le périmètre produit est livré.

| Domaine | Disponible | Suite envisagée |
| --- | --- | --- |
| Sources et bilan | Assistant, normalisation, Conso Maison AC, diagnostics | Topologies hybrides/DC plus complètes |
| Interface | Flux, tendances, historiques 24 h, appareils, stockage, météo | Analyses et comparaisons de périodes |
| Énergie et coûts | Compteurs du jour, différence depuis cumul, tarif fixe | Tarification avancée, bilans historiques plus complets |
| Stratégie | Priorités et scénarios manuels sans commande | Conseils explicables, prévisions énergétiques |
| Pilotage | Boutons On/Off manuels explicitement activés | Pilotage automatique avec repli et arbitrage coordonné |

## Critères avant d'aller plus loin

Conserver le socle local léger, les régulations natives et les identifiants. Ne pas attribuer automatiquement toute décharge au solaire. Pour le futur pilotage : retour d'état, temporisations, hystérésis, réserve, limites réelles, pause et restitution explicite ; un seul arbitre doit éviter les doubles allocations.

Les scénarios actuels ne valident pas un pilotage réel : ils répartissent un budget saisi manuellement. Les prévisions de production/consommation, le suivi de l'origine du stock et les économies réelles demandent des développements et validations distincts.

[Cahier des charges](CAHIER_DES_CHARGES.md) · [Fonctions actuelles](../README.md)
