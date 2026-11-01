# eHome EMS 0.2.0b13 — Conso Maison et courbes

**Conso Maison = Production solaire + Réseau − Charge batterie + Décharge batterie.**

- Réseau signé : positif en import, négatif en export. Autre possibilité : Réseau = Import − Export avec deux capteurs. Le choix Auto conserve la paire Import/Export complète existante, sinon utilise le réseau signé. Le choix explicite est disponible dans Configuration → Conso Maison.
- Le calcul peut désormais fonctionner avec un réseau signé seul. Les valeurs Import/Export nécessaires au flux sont alors séparées automatiquement pour l’affichage, sans entrer une seconde fois dans le bilan. Aucun repli silencieux vers une autre source en cas d’indisponibilité.
- Le cumulus, la borne, le chauffage, le réfrigérateur et tous les usages restent inclus. Les sous-compteurs ne sont ni ajoutés ni soustraits au total. Les batteries actives AC sont additionnées séparément en charge/décharge ; les batteries de secours hors du périmètre sont exclues. Une topologie DC nécessite des mesures AC adaptées.
- Nom visible unifié **Conso Maison**, y compris le flux. Le choix capteur existant reste disponible : celui-ci doit représenter le total, et ne plus soustraire le cumulus. Les identifiants EMS restent stables.
- Nouveau détail du bilan dans la Vue d’ensemble : chaque contribution en W, source, âge et qualité. Les problèmes de réseau, association, topologie, fraîcheur, signe ou unité ont une explication visible.
- Fraîcheur : délai conservé à 300 s par défaut et inchangé pour les configurations existantes. Réglage de 30 à 3 600 s, ou **0 pour désactiver explicitement le blocage sur l’âge** si l’intégration source ne publie que les changements. Les âges restent visibles. Une valeur stable à 0 W n’est pas assimilée à une donnée manquante ; une valeur absente, invalide ou indisponible ne devient jamais zéro.
- Cartes de puissance : courbes lissées avec surface discrète en dégradé, dans la couleur de l’entité, inspirées du visuel fourni. Moyennes par cinq minutes sur six heures, sans relier les trous de données. Aucun historique fictif.

## Vérifier après mise à jour

Mettre à jour vers **0.2.0b13** dans Marketplace/HACS, redémarrer HA une fois puis recharger le panneau. Conserver l’entrée et les associations existantes.

Dans **Configuration → Conso Maison**, choisir Calcul automatique EMS. Vérifier le choix réseau, la présence de solaire et des batteries actives, et confirmer le même périmètre AC. Le champ de capteur maison existant est désactivé dans ce mode. Le détail du calcul dans Vue d’ensemble indique toute source bloquante : ne pas décocher un équipement présent pour contourner son absence de mesure.

Exemple testé : solaire 2 000 W + réseau −300 W − charge batterie 500 W + décharge 0 W = **1 200 W**. Le cumulus reste compris dans ces 1 200 W. Ce total mesure la consommation physique, indépendamment de la puissance achetée au réseau.

Une puissance interne de pack batterie (DC) peut différer de la puissance AC à cause des pertes de conversion. Choisir les puissances côté installation pour un bilan précis. Les mises à jour des capteurs peuvent être décalées : un bilan négatif est signalé, jamais forcé à zéro.

Les commandes physiques restent désactivées ; aucune automatisation existante n’est modifiée. Les indicateurs journaliers apparents conservent leurs hypothèses de la b12.
