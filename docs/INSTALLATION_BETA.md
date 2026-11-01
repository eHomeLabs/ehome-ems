# eHome EMS 0.2.0b14 — installation et retour arrière

Première bêta en observation. Le périmètre produit « V2 » n'est pas encore livré
en totalité. La bêta contient l'assistant, les mesures normalisées, le suivi
multi-batteries et l'export manuel d'un dashboard natif.

La b10 ajoute des priorités de simulation enregistrées et un répartiteur de
budget hypothétique dans Stratégie. Tous les équipements sont exclus par défaut.
Le journal est limité à 20 scénarios en mémoire. Aucun pilotage n'est activé.
Voir SIMULATION.md pour les hypothèses et les limites.

La b9 ajoute un seuil d'animation global de 10 W, corrige l'espace réservé aux
cartes du flux et enrichit les diagnostics de sources dans Configuration.
Tester une borne à 1 W : la valeur doit rester visible sans animation.
À 10 W, la branche doit s'animer si les animations système sont autorisées.
Vérifier aussi une batterie avec charge et décharge à zéro : aucune carte ne
doit recouvrir le texte placé sous la scène.

La bêta 0.2.0b14 ajoute des explications dans chaque étape et une aide par champ
pour les batteries. Une consommation maison déjà calculée est acceptée si elle
décrit les usages réels. L'énergie restante doit être un stock, pas un compteur
cumulatif. Une classe total/total_increasing nécessite désormais une confirmation explicite si le capteur est réellement un stock. Au-delà
de capacité × 1,10, l'association est signalée incohérente. Pendant le suivi, un
tel stock devient indisponible plutôt que d'être affiché comme valide.
Le champ reste facultatif : laissez-le vide si aucune source ne convient.
La vue automatique et la copie native sont disponibles depuis 0.2.0b5 ;
un synoptique animé est disponible dans la vue gérée depuis 0.2.0b7.

La bêta 0.2.0b14 organise le dashboard avec une navigation haute : Vue d’ensemble,
Mes Appareils, Stockage, Usages, Historique, Aujourd’hui, Stratégie et Configuration. Les mesures principales
sont en haut, le flux au centre, les usages en bas et la situation EMS à droite
sur PC. Sur mobile, la colonne de droite passe sous le flux et les usages.
L'EMS reste en observation ; la simulation manuelle ne constitue pas un moteur
de pilotage actif.
La page Configuration montre les sources et les versions chargées.

À l'étape Maison, choisir entre une source existante et le calcul automatique EMS.
Ce dernier demande les capteurs séparés import/injection, les mesures AC des modules
présents et une confirmation du périmètre. Les sources périmées ou manquantes
rendent le résultat indisponible. Voir CONSOMMATION_MAISON.md avant activation.

## Marketplace et nouvelles vues

La b11 ajoute Mes Appareils et Aujourd’hui, les cartes de puissance colorées avec historique, le stockage visuel et le flux central plus compact. Les réglages sont accessibles via Configurer → Mes Appareils / Aujourd’hui et tarif. Voir [notes b11](RELEASE_0_2_0B12.md) pour les unités, périodes, coûts estimatifs et limites.

## Paquet à utiliser

Dans GitHub → Actions → Home Assistant beta package, ouvrir une exécution réussie
correspondant au dernier commit de la proposition de code puis télécharger
l'artefact ehome-ems-0.2.0b14. Il contient le ZIP installable, son SHA-256 et ce guide.
Le paquet est produit seulement après succès de la validation backend HA réelle.
Les artefacts GitHub sont conservés 90 jours et peuvent être reconstruits avec
scripts/build_test_package.py ou en relançant le workflow.

Le ZIP installable contient custom_components/ehome_ems uniquement. L'archive
d'artefact GitHub est une enveloppe : extraire d'abord le fichier
ehome-ems-0.2.0b14.zip qu'elle contient.

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

Le dépôt est public. La méthode recommandée est désormais Marketplace/HACS : ajouter https://github.com/eHomeLabs/ehome-ems en dépôt personnalisé de catégorie Intégration, puis sélectionner la préversion 0.2.0b14 (afficher les bêtas si nécessaire). Le ZIP reste une alternative.

1. Extraire ehome-ems-0.2.0b14.zip sur le PC.
2. Copier son dossier custom_components/ehome_ems dans
   /config/custom_components/ehome_ems sur HA, en remplaçant le code précédent.
   Vérifier qu'il n'y a pas de niveau ehome_ems/ehome_ems imbriqué.
3. Vérifier la présence de manifest.json avec version 0.2.0b14.
   Copier aussi les sous-dossiers frontend et brand, avec tous leurs fichiers.
4. Redémarrer Home Assistant une fois pour charger le nouveau code.
5. Si l'intégration existe déjà : Paramètres → Appareils et services → eHome EMS
   → Configurer. Les associations V0.1 sont reprises.
   Sinon : Ajouter une intégration → eHome EMS.
6. Suivre réseau → solaire → maison → batteries → vérification → confirmation.
   Une étape Usages après les batteries permet aussi de suivre le routeur/ECS,
   la borne VE ou d'autres charges ; elle peut être ignorée.
   Pour une batterie utilisée au quotidien, choisir explicitement le rôle actif.
   Le rôle secours est proposé par défaut ; l'Aferiy peut rester en secours.

Les changements d'associations se rechargent ensuite sans redémarrage complet de HA.
Une entrée eHome EMS apparaît automatiquement dans la barre latérale. Depuis
cette vue, Créer une copie modifiable permet aux administrateurs d'obtenir un
dashboard natif indépendant, sans YAML. Voir DASHBOARD_AUTOMATIQUE.md.
Après mise à jour du code, actualiser également la page ou l'application HA.
Le premier chargement du code et ses mises à jour nécessitent un redémarrage.
Aucune commande d'équipement n'est envoyée par cette bêta.

## Si le flux est absent après une mise à jour

Ouvrir la vue eHome EMS de la barre latérale : son chemin commence par
`/ehome-ems-`. Une copie native indépendante (`/ehome-ems-copy-…` ou un dashboard
créé manuellement) conserve ses cartes : elle n'ajoute pas le flux animé.
Les nouvelles copies comportent un lien vers la vue automatique ; les anciennes
copies ne sont pas modifiées.

La b7 pouvait aussi laisser une ancienne classe d'interface chargée dans une
session HA déjà ouverte : le composant gardait le même nom entre versions.
La b8 utilise un fichier JS et un nom de composant propres à la version.
Cela couvre ce cas de coexistence sans supprimer de copie personnalisée.
La cause sur une instance donnée demande de vérifier la vue réellement ouverte
et la version chargée : ne pas conclure automatiquement à un problème de cache.

Après remplacement complet du dossier, redémarrer HA une fois puis recharger
complètement la page ou fermer/réouvrir l'application HA. Dans Configuration,
les versions Interface et Intégration doivent toutes deux indiquer 0.2.0b14.
Un serveur ne fournissant pas le flux déclenche maintenant une explication visible,
au lieu de masquer silencieusement le composant.

## Premier essai

- Comparer réseau, solaire et maison avec leurs sources : unités et signes.
- Vérifier SOC, charge/décharge et énergie restante des batteries configurées.
- Modifier une association, confirmer et vérifier le rechargement.
- Exporter le dashboard avec ehome_ems.generate_dashboard : voir
  [le guide du dashboard](DASHBOARD_OBSERVATION.md). Utiliser un nouveau dashboard.
- Contrôler les journaux ehome_ems et signaler les erreurs avec la version HA.

Les détails de validation et limites figurent dans VALIDATION_ASSISTANT.md et
DASHBOARD_OBSERVATION.md. Le rendu sur Android, tablette et PC reste à vérifier.
La b14 ajoute le calcul journalier depuis les cumuls appareils et la météo HA. Sans historique à minuit, les euros du jour restent indisponibles. Pas de pilotage automatique. Voir RELEASE_0_2_0B14.md.
Voir USAGES_OBSERVATION.md pour le suivi des usages et la distinction entre
puissance mesurée, consigne et énergie du jour/session/cumul.

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
