# Routeur solaire F1ATB — configuration et commandes manuelles

Dans Usages, sélectionner le type **Routeur solaire** et le profil **F1ATB**. Le cumulus conserve son type thermique distinct. Les anciens usages « routeur/cumulus » restent compatibles avec le profil générique.

## Première configuration

1. Intégrer les données du routeur dans HA, par exemple via son MQTT et la découverte HA. Les capteurs sont facultatifs pour une fiche de paramétrage : renseigner au moins une page web valide ou un topic exact.
2. Saisir l’adresse HTTP/HTTPS de sa page native si souhaité. Aucun mot de passe ou identifiant de broker n’est demandé par EMS.
3. Indiquer la sortie réelle : SSR, Triac ou PWM, puis le topic exact **NomMQTTDuRouteur/NomDeLAction**, tel qu’il est configuré sur le F1ATB. Ni préfixe de découverte ni wildcard à substituer à ce topic.
4. Dans la page native F1ATB, activer la souscription au forçage des actions via MQTT. Vérifier la compatibilité de son firmware avec la documentation ; le format de topic décrit est celui de V15 et suivantes.
5. Cocher la confirmation puis activer explicitement les commandes MQTT dans EMS. Enregistrer n’envoie aucun ordre. L’intégration MQTT HA doit fournir le service de publication.

![Paramétrage F1ATB](screenshots/router-f1atb.png)

## Commandes disponibles

| Action EMS | Charge utile MQTT |
| --- | --- |
| Forcer On pendant 30 minutes | `{"tOnOff":30}` |
| Forcer Off pendant 40 minutes | `{"tOnOff":-40}` |
| Libérer le forçage | `{"tOnOff":0}` |
| Limiter l’ouverture d’une période existante | `{"Periode":0,"OuvreMax":60}` |

La durée est bornée à 1–1 440 minutes. Le mode concerne l’action et peut prendre effet immédiatement ; ce n’est pas la programmation du mode d’une période future. L’index de période, de 0 à 7, doit correspondre à une période déjà créée sur le routeur. EMS ne crée pas d’horaires et ne modifie pas les protections thermiques.

Les modes proposés dépendent de la sortie déclarée. OnOff est réservé au SSR, Decoupe au Triac ; PWM est proposé avec la sortie PWM. Les paramètres numériques facultatifs sont OuvreMax (0–100 %), SeuilOn et SeuilOff en W. Les champs laissés vides ne sont pas envoyés. Vérifier la pertinence des paramètres pour le mode et le firmware employés ; leurs bornes logicielles ne constituent pas un dimensionnement électrique.

## Portée et limites

Désactiver l’option dans EMS n’annule pas un ordre déjà transmis : libérer le forçage avant de désactiver, ou attendre son expiration sur le routeur. Une suppression de fiche n’envoie pas non plus d’ordre.

Les publications sont manuelles, réservées aux administrateurs, liées au topic enregistré et à la révision de configuration. QoS 0 et **retain=false** empêchent la rétention volontaire d’un ancien ordre. Le résultat indique une publication, sans prétendre confirmer la réception ni l’application par le routeur ; contrôler ses états et sa page native.

Les modifications via MQTT ne sont pas sauvegardées comme sa configuration permanente. Après redémarrage, le routeur reprend sa configuration enregistrée. Pour la configuration matérielle, les réseaux, les horaires et les sécurités, utiliser le bouton vers sa page native.

La documentation officielle et les échanges du projet signalent des différences de firmware ; un problème de paramètres MQTT de V17.02 a notamment été corrigé en V17.03. Cette interface n’est pas une validation matérielle de toutes les versions. Les tests EMS utilisent un service MQTT simulé, sans connexion à un routeur personnel. Aucune commande n’est envoyée par observation, rafraîchissement ou scénario.

Sources primaires : [Actions via MQTT](https://f1atb.fr/fr/documentation-routeur-photovoltaique-f1atb/pages-web-ihm/action/actions-via-mqtt/) · [Client MQTT](https://f1atb.fr/fr/documentation-routeur-photovoltaique-f1atb/pages-web-ihm/parametres/mode-expert/client-mqtt/) · [Correction V17.03](https://f1atb.fr/forum_f1atb/thread-2224-post-19696.html).

[Usages](USAGES_OBSERVATION.md) · [Photovoltaïque](PHOTOVOLTAIQUE.md)
