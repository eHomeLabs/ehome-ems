# eHome EMS — Guide Home Assistant

**eHome EMS — Universal Energy Manager**  
*Votre installation. Vos équipements. Votre énergie. Un EMS sur mesure.*

> **Statut : conception.** L'intégration HACS n'est pas encore publiée ; ce guide présente le parcours cible, pas une procédure actuellement exécutable.

## Architecture validée

eHome EMS est exclusivement une intégration personnalisée Home Assistant, installable via HACS, sans serveur autonome RPi5, Raspberry Pi OS, Docker ni base externe obligatoire.

## Parcours utilisateur cible

1. Installer eHome EMS depuis HACS lorsqu'une version testable sera publiée.
2. Ajouter l'intégration dans les paramètres Home Assistant.
3. Choisir les modules : réseau, PV, batteries, eau chaude, chauffage/climatisation, VE, autres charges.
4. Confirmer les entités détectées ou les sélectionner manuellement.
5. Vérifier unités, sens des flux, capacités et cohérence des mesures.
6. Générer puis personnaliser le dashboard Lovelace.
7. Activer ultérieurement des scénarios d'optimisation avec confirmation et garde-fous.

## Feuille de route

- **V0.1** : intégration HACS, configuration, réseau/PV/maison en lecture seule.
- **V0.2** : dashboard automatique et personnalisable.
- **V0.3** : batteries, eau chaude, chauffage/climatisation et borne VE.
- **V0.4** : automatisations sécurisées.
- **V0.5** : prévisions et IA facultative.

## Documentation

- [Présentation du projet](../../README.md)
- [Cahier des charges](../CAHIER_DES_CHARGES.md)
- [Abandon du serveur autonome RPi5](../DEPLOIEMENT_RPI5.md)

## Pages historiques obsolètes

Les anciennes pages `01-Introduction.md` à `10-Journal-installation.md` décrivent l'installation du serveur RPi5. Elles ne doivent plus être suivies pour eHome EMS ; elles seront archivées ou remplacées progressivement.
