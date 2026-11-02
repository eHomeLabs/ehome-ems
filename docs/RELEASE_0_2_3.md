# eHome EMS 0.2.3

- Onglet Photovoltaïque ajouté après Stockage : micro-onduleurs, onduleurs DC et hybrides, ajout/modification/retrait, sources AC/DC distinctes, énergie et métadonnées.
- Aucune agrégation implicite des équipements dans le total solaire ou le bilan Maison. La configuration existante reste la référence.
- Type Cumulus / chauffe-eau distinct du Routeur solaire ; profil F1ATB guidé, mesures facultatives si une cible est renseignée.
- Page native accessible et commandes MQTT manuelles explicites : forçages temporisés, libération et paramètres de mode/seuil/ouverture. Les réglages ne remplacent pas la configuration permanente du routeur.
- Documentation, wiki et captures mis à jour. Les anciens cumulus et les fiches PV sont conservés lors de la reprise de l’assistant.

Mettre à jour en conservant l’entrée existante, redémarrer HA Core pour charger le code Python puis recharger le navigateur. Les commandes F1ATB sont désactivées par défaut. Aucune commande automatique ni connexion à un appareil personnel pour les tests.

[Photovoltaïque](PHOTOVOLTAIQUE.md) · [F1ATB](ROUTEUR_F1ATB.md) · [Installation](INSTALLATION.md)
