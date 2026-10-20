# Validation V0.1 — Home Assistant existant

> **Prototype non validé : ne pas installer avant revue et sauvegarde complète de Home Assistant.** Aucune commande d'équipement n'est implémentée.

## Préparation

1. Réaliser une sauvegarde complète Home Assistant et vérifier qu'elle est récupérable.
2. Relever les trois entités de puissance existantes : réseau, photovoltaïque, maison, ainsi que leurs unités et signes.
3. Contrôler qu'aucun de ces capteurs n'est une commande ou une entité de puissance cumulée en kWh.
4. Prévoir une plage de test sans opération énergétique sensible.

## Tests attendus

- L'intégration apparaît dans le menu d'ajout des intégrations.
- Le formulaire accepte une à trois sources de puissance, et refuse une configuration vide.
- Les entités créées suivent les valeurs sources en W (conversion kW si nécessaire).
- Une source indisponible ou non numérique rend le capteur EMS indisponible.
- Convention confirmée sur l'installation eHome Labs par capture HA du 18/10/2026 à 14:07 : **−711 W = injection de 711 W** ; les valeurs positives correspondent à l'importation. Le capteur brut conserve son signe.
- Prévoir pour les autres installations un paramètre de convention inversée ; **non implémenté à ce stade**.
- Modifier les associations via les options recharge les entités sans redémarrer le RPi.
- Retirer une association supprime sa production active ; vérifier l'état des anciennes entités dans le registre.
- Désactiver ou supprimer l'intégration arrête les abonnements aux événements.
- Aucun appel de service de commande et aucune modification des automatisations HA.
- Redémarrage Home Assistant Core : l'intégration restaure sa configuration.

## Limitations connues

- Découverte automatique et dashboard non implémentés.
- Aucun bilan énergétique fiable calculé à ce stade.
- Validation de compatibilité avec la version HA et HACS à effectuer.
- Une modification du code Python peut nécessiter un redémarrage de Home Assistant Core, même si le rechargement de configuration est prévu.

## Critère de passage à l'installation pilote

Revue de code, tests automatisés et validation du parcours de configuration sur une instance Home Assistant de test, puis accord explicite avant installation sur l'instance principale.

## Cartographie réelle eHome Labs — octobre 2026

| Fonction | Entité |
|---|---|
| Réseau signé | `sensor.sem_linky_power` |
| Import réseau | `sensor.import_reseau` |
| Injection réseau | `sensor.injection_reseau` |
| Production PV | `sensor.prod_solaire_additionnee` |
| Consommation maison | `sensor.conso_reelle_maison` |

**Principe de conception :** privilégier les capteurs existants ; ne calculer des capteurs dérivés que si les données nécessaires manquent. Les capteurs import/injection existants sont des candidats pour les modules ultérieurs, pas encore sélectionnables dans le formulaire V0.1 actuel. Vérifier leur unité et leur convention de signe avant utilisation.
