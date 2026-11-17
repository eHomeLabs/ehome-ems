# Changelog

## 0.2.20

- Lit directement les compteurs journaliers, sans dépendance à History.
- Utilise un état cumulatif inchangé depuis avant minuit comme référence valide pour 0 kWh aujourd’hui.
- Affiche le coût quotidien de la borne dans la vue d’ensemble, distinct des sessions.

Détails : [release 0.2.20](docs/RELEASE_0_2_20.md).

## 0.2.19

- Supprime le blocage ECS basé sur l’âge des rapports du compteur cumulatif.
- Conserve la dernière valeur connue pour information en cas d’indisponibilité, sans l’utiliser pour commander.
- Maintient les suspensions sur source invalide, compteur en baisse et historique absent.
- Retire le réglage d’ancienneté de l’éditeur ECS ; conserve les réglages existants.

Détails et mise à jour : [release 0.2.19](docs/RELEASE_0_2_19.md).

## 0.2.18

- Consolide les développements ECS/F1ATB et sessions VE existants, réutilise la PR #22 pour les prévisions horaires.
- Ajoute jauges jaunes configurables, synthèse et voyants de disponibilité HA aux appareils.
- Ajoute réserve batterie 30 % / seuil minimal 10 % et budget au-dessus du seuil le plus élevé, sans commande batterie ni basculement électrique.
- Filtre les sources metering par métadonnées HA, groupe par appareil et permet d'élargir la liste compatible.
- Affiche le tableau météo horaire, conserve les historiques et associations.
- Supprime la publication concurrente ; génère archives et empreintes de la bonne version après tests complets.
- Exécute tous les tests Python et JavaScript dans les workflows de livraison.

Détails, limites et mise à jour : [release 0.2.18](docs/RELEASE_0_2_18.md).
