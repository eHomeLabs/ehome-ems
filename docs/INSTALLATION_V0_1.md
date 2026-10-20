# Premier essai eHome EMS V0.1 sur Home Assistant OS

> Version pilote **non encore validée sur Home Assistant réel**. Fonctionnement en lecture seule ; sauvegarde complète conseillée.

## Installer

1. Depuis Home Assistant, réaliser une **sauvegarde complète**.
2. Dans **HACS → menu ⋮ → Dépôts personnalisés**, ajouter `https://github.com/eHomeLabs/ehome-ems`, catégorie **Intégration**. Le dépôt étant privé, HACS peut ne pas pouvoir y accéder : dans ce cas, utiliser l'installation manuelle ci-dessous.
3. Si le dépôt apparaît, télécharger l'intégration eHome EMS. Sinon, récupérer le dépôt privé depuis GitHub (authentification requise), puis copier **le dossier** `custom_components/ehome_ems` dans `/config/custom_components/ehome_ems` avec File Editor, Samba ou SSH.
4. Redémarrer **Home Assistant Core** depuis les paramètres HA (pas le Raspberry Pi).
5. Ouvrir **Paramètres → Appareils et services → Ajouter une intégration → eHome EMS**.

## Associer les capteurs

| Champ eHome EMS | Entité |
|---|---|
| Signed grid power | `sensor.sem_linky_power` |
| Grid import power | `sensor.import_reseau` |
| Grid export power | `sensor.injection_reseau` |
| Solar production power | `sensor.prod_solaire_additionnee` |
| Home consumption power | `sensor.conso_reelle_maison` |

Les cinq sources sont annoncées en **W**. Le réseau signé utilise **positif = import, négatif = injection**. Les autres mesures sont reprises telles quelles, sans déduction.

## Vérifier

1. Dans **Outils de développement → États**, chercher `eHome EMS` et comparer les valeurs aux capteurs sources.
2. Vérifier qu'une source indisponible produit un état indisponible.
3. Dans **Paramètres → Appareils et services → eHome EMS → Configurer**, changer temporairement une association et enregistrer : les capteurs doivent se mettre à jour après le rechargement de l'intégration, **sans redémarrer le Pi**.
4. Revenir aux cinq associations initiales.
5. En cas de problème, consulter **Paramètres → Système → Journaux** et rechercher `ehome_ems` ; transmettre la trace d'erreur (sans secrets).

## Limites de la V0.1

- Pas de dashboard, automatisation, commande d'équipement ou détection automatique.
- Les cinq capteurs EMS sont des miroirs **de test** des entités HA existantes ; ils pourront être remplacés par un modèle sans doublons dans une version ultérieure.
- Les changements de **configuration** déclenchent un rechargement de l'intégration. Les changements de **code Python** nécessitent généralement un redémarrage de Home Assistant Core.
- HACS peut refuser un dépôt privé selon les autorisations disponibles. Dans ce cas, la copie manuelle reste la procédure de test recommandée.
