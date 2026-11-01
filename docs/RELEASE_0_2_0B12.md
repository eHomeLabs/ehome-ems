# eHome EMS 0.2.0b12 — réglages directs et dashboard affiné

- Affichages numériques limités à deux décimales, sans réduire la précision des mesures ni des calculs. Valeurs indisponibles en rouge, qualité `valid` en vert.
- Courbes en ligne sans remplissage, moyennes par tranches de cinq minutes sur six heures. Les données manquantes et coupures ne sont pas reliées.
- Ajout, modification et retrait des appareils directement dans **Mes Appareils**. Les formulaires ciblés existent aussi pour réseau, solaire, maison, batteries, usages, compteurs journaliers et tarif depuis **Configuration**. La roue crantée de l’intégration conserve l’assistant complet.
- Écritures réservées aux administrateurs, révision concurrente contrôlée, sources/unités/doublons et bilan AC validés. Les associations non concernées et les identifiants existants sont conservés. Aucune commande d’équipement.
- Navigation : **Vue d’ensemble → Mes Appareils → Stockage → Usages → Historique → Aujourd’hui → Stratégie → Configuration**.
- **Export** remplace Injection dans les libellés. Dans le flux, Import est rouge et Export bleu ; carte réseau et flèches suivent le sens mesuré. Le seuil d’animation reste de 10 W.
- Carte de borne de recharge avec visuel dédié, puissance, énergie et période du compteur, état suivi. Le bouton de copie modifiable est retiré ; aucune copie existante n’est effacée.
- Maison de jour ajoutée, maison de nuit conservée. Bascule automatique selon le fuseau de HA : jour de 07:00 à 18:59, nuit de 19:00 à 06:59, contrôle toutes les 30 secondes, également à chaque mise à jour des états.
- **Aujourd’hui** : Autonomie et Autoconso apparentes, valeurs Import/Export et parts respectives dans les échanges réseau.

## Définition des indicateurs du jour

Autonomie apparente = `(énergie maison − import) / énergie maison × 100`.
Autoconso apparente = `(production solaire − export) / production solaire × 100`.
Parts Import/Export = chaque énergie divisée par la somme Import + Export.

Ces indicateurs sont explicitement apparents : ils supposent des compteurs couvrant le même jour et le même périmètre, et pour l’autoconso un export provenant du solaire. Une batterie chargée sur le réseau, sa variation de stock ou un export de batterie peuvent biaiser l’interprétation solaire. Aucun suivi d’origine de l’énergie stockée n’est inventé. Zéro au dénominateur, mesure absente ou bilan incohérent donnent « Indisponible », pas un pourcentage forcé entre 0 et 100.

Les coûts restent des équivalents estimés à tarif fixe configurable, hors abonnement, tarifs horaires et revente. Pour une consommation du jour, associer un compteur remis à zéro chaque jour (par exemple Utility Meter), jamais son cumul depuis installation. Choisir « Aujourd’hui » ne transforme pas un cumul en compteur journalier.

## Installer et tester

Depuis Marketplace/HACS, dépôt personnalisé **Intégration** : `https://github.com/eHomeLabs/ehome-ems`, préversion **0.2.0b12**. Conserver l’entrée actuelle, mettre à jour puis redémarrer HA une fois et recharger l’application. Les changements suivants via le dashboard rechargent seulement l’intégration.

Ajouter un appareil depuis Mes Appareils, le modifier puis retirer son suivi. Dans Configuration, essayer un raccourci (sans dérouler l’assistant), puis vérifier que les autres associations restent présentes. Seuls les administrateurs disposent des actions d’écriture. Les capteurs sources et les équipements ne sont jamais supprimés par le retrait d’une association.

Vérifier Aujourd’hui, les valeurs à deux décimales, la couleur du réseau dans les deux sens, le seuil 10 W et la température cumulus facultative. Les courbes nécessitent History/Recorder. L’installation HA réelle de l’utilisateur n’est pas modifiée lors des validations en environnement simulé.
