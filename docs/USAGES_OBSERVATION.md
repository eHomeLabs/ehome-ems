# Usages : F1ATB/ECS, recharge VE et autres charges

À partir de 0.2.0b4, une étape Usages suit les batteries. Elle permet d'ajouter,
renommer, modifier ou retirer plusieurs usages avant confirmation finale.
Les identifiants sont stables ; aucune intégration constructeur n'est supprimée.
L'étape est facultative : Continuer vers la vérification permet de l'ignorer.

## Champs

- Type : routeur solaire/ECS, recharge véhicule électrique ou autre usage.
- Puissance réellement consommée, en W/kW.
- Compteur d'énergie existant, en Wh/kWh, facultatif.
- Période réelle de ce compteur : aujourd'hui, session ou cumul total.
- État existant, facultatif : sensor, binary_sensor, switch ou select.
- Confirmation que l'usage appartient au périmètre de consommation maison.

Au moins une mesure ou un état est nécessaire. Les sources absentes, les mauvaises
unités et les doublons sont refusés. Une source indisponible reste indisponible.
Un compteur cumulé peut être suivi comme cumul : il n'est pas transformé en
consommation du jour. La période est déclarée par l'utilisateur ; les unités
seules ne permettent pas de la deviner.

## F1ATB et chauffe-eau

La puissance du compteur du cumulus peut représenter la consommation réelle.
Elle est distincte d'un pourcentage SSR, d'une consigne de puissance ou d'un
ordre de forçage. L'énergie du jour peut provenir d'un compteur journalier existant.
L'état peut représenter le routage ou un mode déjà exposé dans HA.
Ce module ne se connecte pas directement à F1ATB : il lit les entités HA choisies.

## Borne VE

Choisir la puissance consommée par la borne, plutôt que l'import réseau ou toute
la maison. L'énergie peut correspondre à la session, à aujourd'hui ou au cumul
selon le compteur associé. L'état reflète exactement la source choisie : véhicule
branché, charge en cours ou autre état ; ils ne sont pas déduits l'un de l'autre.
Ce premier module accepte un état par usage.

## Total maison et absence de commande

Ces consommations sont déjà contenues dans le total maison, qu'il provienne
d'un capteur existant ou du bilan AC. Elles ne sont jamais ajoutées une seconde
fois ni soustraites du total. Elles servent à expliquer sa répartition.
Un usage hors de ce périmètre ne doit pas être déclaré comme inclus.

Même si un switch est sélectionné pour lire son état, le miroir est un sensor
sans commande. Aucune consigne, aucun changement de mode et aucun ordre de charge
ne sont envoyés. Les automatismes du routeur et de la borne restent inchangés.
Priorités, échéances VE, puissance réglable et coordination du surplus sont des
fonctions futures, distinctes de ce suivi.

## Dashboard

La configuration exportée comprend une vue Usages avec puissance, jauge, énergie
et sa période, ainsi que l'état disponible. L'historique des puissances comprend
les sous-consommations ; il ne les additionne pas. Les jauges utilisent l'échelle
d'affichage générale, à personnaliser dans la copie du dashboard.

La copie déjà installée n'est pas mise à jour automatiquement : régénérer puis
reporter les éléments souhaités dans un nouveau dashboard.
Les bilans journaliers calculés par EMS et les flux animés restent à développer.
