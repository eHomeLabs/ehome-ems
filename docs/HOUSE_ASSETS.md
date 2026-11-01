# Illustrations maison — b12

L’illustration de nuit existante reste `custom_components/ehome_ems/frontend/assets/house.webp`.
La déclinaison de jour est enregistrée dans `custom_components/ehome_ems/frontend/assets/house-day.webp` (768 × 384, WebP avec transparence), puis incluse dans le paquet HA. Aucun chargement externe n’est nécessaire.

Création avec l’outil intégré Image Gen, mode édition, à partir de l’asset nuit. Conversion et réduction au format WebP pour limiter la taille du paquet. L’original généré n’est pas une dépendance du runtime.

Prompt de création :

> Use case: lighting-weather. Edit this exact house illustration into its daytime version for an energy dashboard. Preserve the exact architecture, roof with solar panels, garage, front battery unit, trees, camera perspective and wide composition. Change only lighting and time of day: clear natural daylight, sunlit roof and walls, green foliage, windows no warm nighttime glow. Preserve sophisticated blue/slate house materials. Keep the entire silhouette and framing unchanged so it can replace the night asset without moving any flow connections. Isolated house cutout, genuinely transparent background, no sky rectangle, no text, no labels, no arrows, no extra objects. Wide 2:1 image.

La sélection utilise le fuseau de Home Assistant, jamais celui du terminal ou du téléphone : jour à partir de 07:00, nuit à partir de 19:00. Tests des bornes, de l’heure d’été/hiver et de la stabilité de la géométrie du flux.
