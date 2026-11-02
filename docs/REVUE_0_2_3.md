# Validation 0.2.3

Cette livraison ajoute la collection d’équipements photovoltaïques et le profil de routeur F1ATB. Les détails du socle précédent restent dans [la revue 0.2.2](REVUE_0_2_2.md).

## Contrôles

- 156 tests Python : métadonnées PV, types et unités, conservation des associations et du total solaire, reprise de la collection dans l’assistant, topics et URL, protocole opt-in, durées signées, libération, modes compatibles, bornes et absence de rétention MQTT.
- 19 tests JavaScript du socle et parcours Chromium desktop/mobile : ordre des neuf onglets, ajout/retrait d’un hybride, ajout d’un F1ATB, envoi uniquement sur clic, réglage et libération même si un autre champ du formulaire est invalide.
- La CI exécute HA 2026.9.1 et 2026.11.0b0 dans des installations temporaires : schéma PV sérialisable, CRUD sans changement du bilan, service MQTT simulé, contexte utilisateur, payload exact, refus d’un mode incompatible et refus des lecteurs.
- Archive de 28 fichiers, guides dédiés et dix captures du panneau réel avec données simulées. Liens Markdown/images locaux contrôlés.

Aucun service d’un équipement personnel ni broker réel n’est utilisé. Le contrôle des payloads documentés n’est pas une certification de tous les firmwares F1ATB. Un ordre publié n’est pas présenté comme une réception confirmée. Le mode MQTT concerne l’action ; la configuration des horaires et protections reste native.

Les fiches photovoltaïques ne sont pas automatiquement agrégées dans la production de référence. Pour un hybride, l’origine solaire d’une sortie AC peut être différente de sa puissance totale ; le périmètre et les sources restent à confirmer par l’utilisateur.

[Notes 0.2.3](RELEASE_0_2_3.md) · [Guide F1ATB](ROUTEUR_F1ATB.md) · [Photovoltaïque](PHOTOVOLTAIQUE.md)
