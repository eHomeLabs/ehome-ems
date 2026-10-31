# Feuille de route eHome EMS V2

Le périmètre produit V2 remplace la feuille de route V0.1 à V0.5. Les numéros des futures releases seront attribués selon les livraisons réelles. Le code actuel reste V0.1.

## Lot A — Socle visuel

Assistant guidé, réseau/PV/maison et batteries, normalisation, flux, jauges, statistiques et personnalisation du dashboard. Lecture seule.

Acceptation : unités et signes vérifiés ; bilan cohérent sur mesures synchronisées avec tolérance documentée ; batterie de secours exclue par défaut ; données indisponibles visibles ; associations rechargeables sans redémarrer HA ; aucune commande ; personnalisation conservée.

Premières tâches : auditer le prototype, détailler les écrans et le schéma des données, prototyper la génération et la distribution frontend, vérifier les topologies supportées, puis valider sur RPi4 avec SSD.

## Lot B — Compréhension

Coûts, historiques comparés, prévisions externes, consommation estimée et conseils déterministes.

Acceptation : tarifs vérifiés sur données de référence ; origine batterie incertaine signalée ; prévisions facultatives ; hypothèses et erreurs réel/prévu visibles ; économies simulées séparées des résultats mesurés.

## Lot C — Orchestration

Simulation puis pilotage explicite ECS, batterie et VE selon les capacités exposées. Priorités, réserves, échéances, temporisations et arbitrage unique. Coordination avec F1ATB et les EMS existants.

Acceptation : aucune commande en observation/simulation ; pas de double allocation ; forçages et priorités respectés ; retour d'état vérifié ; repli sur données périmées et restitution après pause testés.

## Lot D — Optimisation

Profils de consommation, scénarios et planification avancée facultative.

Acceptation : comparaison à une stratégie de référence ; calcul mesuré sur RPi4 ; fonctionnement du socle sans moteur avancé.

## Décisions de conception

Priorités saisonnières, objectif coût ou autonomie, réserve batterie, périmètre des mesures, limites réelles des usages et topologies AC/DC du premier lot restent à fixer avant leur implémentation.

[Lire le cahier des charges complet](CAHIER_DES_CHARGES.md)
