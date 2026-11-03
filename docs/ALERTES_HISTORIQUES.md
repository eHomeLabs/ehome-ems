# Historiques, interprétation et alertes (0.2.7)

Les valeurs W, kW, Wh et kWh sont accessibles au clic, au toucher ou à Entrée pour ouvrir les graphiques 24 h / 7 jours. Les sources d’origine sont utilisées, y compris lorsque leur nom a changé. Les trous de données restent visibles. L’absence de Recorder ou de rétention est signalée. Une énergie du jour calculée depuis un compteur cumulé ouvre l’historique de ce compteur, clairement indiqué ; le cumul n’est pas transformé en puissance. Pour une valeur agrégée, les composantes sont affichées séparément. L’appui prolongé ou Maj+Entrée permet toujours de changer une association.

Situation actuelle est un commentaire local à règles explicites, actualisé depuis les mesures. Il distingue surplus, import, charge et restitution batterie, consommation du circuit de chauffe et export. Il ne prétend pas avoir commandé le routeur, ni connaître l’origine de l’énergie stockée. Une situation incomplète est signalée.

## Total photovoltaïque

L’onglet additionne une puissance de production par équipement : DC si renseignée, sinon AC pour les onduleurs non hybrides. Un hybride exige une mesure DC solaire car sa sortie AC peut comprendre de la décharge batterie. Ce total mélange éventuellement des périmètres AC et DC : il reste indicatif et ne remplace pas la source solaire du bilan Maison AC.

L’énergie quotidienne additionne les compteurs uniques déclarés des équipements non hybrides. Un compteur total utilise la référence Recorder à minuit dans le fuseau HA ; les compteurs du jour sont utilisés directement. Les compteurs de session et les compteurs d’énergie hybrides sont exclus. La couverture est affichée ; une source associée indisponible rend le total suivi indisponible. Les doublons d’entité sont éliminés. Un compteur global et ses sous-compteurs ont des identifiants différents : l’utilisateur doit éviter de les déclarer ensemble comme productions distinctes.

## Alertes et Notifications

Dernier onglet, configuration administrateur ; journal lisible par les utilisateurs du panneau. Aucune alerte n’est ajoutée ou activée lors d’une mise à jour.

- **Import quotidien** : seuil en kWh (exemple 12), avec confirmation d’un compteur du jour civil qui se remet à zéro quotidiennement. Ce n’est pas un compteur cumulé à vie. Le seuil est strictement supérieur ; une notification maximum par jour civil HA. Une valeur dont la dernière mise à jour date de la veille ne déclenche pas l’alerte du nouveau jour.
- **Puissance d’import** : seuil en W et durée minimale configurable. W/kW sont convertis. Une notification par épisode ; une mesure revenue sous le seuil réarme l’alerte.
- **Entité indisponible** : état absent, unknown ou unavailable pendant une durée configurable, par exemple 5 minutes. Une notification par épisode ; le retour d’un état disponible réarme l’alerte. Un capteur qui reste bloqué sur une valeur numérique n’est pas détecté par cette règle.

Destination : notification persistante dans HA, ou service `notify.*` existant, par exemple l’application mobile. Les services nécessitant d’autres champs que `title` et `message` ne sont pas pris en charge dans cette version ; un échec apparaît au journal. Aucun destinataire extérieur n’est configuré automatiquement et aucun envoi de test implicite n’est effectué.

Les règles s’exécutent côté HA toutes les 30 secondes, même si le panneau est fermé. Les activations en cours sont conservées sur rechargement. Modifier une règle la réarme. L’intention d’envoi est enregistrée avant appel pour éviter les doublons : après une interruption, un envoi peut rester « non confirmé » plutôt que d’être réessayé. Une erreur n’est pas réessayée pendant le même épisode. Journal limité aux 50 derniers envois. Les alertes n’effectuent aucune commande d’équipement.
