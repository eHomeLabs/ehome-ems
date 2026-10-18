# 06 — Préparer les sources et les mesures

[Accueil](Home.md) · [Précédent](05-Deploiement-EMS.md) · [Suite : validation](07-Validation.md)

> **Préparation fonctionnelle.** Le format de configuration et les adaptateurs ne sont pas encore implémentés. Les tableaux ci-dessous sont un aide-mémoire, pas un fichier à importer.

## Ordre de mise en service

1. Données simulées, sans accès aux équipements.
2. Home Assistant en lecture seule sur le réseau local.
3. MQTT ou API directes selon disponibilité, avec validation appareil par appareil.

Le RPi4 continue à héberger Home Assistant OS ; aucune migration vers le RPi5 n’est requise.

## Préparer Home Assistant

Relever **localement** l’adresse de HA et les entités utiles avec leur unité, fréquence, sens et disponibilité. Ne pas publier l’inventaire réel dans Git.

Lors de l’intégration, utiliser un compte dédié non administrateur si possible et examiner ses permissions effectives. Un jeton longue durée n’est pas, par sa seule création, un jeton « lecture seule ». L’adaptateur V1 devra exclure les appels de service et toute écriture.

Les API officielles utilisent un jeton : REST via l’en-tête Authorization, WebSocket via un échange d’authentification. REST peut lire les états ; WebSocket peut recevoir les changements d’état. Le secret restera côté backend, jamais dans le navigateur ou dans les journaux. Sources : [REST](https://contributors.home-assistant.io/core/internals/rest-api/), [WebSocket](https://contributors.home-assistant.io/core/internals/websocket-api/).

Ne créer ni stocker de jeton avant que l’adaptateur et la gestion des secrets soient prêts.

## Table de correspondance à préparer

| Mesure métier | Unité cible | Question à résoudre |
| --- | --- | --- |
| Production photovoltaïque | W | Valeur totale ou somme de sous-ensembles non recouvrants ? |
| Consommation maison | W | Mesurée directement ou calculée ? |
| Import réseau | W | Entrée depuis le réseau, distincte de l’export |
| Export réseau | W | Sortie vers le réseau, distincte de l’import |
| Batterie : charge / décharge | W | Deux valeurs ou une puissance signée à convertir ? |
| Batterie : état de charge | % | Une mesure par batterie, pas une somme des pourcentages |
| Énergies cumulées | Wh | Compteur cumulatif, journalier ou valeur calculée ? |
| Chauffe-eau / borne VE | W et Wh si disponibles | Sous-compteurs déjà inclus dans la consommation maison ? |

Une conversion kW → W ou kWh → Wh multiplie par 1 000. La puissance décrit un instant ; l’énergie décrit une quantité accumulée. Toute mesure doit garder sa date, sa source et son état de qualité.

## Décisions avant connexion réelle

- Choisir une mesure de référence pour le réseau et pour la maison.
- Vérifier les conventions de signe sur des situations observables.
- Identifier les sous-compteurs déjà inclus dans un total.
- Définir le seuil de péremption par source, selon sa cadence réelle.
- Définir le comportement en cas de valeur absente : ne pas la remplacer silencieusement par zéro.
- Conserver les timestamps en UTC et afficher l’heure locale ; vérifier les journées lors des changements d’heure.
- Définir la fréquence d’acquisition et la rétention avant d’accumuler des historiques.

**Exemple fictif :** si la mesure « maison » comprend déjà le chauffe-eau, ajouter sa puissance à ce total compterait deux fois le même usage. Le sous-compteur sert à expliquer le total.

## Intégrations directes

Pour chaque appareil ciblé, documenter protocole réellement accessible, mode local/cloud, authentification, limites et qualité des données. Ne pas déduire la compatibilité d’un modèle de celle d’un autre. Avec MQTT en V1, prévoir des droits limités aux sujets nécessaires et aucune publication sur les sujets de commande.
