# Vue automatique et copie modifiable — 0.2.0b5

Après confirmation de l'assistant et chargement de l'intégration, une entrée
eHome EMS apparaît dans la barre latérale. Aucune copie de YAML ni ajout manuel
de ressource frontend n'est nécessaire. Le paquet contient le module JavaScript
dans custom_components/ehome_ems/frontend/ehome-panel.mjs.

## Vue gérée

La vue automatique est un panneau personnalisé Home Assistant, en observation.
Elle affiche les mesures, jauges, batteries, usages et qualité issus du même
générateur que l'export natif. Les valeurs suivent les états HA sans commande.
Les mesures indisponibles restent explicitement indisponibles, sans zéro inventé.

L'onglet Historique de cette première vue ouvre la fiche historique native de
chaque mesure. Il ne rend pas encore une courbe synchronisée directement dans
le panneau. La copie native dispose de la carte history-graph habituelle.
Les flux animés et bilans journaliers EMS ne font pas partie de cette étape.

Les changements de configuration rechargent ce panneau. Actualiser permet
aussi de relire les associations, notamment après un renommage d'entité.
La vue suit la langue FR/EN de l'interface.

Le chemin est propre à l'entrée d'intégration. Un chemin déjà occupé n'est pas
écrasé. Le panneau est retiré au déchargement de l'entrée, puis réenregistré au
rechargement. Cela ne touche pas les autres dashboards.

## Copie indépendante

Le bouton Créer une copie modifiable est affiché aux administrateurs.
Il utilise les API WebSocket publiques de HA pour créer un nouveau dashboard
Lovelace natif avec un chemin aléatoire, puis enregistrer la configuration.
La copie est réservée aux administrateurs par défaut ; ce réglage peut être
modifié ensuite dans HA.

Cette copie est modifiable dans les éditeurs habituels de HA. Elle ne suit pas
les régénérations de la vue gérée : ses personnalisations sont conservées.
Une autre copie crée un autre dashboard, sans mise à jour forcée de la précédente.
Les requêtes serveur exigent les droits administrateur.

Si la création échoue sur un chemin occupé, aucune sauvegarde n'est tentée sur
ce chemin. Si la création réussit mais que l'enregistrement échoue, une copie
vide peut rester ; le message fournit son lien. Aucune suppression ni restauration
automatique n'est tentée sur un dashboard.

## Tests et limites

- Tests JavaScript : création/sauvegarde ciblées, collision sans écrasement,
  échec de sauvegarde sans suppression, données absentes et signe réseau,
  identifiants de copie sur HTTP local.
- Moteur HA réel : enregistrement/retrait du panneau, fichier JS servi avec
  type JavaScript, endpoint authentifié, copie native par les API WS,
  conservation d'une personnalisation après reload et refus d'un utilisateur
  non administrateur.
- Chromium sur données simulées : rendu 390 px et 1 440 px, absence de débordement,
  états indisponibles, onglets, ouverture d'historique et double clic de copie.

Le test moteur utilise une configuration temporaire, un serveur limité à
127.0.0.1 et une détection réseau simulée pour isoler l'hôte. Le test navigateur
utilise une fixture, pas le navigateur connecté à l'installation de l'utilisateur.
Le rendu complet dans l'application Android et le shell HA reste à vérifier
sur l'installation physique.
