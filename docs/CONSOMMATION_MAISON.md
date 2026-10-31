# Consommation maison : source existante ou calcul EMS

Disponible à partir de la bêta 0.2.0b3, en observation.

La consommation maison est la puissance utilisée à cet instant par l'ensemble
des usages : éclairage, électroménager, chauffage, chauffe-eau, piscine, véhicule,
etc. Elle s'exprime en W/kW. L'énergie sur une période s'exprime en Wh/kWh :
ce n'est pas le champ demandé ici. La charge batterie est un flux séparé.

## Capteur existant

Choix par défaut, conservé pour les anciennes configurations. Une mesure directe
du total ou un capteur template déjà calculé convient. EMS en reprend la valeur
sans refaire un bilan par-dessus. Ce capteur ne doit pas dépendre du capteur
Maison produit par EMS.

Un compteur ou des pinces mesurant la puissance de tous les usages, ou la somme
cohérente de sous-compteurs, peut fournir ce total. Le périmètre physique compte
plus que la marque du compteur. Une pince sur l'arrivée réseau peut ne mesurer
que l'échange réseau : elle ne donne alors pas seule les usages alimentés aussi
par le photovoltaïque ou la batterie.

## Calcul automatique EMS

Le premier moteur applique un bilan AC :

P maison = P solaire + P import + somme P décharge − P injection − somme P charge.

Exemple : 719 W solaire, 0 W import, 47 W injection, 247 W charge et 0 W décharge
donnent 425 W pour les usages.

Sélectionner Calculer automatiquement dans eHome EMS dans l'écran Maison.
Le champ de source maison est alors ignoré. Le capteur EMS garde son identifiant
unique en changeant de mode.

Conditions :

- Import ET injection : deux sources distinctes. Le réseau signé seul n'est pas
  encore utilisé par le calcul, faute de convention de signe configurée.
- Présence réelle du PV déclarée, avec puissance AC totale s'il est présent.
- Présence réelle de stockage actif déclarée ; toutes les batteries participant
  aux flux quotidiens ajoutées avec le rôle actif.
- Charge ET décharge de chaque batterie active mesurées côté AC. Une puissance
  interne pack/DC n'est pas interchangeable avec une puissance AC.
- Même périmètre de mesure, sans double compte de production ni de stockage.
  Cette cohérence doit être explicitement confirmée.

Les batteries actives DC bloquent le calcul AC simple. Pour un système hybride ou
une topologie différente, conserver un capteur maison existant adapté.
Les batteries de secours sont hors de ce bilan quotidien. Si elles alimentent
les usages au quotidien, revoir leur rôle et leur périmètre ; ne pas les exclure
pour contourner une mesure manquante.

Déclarer un module absent signifie zéro pour ce module uniquement. Ne pas déclarer
absent un équipement réellement présent pour contourner une mesure manquante.

## Données manquantes et fraîcheur

Une source requise absente, indisponible, de mauvaise unité, non numérique ou de
signe inattendu rend le résultat indisponible. Un bilan négatif est également
indisponible (negative_balance), sans être ramené artificiellement à zéro.

L'âge maximal des sources est réglable de 30 à 3 600 s, 300 s par défaut, à partir
de la dernière publication d'état HA (last_reported). Le contrôle est réévalué
toutes les 30 s et à chaque changement. Adapter l'âge pour les appareils qui ne
publient qu'en cas de variation. La fraîcheur ne garantit pas la synchronisation :
des écarts transitoires restent possibles.

L'attribut value_origin distingue external_source et calculated. Lorsque le
capteur est disponible, les sources et la qualité du calcul sont exposées.
HA peut masquer les attributs d'un capteur indisponible.

Ce bilan calcule une puissance, pas l'origine solaire du stock batterie, un taux
d'autonomie ni une énergie journalière.
