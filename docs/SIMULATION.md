# Priorités et scénarios manuels — 0.2.1

Dans Stratégie, un administrateur peut préparer une répartition hypothétique
entre les usages configurés et les batteries actives AC. Les batteries de secours
et DC sont exclues de cette première version. Aucun équipement n'est inclus
par défaut ; cela ne change pas son fonctionnement réel.

## Préparer et exécuter un scénario

1. Cocher les équipements à inclure dans le scénario, sans les activer physiquement.
2. Déclarer un minimum et un plafond en watts entiers. Pour une charge hypothétique
   tout-ou-rien de 1800 W, mettre minimum = plafond = 1800 W. Pour un équipement
   modulable, les limites représentent seulement l'hypothèse choisie : ses capacités
   matérielles ne sont pas vérifiées par ce formulaire.
3. Déplacer les lignes avec Monter/Descendre : la première ligne est prioritaire.
4. Enregistrer explicitement les priorités. Les autres associations EMS sont
   conservées ; l'entrée se recharge sans redémarrage complet de HA.
5. Saisir un budget hypothétique en W puis Simuler ce budget. Un budget nul est
   permis. Les limites et budgets sont compris entre 0 et 1 000 000 W ; ce plafond
   logiciel n'est pas une puissance admissible pour l'installation.

Les valeurs non enregistrées désactivent le bouton de simulation. Un lecteur
peut simuler un budget avec les paramètres enregistrés, sans les modifier.
Le serveur vérifie les droits d'écriture, la révision de la configuration,
les identifiants d'équipements, les doublons et les limites. Un changement
concurrent exige d'actualiser ; les anciennes données ne sont pas écrasées.

## Algorithme et exemple

Chaque équipement inclus reçoit au plus son plafond, dans la limite du budget
restant. Si ce reliquat est inférieur à son minimum, il ne reçoit rien et le
suivant est examiné. Un équipement exclu ne consomme pas de budget. Le même watt
n'est pas attribué deux fois ; le reliquat non attribué reste affiché.

Exemple : budget 2100 W, batterie prioritaire plafonnée à 1000 W, ECS de minimum
800 W et plafond 1800 W : batterie 1000 W, ECS 1100 W, reliquat 0 W. Avec ECS
prioritaire et un budget de 500 W, elle est ignorée (minimum 800 W) et la batterie
peut recevoir les 500 W. Cela décrit uniquement le calcul du scénario.

Le résultat explique pour chaque ligne : exclusion, budget épuisé, minimum
non atteint, plafond atteint ou allocation partielle. Le panneau de droite
de la Vue d'ensemble rappelle les priorités de simulation enregistrées.

## Ce que le résultat ne signifie pas

Le budget saisi n'est pas l'injection réseau ni une estimation automatique de
puissance réallouable. Les mesures instantanées ne servent pas à fabriquer ce
budget. Le scénario peut être étudié même si une source est indisponible ; il ne
prétend alors décrire aucune situation réelle. Ne pas appliquer son résultat
comme consigne au matériel.

Les allocations sont des montants théoriques, pas des incréments à additionner
aux consommations ou aux consignes en cours. Aucune puissance mesurée n'est
automatiquement ajoutée ni soustraite au budget. Au plus 100 cibles sont traitées.

SOC, réserve batterie, échéances, pertes, topologie complète, temporisations,
hystérésis, état des équipements et régulations natives ne sont pas encore des
contraintes de ce premier répartiteur. Il ne coordonne pas F1ATB, Zendure ou
un EMS existant et ne remplace aucun de leurs automatismes. L'EMS reste en observation.
Aucune commande de service matériel n'est envoyée.

## Conservation et journal

Les priorités et limites sont enregistrées dans les options de l'entrée HA.
Elles survivent aux rechargements et sont conservées lors du parcours de
modification des capteurs. Un équipement retiré du suivi disparaît du prochain
scénario ; un nouvel équipement est ajouté exclu par défaut. Les noms proviennent
du suivi EMS, jamais d'un nom fourni par le client pour la simulation.

Le journal conserve au plus 20 résultats en mémoire pour cette entrée. Il est
partagé entre les utilisateurs autorisés à consulter la vue, survit aux simples
rechargements, mais est perdu au redémarrage HA ou au retrait de l'entrée.
Chaque résultat garde son heure, son budget, l'ordre et les limites utilisés.
Ce sont des scénarios manuels, pas des décisions exécutées ni des économies.

## Validation

Tests : conservation du budget, bornes, minimum non atteint, priorité, exclusion
secours/DC, paramètres invalides et changements concurrents ; aucun envoi de
commande ; refus d'écriture pour les lecteurs ; journal borné et conservé sur
reload ; modification, déplacement, sauvegarde et simulation dans Chromium
mobile/desktop. La validation physique du pilotage ne fait pas partie de ce lot.

