# Usages et Mes Appareils

Le panneau suit des entités déjà disponibles dans HA. **Mes Appareils** permet d'ajouter, modifier et retirer des appareils directement. **Usages** présente notamment routeur/cumulus et borne de recharge. Les identifiants sont conservés lors d'une modification ; retirer du suivi ne désinstalle pas l'intégration constructeur.

## Sources et icônes

Nom, puissance W/kW, énergie Wh/kWh, période du compteur, état facultatif et confirmation du périmètre maison. Le cumulus accepte aussi une température d'eau facultative. Au moins une source est nécessaire.

L'icône native MDI est choisie selon le nom : réfrigérateur, lave-linge, sèche-serviettes, piscine, climatisation, cafetière, etc. Le champ **Icône du produit** permet une sélection manuelle. Les sous-compteurs restent inclus dans Conso Maison ; ils ne sont jamais ajoutés ou soustraits à son bilan.

## Énergie quotidienne depuis un cumul

Déclarer la période réelle de la source : **aujourd'hui**, **session** ou **total cumulé**. Pour un cumul, le panneau utilise l'historique à minuit dans le fuseau HA et la variation jusqu'à maintenant, avec traitement des remises à zéro. **Énergie Totale** affiche le compteur source, distinct du résultat calculé du jour.

Exemple : 1 524,81 kWh actuellement − 1 524 kWh à minuit = **0,81 kWh aujourd'hui**. Sans référence historique exploitable à minuit, énergie et coût du jour restent indisponibles. Un compteur de session n'est pas transformé en compteur journalier. Un compteur déclaré « aujourd'hui » doit réellement couvrir le jour courant.

Le coût estimatif applique le tarif fixe configuré à l'énergie quotidienne exploitable, hors abonnement et revente. Ce n'est pas une facturation HP/HC ou Tempo.

![Appareils, tendances et énergie quotidienne](screenshots/appliances.png)

## Cumulus et borne

La puissance réelle consommée est distincte de la consigne SSR, du pourcentage de routage ou d'un ordre de forçage. « Température non associée » signifie qu'aucun capteur de température n'est configuré ; « Température indisponible » concerne la source de température associée. Ces mentions ne signifient pas que la puissance du cumulus est indisponible. L'échelle thermique 0–100 °C n'est pas un stock énergétique mesuré.

La borne affiche sa puissance et l'énergie selon la période déclarée, avec une silhouette dédiée. Un état comme « branché » ne prouve pas une recharge active. Les régulations natives F1ATB et constructeur restent inchangées.

## Tendances

Une seule flèche par carte : hausse, baisse ou stabilité entre moyennes de quarts d'heure sur six heures. Sans données suffisantes, flèche horizontale et mention explicite. Rouge pour une charge consommant une puissance positive, bleue sinon ; production, export et décharge restent bleus. Le seuil de 10 W concerne seulement l'animation des flux, pas la couleur de consommation.

Même si une source `switch` est choisie pour son état, EMS ne fait que la lire. Aucune consigne ni commande n'est envoyée.
