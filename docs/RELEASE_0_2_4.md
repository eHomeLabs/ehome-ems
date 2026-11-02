# eHome EMS 0.2.4 — Support natif F1ATB HTTP local

Le routeur solaire F1ATB peut être connecté directement à eHome EMS depuis **Usages**, sans installer une autre intégration F1ATB et sans MQTT. Le mode MQTT existant est conservé.

## Configuration

**Usages → Ajouter un usage → Routeur solaire → F1ATB → HTTP local direct** : saisir l’adresse IP ou l’URL de base, cliquer **Lire le routeur et ses actions**, puis choisir l’action concernée et enregistrer. Enregistrer ne commande pas le routeur.

Les commandes HTTP manuelles sont désactivées par défaut et réservées aux administrateurs après activation explicite.

## Fonctions

- Lecture locale des actions et de leur configuration, avec rafraîchissement des mesures toutes les 15 secondes.
- Capteurs HA : ouverture, état et minutes de forçage de l’action, disponibilité du routeur, import/export réseau, seconde voie de puissance et compteur cumulé, températures disponibles.
- Forçage On/Off temporisé de 1 à 1 440 minutes et retour en Auto, avec contrôle par relecture.
- Réglages enregistrés dans le routeur : forme d’onde, ouverture en marche forcée et ouverture maximale d’une période proportionnelle existante compatible.
- Configuration complète préservée, détection des modifications concurrentes avant écriture et sérialisation des échanges par routeur.
- Démarrage hors ligne et reconnexion sans bloquer EMS ; aucune valeur absente transformée en zéro.
- Interface et aide français/anglais, adaptée au desktop et au mobile.

Les mesures globales du routeur restent distinctes de l’action sélectionnée. Elles ne sont ni attribuées implicitement à chaque sortie, ni ajoutées au bilan Maison ou à la production solaire. Aucune commande n’est envoyée par observation, rafraîchissement ou scénario.

## Mise à jour

Mettre à jour via HACS / Marketplace, puis **redémarrer Home Assistant Core une seule fois** et recharger le navigateur. Les versions Interface et Intégration doivent afficher **0.2.4**. Conserver l’entrée EMS et ses associations ; les usages MQTT existants ne changent pas de transport et aucune commande n’est activée automatiquement.

Home Assistant **2026.9.1 minimum**. Aucun changement de firmware F1ATB n’est effectué par EMS.

## Validation et limites

162 tests Python et 19 tests frontend, parcours Playwright desktop/mobile, APIs HA réelles sur 2026.9.1 et 2026.11.0b0 avec routeur HTTP simulé : droits, mesures, conflits, commande non confirmée sans réessai, démarrage hors ligne, reconnexion et reload/unload. Ces contrôles ne constituent pas un essai sur matériel réel.

Protocole étudié dans le firmware officiel F1ATB V17.30 et dans l’intégration communautaire WillSpecIm/Integration-f1atb, sans dépendance à cette dernière. Les formats non reconnus sont refusés ; la compatibilité de tous les firmwares n’est pas garantie.

Les horaires détaillés, seuils On/Off, PID, GPIO, calibration, paramètres réseau et protections restent configurés depuis la page native dans cette première implémentation HTTP. Le firmware ne permet pas de verrouiller les modifications simultanées de sa propre page web entre lecture et écriture.

Si le résultat d’un ordre est non confirmé, vérifier le routeur avant de réessayer : l’ordre peut avoir été appliqué. Désactiver les commandes ou retirer une fiche n’annule pas un forçage déjà transmis ; le libérer ou attendre son expiration.

[Guide F1ATB](ROUTEUR_F1ATB.md) · [Installation](INSTALLATION.md)
