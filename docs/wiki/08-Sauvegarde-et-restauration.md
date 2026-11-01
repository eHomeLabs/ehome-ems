# 08 — Sauvegarde et mises à jour

[Accueil](Home.md) · [Suite : dépannage](09-Depannage.md)

La sauvegarde HA doit conserver la configuration de l'entrée EMS et les données historiques nécessaires. Les associations sont dans les données/options de l'intégration ; les priorités de simulation sont conservées. Le journal des 20 derniers scénarios est en mémoire et ne survit pas à un redémarrage HA.

| Changement | Redémarrage global HA |
| --- | --- |
| Source, appareil, icône, tarif, météo | Non : enregistrer suffit |
| Priorités de simulation | Non |
| Installation ou mise à jour du code Python | Oui : HA Core doit charger le nouveau code |
| Affichage resté en cache | Recharger le navigateur |

Pour migrer de la b15 à la 0.2.2, conserver l'entrée, mettre à jour puis redémarrer Core une fois et recharger le navigateur. Aucun redémarrage du système hôte n'est demandé.

Pour revenir à la b15, réinstaller ses fichiers et redémarrer HA Core. Les nouveaux champs 0.2.2 sont facultatifs ; désactiver les commandes et conserver une sauvegarde compatible avant de revenir à une ancienne version. Conserver une sauvegarde compatible pour les futures évolutions de format.

[Installation et retour arrière](../INSTALLATION.md)
