# eHome EMS 0.2.2

- Libellé « Tendance sur 15 mn » sur les cartes ; données insuffisantes signalées par la flèche horizontale et son aide.
- Tolérance de puissance négative configurable sur les appareils, 5 W par défaut. Les petits décalages deviennent 0 W avec valeur brute et correction tracées ; les autres erreurs restent indisponibles. Réseau et bilan Maison inchangés.
- Commandes On/Off manuelles : sélectionner une entité commandable et activer l’option par appareil. Les boutons lisent l’état HA et envoient une commande uniquement sur clic administrateur ; droits, état attendu, révision et concurrence vérifiés côté serveur.
- Objectif quotidien configurable en kWh pour les usages, dont le cumulus : 2,16 / 3 kWh = 72 %. Remplissage selon l’objectif, température séparée. Ce n’est pas la chaleur encore disponible ni un SOC de batterie.
- Réglages du cumulus accessibles depuis Usages et Stockage ; documentation et captures actualisées.

## Après mise à jour

Conserver l’entrée existante. Redémarrer Home Assistant Core pour charger le nouveau code puis recharger le navigateur. Les nouveaux champs sont facultatifs ; les commandes sont désactivées par défaut. Dans Modifier un appareil, choisir l’entité de commande et l’activer volontairement. Pour le cumulus, renseigner par exemple 3 kWh d’objectif quotidien.

Le pilotage automatique n’est pas ajouté. Observation, rafraîchissements et scénarios ne déclenchent aucun ordre. Les services de l’installation réelle n’ont pas été utilisés pour les tests : les essais utilisent des entités simulées.

[Installer](INSTALLATION.md) · [Usages et commandes](USAGES_OBSERVATION.md) · [Wiki](wiki/Home.md)
