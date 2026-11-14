# Changelog

## 0.2.18

- Consolide les développements ECS/F1ATB et sessions VE existants, réutilise la PR #22 pour les prévisions horaires.
- Ajoute jauges jaunes configurables, synthèse et voyants de disponibilité HA aux appareils.
- Ajoute réserve batterie 30 % / seuil minimal 10 % et budget au-dessus du seuil le plus élevé, sans commande batterie ni basculement électrique.
- Filtre les sources metering par métadonnées HA, groupe par appareil et permet d'élargir la liste compatible.
- Affiche le tableau météo horaire, conserve les historiques et associations.
- Supprime la publication concurrente ; génère archives et empreintes de la bonne version après tests complets.
- Exécute tous les tests Python et JavaScript dans les workflows de livraison.

Détails, limites et mise à jour : [release 0.2.18](docs/RELEASE_0_2_18.md).
