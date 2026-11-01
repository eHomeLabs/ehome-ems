# eHome EMS 0.2.0b11 — Appareils et dashboard visuel

- Cartes de puissance colorées et courbes des six dernières heures issues de l’historique HA. Aucune courbe synthétique si l’historique est absent ; les indisponibilités et longues coupures ne sont pas reliées.
- Stockage : cartes batterie avec remplissage SOC, charge/restitution, énergie restante mesurée et autonomie indicative. Plusieurs batteries, dont secours, gardent leur rôle et leurs identifiants.
- Cumulus : température facultative, puissance, énergie avec période explicite et coût estimé du jour. Le pictogramme utilise une échelle de température 0–100 °C, pas une estimation de stock thermique.
- Nouvel onglet **Mes Appareils** et menu dans Configurer : ajouter/modifier/retirer frigo, lave-vaisselle, expresso… Puissance et énergie facultatives. Les appareils restent des sous-comptages et sont exclus des scénarios de pilotage.
- Nouvel onglet **Aujourd’hui**, alimenté par des compteurs journaliers explicitement associés. Tarif fixe facultatif en €/kWh ; estimations hors abonnement, tarification horaire et revente. Aucun montant calculé depuis un compteur de session/cumulé.
- Flux : maison centrale agrandie, cartes compactes colorées, liens lumineux et seuil d’animation conservé à 10 W. Les batteries actives AC disposent chacune de leur liaison ; les batteries de secours restent distinguées.

## Installer via Marketplace / HACS

Ajouter `https://github.com/eHomeLabs/ehome-ems` en dépôt personnalisé, catégorie **Intégration**, puis sélectionner la préversion **0.2.0b11** (activer l’affichage des versions bêta si nécessaire). Le dépôt reste en bêta ; il ne s’agit pas d’une validation au catalogue officiel.

Si l’intégration a déjà été copiée par ZIP, Marketplace/HACS peut ensuite gérer son dossier. Conserver l’entrée existante et ses associations. Redémarrer Home Assistant une fois après l’installation du code Python, puis recharger l’application/le navigateur. Les réglages suivants rechargent uniquement l’intégration.

Dans **Paramètres → Appareils et services → eHome EMS → Configurer**, passer les associations existantes, puis **Mes Appareils** et **Aujourd’hui et tarif**. Le tarif n’a aucune valeur par défaut. Associer uniquement des compteurs du jour remis à zéro à minuit ; pour un cumul, créer préalablement un compteur journalier HA (Utility Meter). Aucun helper n’est créé ni modifié automatiquement.

Pour Aferiy, ajouter une seconde batterie avec ses propres sources et choisir explicitement **Secours** ou **Active / AC** selon son rôle réel. Aucun ordre n’est envoyé aux équipements. Le mode observation reste actif.

## Limites

Les courbes nécessitent l’intégration History/Recorder et l’enregistrement des capteurs source. Leur chargement est groupé et limité à une requête par cinq minutes, sur les six dernières heures et au plus 100 sources. La carte conserve les états indisponibles.

La consommation maison conserve le périmètre choisi par l’utilisateur. Une source excluant le cumulus ne devient pas un total maison complet. Les appareils et usages ne sont jamais additionnés de nouveau à ce total.

Autonomie batterie : énergie disponible mesurée divisée par la puissance maison actuelle, sans pertes, réserve, partage entre batteries ni prévision. Elle ne constitue pas une autonomie garantie. L’origine de l’énergie stockée reste inconnue ; aucun gain solaire, taux d’autoconsommation ou d’autonomie n’est inventé à partir des charges/décharges.
