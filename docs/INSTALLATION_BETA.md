# eHome EMS 0.2.0b3 — installation et retour arrière

Première bêta en observation. Le périmètre produit « V2 » n'est pas encore livré
en totalité. La bêta contient l'assistant, les mesures normalisées, le suivi
multi-batteries et l'export manuel d'un dashboard natif.

La bêta 0.2.0b3 ajoute des explications dans chaque étape et une aide par champ
pour les batteries. Une consommation maison déjà calculée est acceptée si elle
décrit les usages réels. L'énergie restante doit être un stock, pas un compteur
cumulatif. Les compteurs déclarés total/total_increasing sont refusés ; au-delà
de capacité × 1,10, l'association est signalée incohérente. Pendant le suivi, un
tel stock devient indisponible plutôt que d'être affiché comme valide.
Le champ reste facultatif : laissez-le vide si aucune source ne convient.
La création automatique du dashboard et les flux animés restent à développer.

À l'étape Maison, choisir entre une source existante et le calcul automatique EMS.
Ce dernier demande les capteurs séparés import/injection, les mesures AC des modules
présents et une confirmation du périmètre. Les sources périmées ou manquantes
rendent le résultat indisponible. Voir CONSOMMATION_MAISON.md avant activation.

## Paquet à utiliser

Dans GitHub → Actions → Home Assistant beta package, ouvrir une exécution réussie
correspondant au dernier commit de la proposition de code puis télécharger
l'artefact ehome-ems-0.2.0b3. Il contient le ZIP installable, son SHA-256 et ce guide.
Le paquet est produit seulement après succès de la validation backend HA réelle.
Les artefacts GitHub sont conservés 90 jours et peuvent être reconstruits avec
scripts/build_test_package.py ou en relançant le workflow.

Le ZIP installable contient custom_components/ehome_ems uniquement. L'archive
d'artefact GitHub est une enveloppe : extraire d'abord le fichier
ehome-ems-0.2.0b3.zip qu'elle contient.

La cible actuelle est Home Assistant Core 2026.11.0b0 et Python 3.14.
La CI vérifie aussi 2026.9.1 comme point de comparaison.
Cela ne signifie pas que le RPi4 doit être modifié pour Python : HA OS gère son
propre environnement. Aucune autre version HA n'est déclarée validée ici.

## Avant le remplacement

1. Effectuer une sauvegarde HA comprenant la configuration et les intégrations
   personnalisées ; conserver un moyen de restauration.
2. Si V0.1 est installée, conserver une copie du dossier actuel
   /config/custom_components/ehome_ems, hors de custom_components.
3. Noter ou capturer les associations de capteurs actuelles. Ne pas supprimer
   l'entrée eHome EMS : ses identifiants servent à conserver les entités existantes.

## Installation manuelle de la bêta

Le dépôt reste privé. Ce guide ne suppose pas un téléchargement direct par HACS
et ne demande aucun changement de visibilité du dépôt.

1. Extraire ehome-ems-0.2.0b3.zip sur le PC.
2. Copier son dossier custom_components/ehome_ems dans
   /config/custom_components/ehome_ems sur HA, en remplaçant le code précédent.
   Vérifier qu'il n'y a pas de niveau ehome_ems/ehome_ems imbriqué.
3. Vérifier la présence de manifest.json avec version 0.2.0b3.
4. Redémarrer Home Assistant une fois pour charger le nouveau code.
5. Si l'intégration existe déjà : Paramètres → Appareils et services → eHome EMS
   → Configurer. Les associations V0.1 sont reprises.
   Sinon : Ajouter une intégration → eHome EMS.
6. Suivre réseau → solaire → maison → batteries → vérification → confirmation.
   Pour une batterie utilisée au quotidien, choisir explicitement le rôle actif.
   Le rôle secours est proposé par défaut ; l'Aferiy peut rester en secours.

Les changements d'associations se rechargent ensuite sans redémarrage complet de HA.
Le premier chargement du code et ses mises à jour nécessitent un redémarrage.
Aucune commande d'équipement n'est envoyée par cette bêta.

## Premier essai

- Comparer réseau, solaire et maison avec leurs sources : unités et signes.
- Vérifier SOC, charge/décharge et énergie restante des batteries configurées.
- Modifier une association, confirmer et vérifier le rechargement.
- Exporter le dashboard avec ehome_ems.generate_dashboard : voir
  [le guide du dashboard](DASHBOARD_OBSERVATION.md). Utiliser un nouveau dashboard.
- Contrôler les journaux ehome_ems et signaler les erreurs avec la version HA.

Les détails de validation et limites figurent dans VALIDATION_ASSISTANT.md et
DASHBOARD_OBSERVATION.md. Le rendu sur Android, tablette et PC reste à vérifier.
Pas encore de flux animé, bilan journalier, prévision, conseil ni pilotage.

## Retour à la V0.1

1. Remplacer /config/custom_components/ehome_ems par le dossier V0.1 conservé.
2. Redémarrer Home Assistant une fois.
3. Conserver l'entrée d'intégration existante. Les clés réseau/solaire/maison
   restent compatibles ; V0.1 ignore les nouveaux réglages de batteries.
4. Les nouveaux miroirs de batteries ne sont plus fournis par V0.1 et les
   dashboards bêta qui les utilisent afficheront des entités indisponibles.
5. Pour retrouver exactement l'état antérieur, restaurer la sauvegarde HA réalisée
   avant l'installation plutôt que modifier manuellement les fichiers .storage.

Les mises à jour de code n'ont pas été installées sur le RPi4 de l'utilisateur
pendant la préparation de ce paquet.
