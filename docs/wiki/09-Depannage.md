# 09 — Dépannage

[Accueil](Home.md) · [Journal local](10-Journal-installation.md)

| Symptôme | Vérification |
| --- | --- |
| Conso Maison indisponible | Ouvrir son diagnostic ; vérifier source manquante, unité, signe, périmètre AC et politique d'âge |
| Bilan négatif | Comparer les contributions ; ne pas masquer l'erreur en forçant zéro |
| Température du cumulus indisponible | Vérifier la source de température ; sa puissance est une autre mesure |
| Flèche horizontale | Stabilité ou données historiques insuffisantes ; lire la mention sous la flèche |
| Historique 24 h absent | Vérifier l'enregistrement des sources dans History/Recorder |
| Coût quotidien indisponible | Vérifier tarif, période du compteur et référence historique à minuit |
| Stock batterie refusé | Wh/kWh, nature de stock et capacité ; confirmer explicitement une mauvaise classe HA si le stock est réel |
| Ancienne interface après mise à jour | Comparer Interface/Intégration dans Configuration ; redémarrer Core si code Python remplacé puis recharger le navigateur |
| Modification concurrente refusée | Actualiser avant de refaire la modification ; éviter d'écraser une autre session |

Pour un signalement, fournir version EMS, version HA, étape reproduite, qualité affichée et extrait de journal expurgé. Ne pas publier URL privée, jeton ni inventaire d'entités personnelles. Les sources se diagnostiquent d'abord dans leurs intégrations HA ; EMS ne remplace pas leur fonctionnement.

[Diagnostic du bilan](../CONSOMMATION_MAISON.md) · [Installation](../INSTALLATION.md)

Un On/Off désactivé indique un état inconnu, une commande en cours ou des droits insuffisants. Si la configuration ou l’état a changé entre affichage et clic, actualiser. Les actions manuelles se configurent séparément des capteurs de puissance.

Pour une petite valeur négative de consommation d’un appareil, vérifier le réglage de tolérance (5 W par défaut). Ne pas utiliser ce réglage pour masquer une véritable production ou modifier le signe du réseau.
