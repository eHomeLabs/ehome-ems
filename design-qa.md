# Validation du flux — 0.2.0b9

final result: passed

## Référence et preuves

Source : capture appareil fournie par l'utilisateur, `upload/01-1000021476.jpg`,
691 × 1536. Le problème est visible sous la batterie Zendure : la carte cache
le texte et une borne à 1 W a une branche animée.

Code vérifié : `5f19b8217abadfd38b36cf9d85ed0dc74c8e3aba`.
Exécution : https://github.com/eHomeLabs/ehome-ems/actions/runs/41245666096.
Artefact : `panel-preview-simulated`, captures `idle-mobile.png`,
`idle-desktop.png`, `flow-mobile.png`, `flow-desktop.png`, `desktop.png`,
`mobile.png` et captures du sélecteur de source.

Viewports CSS : 390 × 844 et 1440 × 1600, densité 1. Capture mobile du composant
au repos : 358 × 823. La région de flux de la capture appareil a été recadrée
puis ramenée à 358 px de large, sans étirement, et juxtaposée à la capture
Chromium native. Le nom batterie plus long dans la fixture est volontaire.
La navigation sticky peut apparaître en haut de la capture isolée lors du
scroll ; elle ne fait pas partie du défaut du texte sous Zendure.

## Cas de régression

- Solaire 0 W, import 731 W, injection 0 W, maison source existante 731 W.
- Batterie Zendure : charge 0 W ET décharge 0 W visibles, SOC 10 %.
- Cumulus 0 W ; véhicule 1 W, valeur conservée.
- Cas limite véhicule : 9,99 W non animé, 10 W animé, retour à 1 W non animé.
- Tests unitaires complémentaires : conversion 0,009/0,010 kW et disponibilité.

## Corrections et comparaison visuelle

1. La scène de hauteur supposée ne réservait pas la hauteur réelle d'une carte
   affichant deux puissances à zéro et un nom sur plusieurs lignes. Un wrapper
   réserve désormais la borne inférieure réelle des cartes et du libellé maison.
   La scène garde sa géométrie propre : sa hauteur ne dépend pas du wrapper,
   pour éviter une boucle de redimensionnement.
2. Un ResizeObserver suit la scène et les cartes ; il est retiré au changement
   de vue et à la déconnexion, puis recréé si nécessaire. La réserve suit les
   changements de contenu, le chargement de l'image et les redimensionnements.
3. Le premier rendu corrigé a révélé un trait passant derrière la valeur maison.
   Le départ du trait est maintenant calculé sous le bas réel de cette valeur,
   et son extrémité est incluse dans l'espace réservé.
4. Recapture finale : la note est entièrement sous la carte Zendure sur mobile
   et desktop, même avec le nom long et les deux lignes à zéro. Le trait maison
   démarre sous le texte. Les assertions géométriques vérifient un écart de 8 px
   minimum pour ces deux points.

La comparaison juxtaposée et l'inspection des captures natives ont porté sur la
zone batterie/note, la valeur maison/trait et les branches d'usages. La branche
véhicule est grisée ; l'absence d'animation est confirmée par le test DOM,
pas déduite d'une image statique.

## Surfaces vérifiées

- Typographie : styles HA conservés, valeurs et unités inchangées ; nom batterie
  long et libellé source existante ne masquent plus la note.
- Espacement : hauteur adaptée au contenu ; navigation haute et disposition
  centrale/droite conservées. Pas de débordement horizontal du dashboard.
- Couleurs : palette précédente conservée ; sous 10 W le trait est inactif,
  sans griser ou effacer la mesure numérique.
- Image : maison WebP locale inchangée, transparence et cadrage conservés ;
  icônes MDI natives.
- Texte : seuil expliqué comme un seuil visuel, sans prétendre qu'une faible
  valeur prouve l'arrêt d'un équipement. Configuration présente valeur source,
  valeur EMS et raisons de qualité disponibles ; qualité manquante non inventée.

## Validation et limites

Tous les jobs réussissent : tests Python, 9 tests JavaScript, scénarios sur HA
2026.9.1 et 2026.11.0b0, Chromium mobile/desktop, paquet ZIP contrôlé.
Les interactions existantes (navigation, historique, changement de source,
annulation, copie indépendante), réduction des animations et contrôles de droits
restent vérifiés. Aucune erreur JavaScript observée.

Le seuil est global à 10 W inclus pour toutes les branches. Il ne modifie pas
les capteurs, le calcul maison, les compteurs ni les automatismes. Les mesures
absentes ne deviennent pas zéro. Stratégie reste en observation.

Le rendu dans le shell Android et la fluidité sur RPi4 demandent encore le retour
sur appareil. Aucun P0/P1/P2 restant dans les cas capturés ; P3 : ajuster la densité
visuelle selon les prochains retours, sans remplacer la réserve dynamique par
une hauteur supposée.
