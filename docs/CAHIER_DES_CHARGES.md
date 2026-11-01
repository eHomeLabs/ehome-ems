# Cahier des charges eHome EMS
Référence produit — mise à jour du 1er novembre 2026 ; état livré : 0.2.1

## Vision
eHome EMS — Universal Energy Manager. Votre installation. Vos équipements. Votre énergie. Un EMS sur mesure.

Intégration Home Assistant distribuée via HACS, associant un assistant de configuration, un dashboard énergétique généré, des analyses, des prévisions et, sur activation explicite, un pilotage coordonné. Le fonctionnement local de base doit rester indépendant d'un abonnement ou d'une IA distante. Les équipements restent accessibles par leurs intégrations HA existantes.

Ce document distingue le socle livré en 0.2.1 des objectifs futurs. Le suivi en observation, les historiques, le calcul du jour depuis les cumuls et les scénarios manuels sont disponibles. Prévisions énergétiques, conseils avancés et pilotage restent à développer.

## Acquis et banc de validation de référence
Architecture exclusivement intégration HA, sur l'instance existante. Référence de test RPi4 avec SSD. Version 0.2.1 en observation et rechargement propre des paramètres. Aucune modification implicite des automatisations existantes.

Sources fonctionnelles : puissance réseau signée, import, export, production solaire et consommation maison. Les unités et le périmètre physique sont contrôlés dans l'assistant ; les identifiants réels restent dans la configuration locale de l'utilisateur.

Référence initiale : PV 3,24 kWc, Zendure SolarFlow 2400 AC+ de 8,2 kWh selon la dernière correction du 30 octobre, Aferiy P210 de 2,3 kWh en secours et exclue par défaut du bilan actif, cumulus 150 L 1800 W avec routeur F1ATB, VE Zoé et borne annoncée 7,2 kW maximum. Le courant réellement autorisé pour la borne reste un paramètre propre à l'installation, distinct de sa puissance commerciale. L'extension PV reste un projet tant qu'elle n'est pas déclarée installée.


## Assistant de configuration
1. Présenter le mode observation, choisir les modules et permettre de reprendre le parcours sans perdre les étapes validées.
2. Réseau : sélectionner puissance signée ou deux capteurs import/export, convention de signe, mono/triphasé, compteurs d'énergie et puissance souscrite facultative.
3. Photovoltaïque : un ou plusieurs champs/onduleurs, puissance totale, compteurs, puissance crête et mesures AC/DC. Éviter de sommer un total avec ses sous-ensembles.
4. Maison : mesure directe ou calcul par bilan, périmètre AC des batteries ; cumulus, borne et autres usages toujours inclus dans le total. Prévisualisation des valeurs et contrôle des incohérences.
5. Stockage : ajouter plusieurs batteries, rôle actif ou secours, SOC, énergie utile, charge/décharge, couplage AC/DC, capacités et limites. Un profil constructeur propose les correspondances mais l'utilisateur les valide.
6. Usages : ECS, routeur, VE, piscine, chauffage/PAC et autres charges. Distinguer mesure seule, marche/arrêt et consigne modulable.
7. Tarifs et objectifs : Base, HP/HC, calendriers tels que Tempo si source disponible, prix achat/vente, réserve batterie, confort et échéances.
8. Prévisions facultatives : source déjà disponible dans HA, horizon et historique utilisable. L'absence de prévisions ne bloque pas le suivi.
9. Contrôler unités, signes, compteurs, fraîcheur des données et bilan ; afficher clairement les fonctions disponibles et celles qui manquent de données.
10. Générer un aperçu puis le dashboard. Le pilotage reste désactivé ; un parcours séparé permet de l'activer équipement par équipement.

Les réglages restent modifiables sans réinstallation ni redémarrage complet de HA. Une première installation ou certaines mises à jour peuvent nécessiter un redémarrage.

## Dashboard
Vue Synthèse : flux animé lisible, avec solaire, réseau, maison, batteries distinctes et usages principaux. Sens et valeurs explicites, état global et date de mise à jour. Affichage mobile, tablette et PC ; animation réduite disponible et sens compréhensible sans couleur.

Jauges de puissance en W/kW, charge et décharge séparées, jauges d'énergie en kWh avec période et objectif explicites, SOC et réserve. Les échelles et seuils sont configurables.

Vues complémentaires : Aujourd'hui, Historique, Stockage, Usages, Prévisions, Conseils et Réglages. Courbes production/consommation/import/export/batterie synchronisées ; périodes jour/semaine/mois/année ; répartition des usages avec reliquat non mesuré.

Le panneau géré suit les associations. Les anciennes copies personnelles et les exports restent indépendants et préservés ; aucun bouton de création de copie n'est proposé dans le panneau.

## Modèle énergétique et indicateurs
Convention interne AC : réseau positif à l'import, batterie positive en décharge. Si toutes les mesures partagent le même périmètre :
P maison = P PV AC + P import + P décharge batterie - P export - P charge batterie.
Une mesure maison valide reste prioritaire ; le bilan sert aussi au diagnostic. Les systèmes hybrides DC demandent un adaptateur de topologie pour éviter les doubles comptes.

Exposer production, consommation, import, export, charge/décharge, énergie restante, taux d'autoconsommation, taux d'autonomie, talon, coûts et énergie par usage.

Séparer surplus net exporté, surplus avant allocation aux charges pilotées et puissance réellement réallouable. Une batterie qui décharge ne doit pas créer un faux surplus solaire ; un zéro injection ne signifie pas qu'aucune énergie n'est déjà absorbée par le stockage ou le routeur.

Sans batterie, autoconsommation = (production - export solaire) / production et autonomie = solaire fourni à la maison / consommation, sur une même période. Avec batterie, conserver un bilan charge/décharge et l'origine PV/réseau du stock, ainsi que ses variations et pertes. Sans données suffisantes, afficher un indicateur estimé ou indisponible ; ne pas attribuer automatiquement toute décharge au solaire. Distinguer énergie PV retenue sur site et énergie PV effectivement livrée aux usages.

Utiliser les compteurs fiables existants en priorité ; intégrer les puissances si nécessaire avec traitement des trous et sans reconstruire artificiellement l'énergie manquante. Gérer remises à zéro, statistiques HA, fuseau local et changement d'heure. Ne jamais remplacer une donnée indisponible par zéro.

## Analyse et prévisions
Analyse : talon, pics d'import, périodes d'injection, rendement batterie estimé sur périodes comparables, énergie déplacée, pertes, couverture ECS/VE et anomalies. Comparer des jours et semaines en tenant compte de la météo et de l'historique disponible.

Prévisions : production aujourd'hui/demain et courbe horaire si disponible ; consommation à partir d'un profil simple puis de l'historique ; SOC prévisionnel, réserve au soir, risque d'import et créneaux pour usages. Afficher hypothèses, fraîcheur, erreur réel/prévu et niveau de confiance. Ne pas inventer une courbe horaire à partir d'une seule valeur journalière.

Conseils explicables : chaque proposition présente données utilisées, action suggérée, durée, contrainte, gain estimé et incertitude. Exemples : différer une recharge, conserver une réserve, privilégier ECS ou stockage. Le conseil de charge HC tient compte du rendement aller-retour, de l'usure paramétrable, du tarif évité et du PV attendu. Les économies réalisées et les économies simulées sont séparées. Une IA de reformulation peut être facultative ; le calcul et les règles ne doivent pas en dépendre.

## Pilotage progressif
Modes Observation, Conseil, Simulation et Automatique. La simulation journalise les décisions sans envoyer de commande. En automatique : priorités modifiables, échéances, minima de marche/arrêt, hystérésis, réserve SOC, puissance réseau maximale et import d'appoint autorisé par équipement.

Un seul arbitre répartit la puissance disponible entre charges et stockage. Il coordonne les consignes plutôt que plusieurs boucles concurrentes. Pour F1ATB, conserver la régulation rapide du routeur et agir seulement sur les modes/consignes explicitement exposés. Même principe pour un EMS constructeur déjà actif.

Prévoir reprise manuelle temporaire, expiration du forçage, pause du pilotage EMS et journal des raisons. Une pause stoppe les nouvelles décisions et applique le mode de restitution configuré ; elle ne signifie pas couper toute la maison. En cas de capteur essentiel périmé, suspendre l'optimisation et appliquer un comportement de repli propre à l'équipement. Vérifier les retours d'état et limiter les répétitions de commandes. Préserver les fonctions de confort et de sécurité natives des équipements.

## Architecture et qualité
Backend Python pour configuration, normalisation, états et règles ; frontend pour flux, jauges et génération du dashboard. Le paquet HACS unique contient backend, frontend et assets locaux. Les évolutions doivent conserver les interfaces publiques HA.

Écouter les changements d'état des sources plutôt que multiplier les appels matériels. Calculs rapides distincts des bilans historiques et des prévisions ; aucun solveur lourd obligatoire sur le RPi4. Statistiques HA réutilisées, requêtes bornées et fréquence d'affichage limitée.

Identifiants stables, migrations de configuration, reload/unload propres, diagnostics expurgés et droits administrateur pour modifier le pilotage. FR en priorité, structure de traduction EN. Documentation des topologies compatibles, entités attendues et limites. CI et tests sur signes, unités, bilans, statistiques, changements d'heure, arbitrage et migrations. Conformité HACS/Marketplace vérifiée au moment de la publication ; validation officielle distincte de la simple installation par dépôt personnalisé.

## Lots et critères d'acceptation
Lot A — socle visible : assistant, réseau/PV/maison/batteries, flux, jauges et statistiques, lecture seule. Acceptation : signes et unités vérifiés, bilan cohérent sur jeu de mesures synchronisées avec tolérance documentée, batterie secours exclue, états indisponibles visibles, configuration rechargeable sans reboot.

Lot B — compréhension : coûts, historique, prévisions externes et conseils déterministes. Acceptation : coût vérifié sur jeu de référence, origine batterie incertaine signalée, absence de prévisions tolérée, erreurs réel/prévu visibles.

Lot C — orchestration : simulation puis pilotage ECS/batterie/VE selon capacités exposées. Acceptation : aucune commande en observation/simulation, allocation sans double compte, priorités et forçages respectés, repli testé sur source périmée.

Lot D — optimisation : profils de consommation, scénarios et optimisation avancée facultative. Acceptation : comparaison à une stratégie de référence, temps de calcul mesuré sur RPi4 et fonctionnement du socle sans ce moteur.

Le socle du lot A et une partie des historiques/coûts sont disponibles en 0.2.1. Les lots B à D restent des objectifs au-delà des fonctions explicitement listées dans le README.

## Décisions restant à prendre
Priorités confort/ECS/batterie/VE selon saison ; autonomie ou coût comme objectif par défaut ; seuils et réserve batterie ; rôle précis de l'Aferiy ; périmètre électrique des mesures ; courant maximal réellement autorisé à la borne ; topologies AC/DC du premier lot. Le cadrage s'appuie sur les besoins exprimés et la documentation publique.

## Sources consultées le 31 octobre 2026
- Home Assistant Energy : https://www.home-assistant.io/docs/energy
- Stratégies de dashboard : https://contributors.home-assistant.io/frontend/custom-ui/strategy/
- Forecast.Solar : https://www.home-assistant.io/integrations/forecast_solar/


