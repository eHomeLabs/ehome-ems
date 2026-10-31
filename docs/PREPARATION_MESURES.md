# Préparation après b10 — périmètres et contexte d'export

Branche de travail : `codex/measurement-budget-preparation`. Aucun nouveau ZIP,
aucun changement de version et aucun changement du fonctionnement de la b10.
Les fonctions ci-dessous sont pures et ne sont pas appelées par l'intégration,
le dashboard ou le simulateur. Aucun service matériel n'est exposé ou invoqué.

## Capteur maison et total des usages

Le capteur existant reste intact, avec son périmètre et son historique.
Le prototype `measurement_context.home_total` calcule séparément un total :

- Source déclarée totale : la valeur est conservée, sans ajouter les sous-compteurs.
- Source déclarée hors usages : ajout des seules puissances explicitement exclues.
  Exemple simulé : maison hors ECS 500 W + ECS 700 W = total maison 1200 W.
- Bilan EMS AC : total déjà calculé, sans rajouter le cumulus ou les autres usages.

Schéma de préparation `home_boundary` pour une source existante :

```json
{
  "mode": "excludes_usages",
  "confirmed": true,
  "excluded_usage_ids": ["heater"],
  "disjoint_confirmed": true
}
```

`heater` représente un identifiant stable du module Usages, pas un identifiant
réel de capteur. La confirmation doit décrire un périmètre AC de charges maison,
hors charge des batteries. Pour `mode: total`, la liste des exclusions est vide.
Les usages exclus doivent être distincts physiquement et absents de la source
maison. Les doublons d'identifiants/sources sont détectés ; les recouvrements
physiques de compteurs différents ne peuvent pas être devinés et demandent
une confirmation guidée. Aucune source absente ne devient zéro.

Une future intégration devra exposer le total reconstruit séparément du capteur
existant, avec origine et composants, sans changer silencieusement sa valeur
ou ses identifiants. Ce schéma n'est pas encore proposé dans l'assistant b10.

## Fraîcheur et cohérence

Chaque source est fournie au prototype avec sa valeur, son unité et sa date de
publication (future adaptation depuis `last_reported`). `last_changed` ne doit
pas être utilisé : une puissance stable peut être régulièrement republiée.

- Pas de date ou date naïve : âge inconnu, calcul refusé.
- Date future : refus ; aucune hypothèse sur un décalage d'horloge.
- Âge au-delà du maximum : source périmée. Maximum par défaut 300 s,
  paramétrable de 30 à 3600 s, borne incluse.
- Dates converties en UTC avant comparaison, y compris pendant le changement
  d'heure ; une heure locale répétée ne rend pas une vieille mesure fraîche.
- Écart de publication des sources : 30 s maximum par défaut, paramétrable.
  Cela ne certifie pas la simultanéité de leur échantillonnage physique.

Le contexte utilise le bilan AC déclaré (PV, import, injection et toutes les
batteries actives AC) et le total maison. Le résidu est affiché ; au-delà de
50 W par défaut, le contexte est refusé. La tolérance est réglable et uniquement
diagnostique : ce n'est ni une marge de sécurité ni une puissance disponible.
Les topologies DC actives et les sources réutilisées à plusieurs rôles bloquent
ce premier modèle. Les batteries de secours restent hors du bilan quotidien.

## Export observé, scénario et puissance réallouable

`export_context` conserve séparément :

- `export_observed_w` : puissance d'injection lue et normalisée, si fraîche.
- `home_total_w`, `balance_residual_w`, `report_span_seconds` : diagnostics.
- `scenario_export_ceiling_w` : référence entière issue du seul export observé,
  arrondie vers le bas, uniquement si les contrôles sont satisfaits.
- `reallocatable_power_w` : toujours indisponible dans ce prototype.
- `commands_allowed` : toujours faux.

La référence d'export n'est PAS un budget opérationnel ni une consigne. Elle
n'est pas envoyée à la simulation b10. Toute future reprise dans un scénario
demandera une action explicite et l'affichage de sa date et de ses limites.

Exemple : 200 W exportés, 1000 W de charge batterie et 700 W vers l'ECS ne
deviennent jamais 1900 W disponibles. Seuls les 200 W d'export peuvent constituer
la référence du scénario ; la puissance réallouable reste inconnue. Avec zéro
export et une batterie en charge, la référence d'export reste zéro.

Une décharge batterie positive pendant l'injection bloque cette référence pour
ne pas certifier une origine solaire. Import et injection simultanés sont
également refusés par ce premier contexte ; cela peut être légitime sur certaines
installations triphasées et demandera un modèle adapté, pas une correction à zéro.
Le seuil d'animation de 10 W ne joue aucun rôle dans ces contrôles : même 1 W
normalisé de décharge ou d'import peut signaler une ambiguïté. La précision
numérique reste celle de la normalisation de puissance existante (deux décimales).

## Suite à raccorder après retour des tests b10

1. Assistant de déclaration du périmètre et conservation de ses options.
2. Adaptateur HA pour dates de publication, paramètres et diagnostics FR/EN.
3. Total maison distinct, sans casser les sources ni les entités existantes.
4. Présentation de l'export daté et reprise explicite dans un scénario manuel.
5. Contraintes de réserve SOC, besoins, échéances et régulations natives avant
   d'envisager une vraie puissance réallouable ou une orchestration.

La préparation ne valide pas encore ces interfaces HA ou les topologies physiques.
Les tests utilisent uniquement des sources simulées et la bibliothèque standard.
