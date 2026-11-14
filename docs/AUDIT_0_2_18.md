# Audit de consolidation 0.2.18

Référence initiale : branche `eHome`, commit `35230473cfa0447e123495401e4a68dc7abed004`.

## Développements existants

| PR | État au début de l'audit | Réutilisation |
| --- | --- | --- |
| #17 | Fusionnée (`f832dc6`) | Compteur Énergie Maison et documentation des périmètres ; pas de nouveau compteur concurrent |
| #19 | Fusionnée (`6dcc378`) | Suivi VE persistant, calculs de session, tarifs et puissance maximale conservés |
| #21 | Fusionnée (`3523047`) | Cycle ECS, météo HC, compteur stable, forçages et protections conservés |
| #22 | Ouverte en brouillon (`9a299a6`) | Branche intégrée dans la branche de release ; tableau horaire et validation des données complétés |

Les 23 branches distantes ont été recensées. Les branches `codex/b12…b15`, `codex/v0.2.*`, `codex/v2-measurement-foundation` et `codex/measurement-budget-preparation` contiennent l'historique de fondation. Les branches `codex/v027…v0211`, `codex/energy-goal-deadline`, `codex/f1atb-native-http`, `codex/temperature-helper-storage`, `feature/home-consumption-energy`, `feature/ev-session-cost-peak`, `fix/restore-sensor-ha-2026` et `fix/cumulus-stable-counter` ont été comparées à la base et aux commits de consolidation. Plusieurs restent non ancêtres après fusion squash : ce statut Git n'implique pas l'absence de leurs fonctions. Aucun ensemble ancien n'a été fusionné aveuglément. Seule #22 apporte le développement ouvert restant à intégrer.

## Vérifications énergétiques

Les tests existants vérifient la convention import positif/export négatif, l'équivalence réseau signé/séparé, la charge réseau, l'export batterie, l'absence de doubles comptes des sous-compteurs et l'exclusion DC du bilan AC. Les sources invalides ne deviennent pas zéro. Les compteurs Maison conservent leur identifiant et leur restauration. Les écarts historiques cités dans #17 ne peuvent pas être réconciliés sans les mêmes sources/périodes ; aucune correction arbitraire des kWh n'est appliquée.

Le plan de simulation n'envoie pas de commande et n'alloue que le budget positif saisi. Aucune stratégie de décharge batterie n'est introduite. Le nouveau budget batterie exclut la réserve et le minimum natif déclaré ; les protections natives restent nécessaires pour les commandes indépendantes d'eHome.

## Corrections de livraison

- Deux chemins pouvaient publier en concurrence, dont un sans attendre les contrôles : suppression du workflow de publication concurrent.
- L'artefact et les notes étaient figés en 0.2.11 : paquet de la version du manifest, empreinte SHA-256 et notes correspondantes.
- La découverte unittest ignorait les fonctions de test météo et VE : exécution pytest de toute la suite et de tous les fichiers JavaScript.
- Champs numériques HA sérialisables ; validation des booléens, valeurs infinies et hors limites conservée côté serveur.
- Publication après les jobs HA simulé, navigateur, documentation et archive. Fusion uniquement après contrôle des statuts du commit proposé.

Voir [les fonctions et limites de la release](RELEASE_0_2_18.md).
