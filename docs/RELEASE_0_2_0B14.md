# eHome EMS 0.2.0b14 — tendances, énergie du jour et observation fiable

## Conso Maison

Le bilan reste **solaire + réseau − charge batterie + décharge batterie**, cumulus et borne inclus. Une source qui publie seulement les changements ne rend plus le bilan indisponible au bout de cinq minutes : en observation, son âge est signalé sans masquer une valeur numérique valide. Le mode Strict reste disponible dans Configuration → Conso Maison et bloque après le délai configuré. Les valeurs manquantes, indisponibles, invalides, les unités incorrectes et les bilans négatifs restent bloquants. Les erreurs d’arrondi à proximité de zéro ne créent plus un faux bilan négatif.

Si le résultat est indisponible, le détail s’ouvre automatiquement avec chaque source, contribution, âge et motif. Cette correction vise le blocage lié à l’ancienneté des rapports ; elle ne prétend pas diagnostiquer une source physique sans ses données. Aucun capteur manquant n’est remplacé par zéro.

## Cartes et tendances

Les courbes sont retirées. Une flèche principale indique le dernier pas complet de 15 minutes et 24 petites flèches résument les six dernières heures, dans l’ordre de lecture. Chaque direction compare la moyenne d’un quart d’heure au précédent ; elle ne représente ni une prévision ni un gain énergétique. Données insuffisantes, pas manquant ou absence d’historique : flèche horizontale neutre explicitement identifiée, jamais faux zéro de puissance.

Titres sur deux lignes maximum, zones de valeur et tendance communes, cartes appareils alignées. Les cartes Aujourd’hui, météo comprise, partagent le même format. Tous les pourcentages visibles sont arrondis à l’entier, sans modifier les calculs.

## Mes Appareils : déduire le jour depuis un cumul

Pour les compteurs hors session, le panneau lit History/Recorder depuis minuit dans le fuseau HA. L’énergie journalière est calculée par différence avec la référence disponible à minuit, puis convertie en euros avec le tarif fixe configuré. Le cumul source reste visible séparément. Les baisses de compteur sont traitées comme des remises à zéro ; les incréments avant et après remise à zéro sont additionnés. Wh et kWh sont convertis.

Exemple : cumul à minuit 1 524 kWh, cumul actuel 1 524,81 kWh → **0,81 kWh aujourd’hui**, et non 1 524,81 kWh. Le calcul s’applique aussi aux anciens appareils déclarés « Aujourd’hui » alors qu’ils remontent un cumul. Une énergie de session reste une énergie de session.

Sans référence historique valide à minuit, l’énergie et les euros du jour restent indisponibles. Le panneau ne peut pas reconstituer une consommation passée à partir d’une seule valeur totale. Activez l’enregistrement de ces sources ; le calcul deviendra disponible avec l’historique nécessaire. Les requêtes sont regroupées, bornées à la journée et limitées à une fois par cinq minutes ; les résultats sont conservés en mémoire tant que les entrées ne changent pas. Aucun nouveau compteur physique ou automatisme n’est créé. Les euros sont un équivalent estimé au tarif fixe, pas la facture réseau exacte d’un appareil pouvant consommer du solaire.

## Stock batterie Aferiy et autres appareils

Un vrai stock peut être mal déclaré `total` / `total_increasing` par son intégration source. Dans Modifier la batterie, une confirmation explicite permet de l’utiliser comme **énergie restante**, avec Wh/kWh. Les limites de capacité restent appliquées (capacité déclarée + 10 %), et une puissance en W n’est jamais acceptée comme énergie. Les motifs précis sont désormais affichés dans les erreurs de configuration. Ne cocher cette confirmation que pour un vrai stock restant, jamais pour un total d’énergie consommée.

## Météo

Dans Configuration → Compteurs du jour et tarif, choisir une entité `weather` déjà présente dans HA. Aujourd’hui affiche sa prévision journalière : état du ciel, températures mini/maxi et pluie si fournies. Si la prévision journalière n’est pas disponible, la carte affiche les conditions actuelles en les identifiant explicitement. Pas de fournisseur ou de localisation imposés ; lecture de l’intégration météo HA par abonnement WebSocket.

## Mise à jour

Dans Marketplace/HACS, sélectionner **0.2.0b14**, conserver l’entrée et les associations, puis redémarrer HA une fois et recharger le panneau. Les réglages suivants se font par les raccourcis du dashboard. Vérifier Conso Maison, le détail des âges, la confirmation du stock Aferiy, l’historique des cumuls appareils et l’entité météo.

Observation et simulation restent sans commande physique ; aucune automatisation existante n’est modifiée.
