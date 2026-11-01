# Validation 0.2.2

La passe complète de consolidation 0.2.1 reste dans [son rapport historique](REVUE_0_2_1.md). La présente version ajoute quatre comportements ciblés : libellé de tendance, tolérance négative sur usages, objectif quotidien et commande On/Off manuelle.

## Contrôles

- 149 tests Python : bornes −5 W, conversions W/kW, refus au-delà de la tolérance, absence de correction sur les autres rôles, attribut de valeur brute, validation des objectifs et commandes manuelles.
- 19 tests JavaScript : pourcentage 2,16 / 3 = 72 %, absence de données, objectif dépassé, historique et formatage.
- Chromium desktop/mobile : action On puis Off sur fixture simulée, état indisponible désactivé, carte cumulus à 72 %, alignement et régressions des autres vues.
- La CI exécute les instances temporaires HA 2026.9.1 et 2026.11.0b0 : commande simulée, contexte utilisateur, rejet d’état/révision obsolètes, refus des lecteurs non administrateurs et absence de commande par observation/simulation.
- Archive de 26 fichiers, incluant le module de commande manuelle ; liens documentaires contrôlés et captures régénérées.

Le module de commande n’accepte ni nom de service ni entité arbitraire dans la requête : il résout la cible enregistrée et activée. Les commandes ne sont déclenchées que par l’action manuelle de l’utilisateur. Aucune installation personnelle ni aucun appareil physique n’a été utilisé pour ces tests. Les résultats effectifs de la CI sont associés au commit/tag de publication.

L’objectif du cumulus mesure une consommation quotidienne relative à un seuil déclaré ; les soutirages et pertes thermiques ne sont pas modélisés. Les SOC des batteries restent mesurés, sans substitution par un objectif.

[Notes 0.2.2](RELEASE_0_2_2.md) · [Usages et commandes](USAGES_OBSERVATION.md)
