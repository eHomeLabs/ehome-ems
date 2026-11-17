# eHome EMS 0.2.19 — Compteurs stables et disponibilité

Le complément ECS/F1ATB ne se bloque plus après 300 secondes sans nouveau rapport du compteur d’énergie. Une valeur cumulative numérique en Wh/kWh reste exploitable tant que Home Assistant la fournit. La disponibilité des appareils reste fondée sur leurs états HA, sans exiger un changement de metering.

La solution retenue utilise la dernière mesure valide de Home Assistant, sans dépendance à `last_seen` de Zigbee2MQTT : toutes les intégrations sont compatibles. Une valeur conservée par HA ne prouve pas une communication récente ; activez la disponibilité native de votre intégration pour détecter les appareils déconnectés. EMS ne déduit plus une panne du seul âge d’un compteur cumulatif.

Si la source devient absente, `unknown`, `unavailable` ou invalide, le complément est suspendu. La dernière valeur du compteur mémorisée depuis le chargement est affichée séparément, uniquement pour information : elle ne remplace jamais une source indisponible dans les calculs ou commandes. Une baisse du compteur, une référence de cycle absente ou un historique inexploitable continuent de bloquer le complément.

Le champ d’ancienneté du compteur est retiré de l’éditeur d’objectif. Son ancienne valeur est conservée pour compatibilité et n’est plus utilisée. Les contrôles de fraîcheur des puissances du bilan Maison restent indépendants. Aucune puissance ancienne n’est intégrée en énergie par ce correctif.

Les baux F1ATB courts, les fenêtres autorisées, l’échéance, la relecture des commandes, les priorités manuelles et le thermostat natif sont conservés. Aucune commande sur une installation réelle n’a été exécutée pour les tests.

## Mise à jour

Dans HACS, actualiser les informations du dépôt puis installer **0.2.19** et redémarrer Home Assistant. Vérifier la version affichée et l’objectif ECS existant ; aucun changement des associations ou activation automatique supplémentaire n’est nécessaire.

À vérifier sur votre installation : compteur stable plus de 300 s sans blocage ; arrêt du complément lorsque la source passe réellement indisponible ; reprise après retour de la source et arrêt à l’objectif.
