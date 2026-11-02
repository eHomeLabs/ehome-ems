# eHome EMS 0.2.5 — Température des usages et batteries électriques

- Le champ température des usages accepte maintenant les entités `input_number` en plus des `sensor`, dans le panneau, l’assistant HA et le changement ciblé de source.
- L’aide numérique doit avoir l’unité **°C** ou **°F** ; les °F sont convertis en °C. Une source sans unité, invalide ou indisponible ne devient pas une température inventée. La valeur affichée correspond à la source sélectionnée : un maximum du jour reste un maximum du jour.
- L’onglet **Stockage** affiche uniquement les batteries électriques. Le cumulus reste dans **Usages**, avec ses associations, son objectif quotidien et ses commandes manuelles.
- Les réglages F1ATB HTTP/MQTT et les configurations existantes sont conservés.

Mettre à jour depuis HACS / Marketplace, redémarrer Home Assistant Core, puis recharger le navigateur. Vérifier **Interface 0.2.5 · Intégration 0.2.5**. Ne pas supprimer l’entrée existante.

Validation : tests Python (164), frontend (19), parcours desktop/mobile et intégration HA simulée incluant une aide numérique de température, ses changements de valeur, sa conversion °F/°C et son indisponibilité. Aucun appareil personnel n’est commandé par ces tests.

[Installation](INSTALLATION.md) · [Usages](USAGES_OBSERVATION.md)
