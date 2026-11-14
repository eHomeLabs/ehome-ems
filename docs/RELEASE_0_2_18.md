# eHome EMS 0.2.18 — Universal Energy Manager

Cette release consolide les PR #17 (Énergie Maison), #19 (sessions VE), #21 (ECS) déjà fusionnées et réutilise la PR #22 (météo solaire horaire). Les associations, identifiants et personnalisations existants sont conservés.

## ECS / F1ATB

Objectif configurable (3 kWh proposé), cycle 07:00 → 07:00 sans remise à zéro du compteur cumulatif. Le routeur conserve la priorité photovoltaïque native ; le complément nocturne est calculé à rebours de l'échéance à partir de l'énergie restante, de la puissance déclarée et des créneaux autorisés. Les fenêtres doivent permettre matériellement d'atteindre l'objectif.

Le complément météo HC (12:30–14:30 proposé) vise une fraction configurable de l'objectif du cycle par mauvais temps (50 % proposé). Toute énergie déjà consommée est déduite. Le complément nocturne vise l'objectif complet. Une météo absente n'est pas interprétée comme du mauvais temps.

Forçages 30 min, 1 h et Full : contrôles de droits, conflits, état du routeur, compteurs et puissance fraîche conservés ; Full vise l'objectif énergétique avant 07:00, sans marche permanente illimitée. Les baux courts et retour Auto restent inchangés. Aucune activation automatique d'un objectif existant. Voir [le guide ECS](STRATEGIE_ECS_0_2_17.md).

## Batteries et réserve

Dans Stockage → modifier la batterie, réserve énergétique configurable de 30 %, seuil minimal natif déclaré de 10 %. Le budget estimé utilisable exclut **le plus élevé** des deux seuils : capacité × max(0, SOC − seuil) / 100. Les données invalides n'autorisent aucun budget. Sans capacité, le budget kWh reste indisponible.

Ce paramétrage ne commande ni le BMS Zendure ni un inverseur de source. eHome n'envoie aucune commande de décharge batterie ; le moteur de simulation ne distribue qu'un surplus positif fictif. La réserve doit également être configurée dans la régulation native si celle-ci peut décharger indépendamment d'eHome. L'énergie physique disponible dépend des pertes et du matériel ; la réserve EMS ne constitue pas un basculement électrique automatique ni une garantie de secours.

## Mes appareils et sélection des sources

- Jauge horizontale jaune par appareil, calculée à partir de sa puissance nominale/maximale configurée. Remplissage borné à 100 % ; puissance réelle et flèches de tendance conservées. Aucun maximum supposé si non renseigné.
- Synthèse des appareils disponibles, indisponibles et inconnus. Voyant vert/rouge/gris fondé sur les sources associées HA : `off` et `0 W` sont disponibles ; `unavailable` est rouge ; source absente ou `unknown` est grise. Une source associée indisponible prime sur une source inconnue.
- Détection du metering via classes HA et unités puissance/énergie/courant/tension, indépendamment de Zigbee2MQTT, ZHA, Shelly, MQTT ou ESPHome. Entités groupées par appareil du registre HA, pertinence du nom prioritaire. Les champs gardent leurs unités compatibles ; « Afficher toutes les entités » retire le filtre metering dans la liste compatible. Les champs spécialisés (température, SOC…) conservent leurs sources dédiées.
- Onglet actif conservé après enregistrement ; alertes, tendances, coûts estimatifs et historiques préservés.

## Bilan et prévisions

Conso Maison AC = solaire + import − export − charge + décharge. Une seule représentation réseau (signée ou séparée), sans ajout des sous-compteurs et sans source dupliquée. Les équipements hybrides ne mélangent pas production DC et sortie AC ; les fiches PV ne remplacent pas implicitement le bilan Maison. Les compteurs du jour restent des sources explicitement associées : une différence historique HA/EMS n'est pas corrigée par une valeur inventée. Voir [les périmètres énergétiques](energy-accounting-configurable-sources.md).

Prévisions horaires du fournisseur météo HA, tableau du jour dans le fuseau HA et indice solaire 08:00–17:00 pondéré vers midi. Données manquantes explicites ; ce sont des conditions météo et un indice, **pas une prédiction de production en kWh**. La disponibilité des prévisions horaires dépend de l'intégration météo choisie.

## Installation / mise à jour

1. Sauvegarder Home Assistant et la configuration eHome EMS.
2. HACS → Intégrations → eHome EMS → Mettre à jour vers **0.2.18**. Au besoin, ouvrir le menu HACS et actualiser les informations du dépôt `eHomeLabs/ehome-ems`.
3. Redémarrer Home Assistant pour charger le nouveau code Python, puis recharger complètement le navigateur ou l'application mobile.
4. Vérifier la version **0.2.18**, les associations et les journaux. Renseigner les puissances maximales et les réserves souhaitées sans réactiver automatiquement les commandes.

Home Assistant minimum : 2026.9.1. Pour une installation manuelle, décompresser `ehome-ems-0.2.18.zip` à la racine de la configuration HA (dossier `custom_components/ehome_ems`), puis redémarrer. L'archive SHA-256 accompagne le paquet.

## Contrôles de livraison

Tests Python (y compris les tests météo et VE auparavant hors découverte unittest), tests JavaScript, navigateur Chromium sur ordinateur/mobile, intégration HA simulée sur deux versions, vérification documentaire et paquet ZIP. Publication unique par le workflow Home Assistant package après réussite de ces contrôles. Aucun test sur une installation personnelle ni aucune commande à un routeur ou une batterie réelle.
