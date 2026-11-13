# Stratégie ECS — v0.2.17

## Configuration de référence

- Objectif du cycle : **3 kWh** ; cycle de **07:00 à 07:00** (fuseau HA).
- Compteur cumulatif : `sensor.sem_cumulus_energy` (Wh/kWh, sans remise à zéro à minuit).
- Puissance du cumulus : **1 800 W** ; mesure indépendante `sensor.sem_cumulus_power` (W).
- Complément nocturne autorisé : **01:00–07:00**, marge 5 min.
- F1ATB : connexion HTTP locale, marche forcée à 100 %, thermostat et protections matériels inchangés.

## Complément météo (optionnel)

Dans Stratégie → Configurer l'objectif, activer **Complément météo en heures creuses** et choisir une entité `weather.*` proposant les prévisions horaires HA. Définir **12:30–14:30** et **0,5** pour 50 %. En cas de pluie ou ciel couvert prévus vers 12:30, le moteur vise **1,5 kWh reçus depuis 07:00**, et non 1,5 kWh supplémentaires. Si le cumul atteint déjà 1,5 kWh, il ne commande rien. Si les prévisions horaires sont absentes ou inconnues, aucun complément météo n'est autorisé.

La stratégie nocturne vise ensuite les **3 kWh totaux** avant 07:00, en conservant l'énergie déjà reçue. La journée civile depuis minuit reste une statistique distincte.

## Forçage manuel

- **30 min** et **1 h** : marche forcée F1ATB à 100 %, temporisée et vérifiée par relecture. L'automatique est suspendu pendant le forçage, puis reprend.
- **Full** : pilotage jusqu'à l'objectif kWh du cycle ou jusqu'à 07:00, avec commandes F1ATB limitées à des baux renouvelés de deux minutes. Nécessite le mode automatique et un compteur exploitable ; ne signifie pas une chauffe permanente ou une mesure directe de température.

## Sécurités

Un compteur cumulatif immobile hors chauffe n'est pas nécessairement en panne. Si sa dernière valeur est ancienne, l'EMS n'autorise un **premier bail bref** que si la puissance réelle du cumulus est disponible, récente et confirme l'arrêt (moins de 100 W, tolérance -5 W). Une fois le cumulus en chauffe, le compteur d'énergie doit de nouveau communiquer ; sinon l'EMS cesse de renouveler la commande. Compteur absent, historique de cycle manquant, remise à zéro, puissance inconnue ou routeur non confirmé : aucune nouvelle chauffe automatique.

**Test conseillé :** commencer avec le mode observation, vérifier les valeurs du cycle et les prévisions, puis activer l'automatique avec une surveillance locale du F1ATB. Ne pas tester la marche forcée sans vérifier la configuration électrique et les protections du cumulus.
