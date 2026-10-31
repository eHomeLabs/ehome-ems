# Validation visuelle et mise à jour du panneau — 0.2.0b8

final result: passed

## Référence et preuves

- Source : maquette d'ensemble validée, `generated_images/exec-f13f025c-7b57-4a86-adef-ef9e1745b156.png`, 1536 × 1024.
- Modification explicite de la référence : navigation en haut, demandée après validation ; la barre latérale de la maquette n'est pas reproduite.
- Code inspecté : `ece48f34f4ebd129f194cc8076a0c324814f2731`.
- Rendu Chromium : https://github.com/eHomeLabs/ehome-ems/actions/runs/41242809849 ; artefact `panel-preview-simulated`.
- Captures : desktop.png (1440 × 1600), mobile.png (390 × 844), flow-desktop.png (983 × 890), flow-mobile.png (358 × 702), editor-desktop.png et editor-mobile.png.
- Viewports CSS : 1440 × 1600 et 390 × 844, densité 1. La hauteur desktop permet de capturer tout le dashboard ; le défilement reste normal sur un écran plus court.
- Source et capture desktop juxtaposées à largeur commune 768 px, sans étirement, puis inspection du flux et des valeurs à leur résolution native.
- État : français, sombre, administrateur ; données simulées cohérentes : solaire 1500 W, import 0 W, injection 75 W, charge 1000 W, maison 425 W, SOC 18 %, cumulus 200 W, véhicule 0 W.

## Contrôle visuel

- Typographie : police système HA, valeurs principales hiérarchisées, chiffres tabulaires ; libellés et unités lisibles à la résolution native. Les valeurs W viennent des miroirs, sans chiffres de démonstration embarqués en production.
- Espacement : navigation horizontale au-dessus des mesures principales ; flux dans la colonne centrale/gauche, situation à droite, usages et qualité en bas. Repli sur une colonne et navigation défilante horizontalement sur mobile.
- Couleurs : ambre solaire, bleu maison, cyan réseau, vert batterie, orange ECS et violet VE ; le sens reste explicite par les libellés Import/Injection et Charge/Décharge.
- Images : maison locale transparente générée pour la maquette précédente, conservée ; icônes MDI via ha-icon natif, vrais tracés MDI dans le banc de test.
- Texte : mode Observation explicite, aucun pilotage présenté comme actif. Sources existantes distinguées du total calculé EMS. Compteur de mesures indisponibles incluant les miroirs absents du registre.

La vue réelle ajoute un indicateur Import distinct de l'Injection pour éviter de masquer un échange réseau important. Le nombre d'usages suit la configuration (deux dans la fixture, quatre dans la maquette). Aucun appareil, gain, taux d'autonomie, conseil ou ordre de priorité n'est inventé pour remplir l'écran. La densité du flux reste plus aérée que l'image de présentation afin de conserver la lisibilité des états et des deux directions réseau.

## Historique des corrections visuelles

1. Premier rendu b8 : carte batterie trop basse dans la scène desktop, masquant une partie de la note sur les usages, et trait blanc passant derrière la valeur maison.
2. Correction : scène desktop de ratio 1000/600, batterie à 50 % de sa hauteur, origine du trait maison à y=700 ; retrait des paragraphes de présentation au-dessus des mesures et alignement de la marque à gauche.
3. Recapture : les captures finales desktop et mobile montrent les valeurs, cartes et notes sans recouvrement. Le flux reste centré autour de la maison ; aucune barre traversante jaune-bleue ni éclair central.

Les captures natives du flux et du sélecteur ont été ouvertes séparément pour le contrôle régional des valeurs, icônes, raccordements et champs. La comparaison d'ensemble a été faite en juxtaposition ; elle ne repose pas sur le code seul.

## Tests des interactions et de mise à jour

- Le banc navigateur enregistre volontairement une ancienne classe `ehome-ems-panel` avant de charger le nouveau module : le composant versionné b8 est distinct et affiche le flux.
- Navigation haute et présence des six rubriques ; parcours Stockage/Historique/Stratégie/Configuration, ouverture d'historique, recherche et changement de source par appui prolongé ou bouton explicite, annulation et copie native indépendante.
- Versions Interface et Intégration affichées dans Configuration.
- Serveur simulé sans champ flow : message de diagnostic visible, pas de disparition silencieuse.
- Absence de débordement horizontal du dashboard, image décodée, traitement des mesures indisponibles, réduction des animations et absence d'erreurs JavaScript observées.
- Lecteur : bouton de copie absent ; droits d'écriture toujours contrôlés côté serveur.
- Moteurs HA : endpoint versionné, nom du composant, version du snapshot, image locale, permissions et rechargements couverts par le scénario de validation.

## Diagnostic de l'absence de flux signalée sur b7

Le ZIP réellement livré a été téléchargé et inspecté : il contient le code frontend du flux, le snapshot backend et la maison WebP. Un défaut de coexistence est identifié dans la b7 : nom de composant identique et enregistrement ignoré si une ancienne classe est déjà présente. La b8 versionne à la fois l'URL du module et le nom de composant.

Ce mécanisme ne prouve pas la cause sur l'installation de l'utilisateur. Une copie Lovelace indépendante ne contient pas non plus le synoptique. Les nouvelles copies incluent donc un lien vers la vue automatique ; les anciennes copies personnalisées restent intactes. Le diagnostic utilisateur doit distinguer vue ouverte, version chargée et éventuel remplacement partiel du dossier.

## Limites et suivi

- Rendu dans le shell Android HA et fluidité sur RPi4 à confirmer sur appareil physique.
- Stratégie reste un état des lieux : édition des priorités, simulation, conseils et commandes non livrés.
- P3 : affiner la densité du synoptique après retour d'usage sur tablette.
- Aucun P0/P1/P2 restant dans le périmètre des captures et tests.
