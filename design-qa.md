# Validation visuelle — flux maison centrale, 0.2.0b7

final result: passed

## Référence et preuves

- Source visuelle : maquette à maison centrale validée dans la conversation,
  `generated_images/exec-db9b87b4-1505-4284-8bda-9563b068f21f.png` (1024 × 1536).
- Code vérifié : `16c5bc2174522f063935ea026649021ccf78f7e1`.
- Captures Chromium : [exécution de validation](https://github.com/eHomeLabs/ehome-ems/actions/runs/41238867023),
  artefact `panel-preview-simulated`, `flow-mobile.png` (358 × 701),
  `flow-desktop.png` (1192 × 1097), `editor-mobile.png`, `editor-desktop.png`.
- Viewports CSS : 390 × 844 et 1440 × 1600, densité 1.
- Comparaison effectuée en juxtaposition : source ramenée à 390 px de large,
  composant mobile à sa résolution native 358 px, sans étirement.
  L'en-tête et les onglets HA sont hors du composant de flux ; le cadrage
  n'est donc pas une reproduction pixel à pixel de l'écran de présentation.
- État : français, thème sombre, administrateur, données simulées cohérentes :
  PV 1500 W, injection 75 W, charge 1000 W, maison 425 W ; usages suivis
  cumulus 200 W et véhicule 0 W. Aucun reste de consommation n'est inventé.

## Comparaison et corrections

1. Premier rendu : la capture du viewport ne montrait pas le bas du flux et
   les icônes HA manquaient dans le banc de test isolé. Correction : captures
   du composant complet, viewport desktop plus haut, adaptateur de test utilisant
   les vrais tracés Material Design Icons. La production utilise `ha-icon` natif.
2. La maison était trop déportée à droite et l'espace vertical mobile excessif.
   Correction : centre de la maison à 56 % de la scène, hauteur mobile 350 px,
   raccordement direct aux usages. Les dernières captures montrent les cartes
   complètes et aucun recouvrement de leurs valeurs.

## Surfaces vérifiées

- Typographie : police système cohérente avec HA, valeurs hiérarchisées et
  chiffres tabulaires ; les libellés et unités sont lisibles sur mobile.
- Espacement : sources en haut, maison centrale, batterie latérale, usages
  en dessous ; absence de barre traversante jaune-bleue et d'éclair central.
  La grille d'usages s'adapte au nombre de mesures configurées.
- Couleurs : ambre solaire, cyan réseau, vert stockage, orange ECS, violet VE,
  sur fond bleu nuit ; les libellés expriment aussi le sens et le type du flux.
- Images : maison générée séparément à partir de la direction validée,
  transparence propre, ressource WebP locale ; icônes MDI, sans substitut emoji.
- Texte : total maison calculé distingué d'une source maison existante dont
  le périmètre peut exclure le cumulus. Import et injection sont affichés
  séparément, sans convention de signe implicite. Pas d'autonomie inventée.

Les nombres et le nombre d'usages diffèrent volontairement de la maquette :
ils viennent de la fixture. L'import reste affiché même à zéro pour rendre la
convention explicite. Les batteries de secours et DC sont présentées séparément
et ne sont pas dessinées comme une branche AC quotidienne.
Les détails typographiques et les valeurs sont lisibles dans les captures
natives ouvertes ; aucun agrandissement régional supplémentaire n'était requis.

## Interactions et limites

Tests Chromium réussis : absence de débordement horizontal, image décodée,
flux actifs selon les états, arrêt du flux solaire indisponible, réduction des
animations, appui prolongé, recherche et sauvegarde de source, onglets,
historique et copie indépendante ; aucune erreur JavaScript observée.
Tests HA réels : snapshot des identifiants miroirs, image servie avec type WebP,
authentification, permissions, rechargement et conservation des personnalisations.

Reste à confirmer sur l'appareil physique : rendu dans le shell Android HA et
fluidité sur RPi4. La copie Lovelace indépendante garde les cartes natives et
n'inclut pas ce composant. Les animations ne certifient ni synchronisation des
mesures ni origine solaire de l'énergie stockée.

## Suivi mineur

- P3 : ajuster la luminosité des traits selon les retours en situation réelle.
- Aucun défaut P0/P1/P2 restant dans le périmètre des captures et tests ci-dessus.
