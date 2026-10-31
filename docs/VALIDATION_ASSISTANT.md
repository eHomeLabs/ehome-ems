# Premier assistant du lot A — validation

Branche de développement, sans publication HACS ni validation matérielle.
Le périmètre est limité aux puissances réseau, solaire et maison. Le stockage,
les usages, les énergies journalières et le dashboard restent à développer.

## Parcours codé

1. Réseau : capteur global signé et/ou mesures séparées disponibles, tous facultatifs.
   Ces capteurs sont des miroirs indépendants ; ils ne sont jamais sommés.
2. Photovoltaïque : une mesure totale facultative.
3. Maison : une consommation totale mesurée facultative.
4. Vérification : aperçu normalisé en W et état de qualité, menu de correction.
5. Confirmation : seul point d'enregistrement. Retour possible à la vérification.

Au moins une mesure est nécessaire pour enregistrer. Les associations utilisent
les mêmes clés que V0.1 ; aucune migration de données n'est nécessaire.
L'ancien mécanisme de rechargement de l'entrée est conservé.
La reprise des étapes fonctionne pendant le parcours ouvert ; fermer ou annuler
le parcours abandonne les modifications non enregistrées.

Une mesure temporairement indisponible peut être associée si son unité W/kW est
encore connue. Les capteurs absents ou d'unité inconnue doivent être corrigés.
Le capteur réseau global conserve sa convention de signe ; la sélection de
convention et la normalisation du réseau vers import positif restent à développer
avant les calculs de bilan. L'export séparé est une magnitude positive.
L'aperçu indique les erreurs numériques ou de direction sans inventer un zéro.

## Vérifications automatisées

Installer les dépendances de requirements-test.txt puis exécuter :

```sh
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
```

Les tests couvrent conversion et signes, données absentes, transitions du
parcours, modules ignorés, confirmation explicite, doublons, unités incorrectes,
sources disparues, refus des miroirs même renommés, reprise des réglages V0.1,
priorité des options et suppression d'une association.

Les tests du parcours utilisent Voluptuous et des doubles minimaux des API HA.
Ils ne valident ni le rendu des sélecteurs/menus dans HA, ni les registres
réels, ni le rechargement des entités.

## À vérifier sur une instance de développement Home Assistant

- Affichage français et anglais des écrans, menus, champs et erreurs.
- Configuration avec réseau seul, solaire seul et réseau/solaire/maison.
- Aperçu des valeurs W/kW, export négatif et source temporairement indisponible.
- Depuis l'aperçu, corriger chaque groupe puis confirmer.
- Annuler dans les options : conserver exactement les réglages précédents.
- Sur une entrée V0.1 : retrouver les associations, effacer un champ, enregistrer,
  vérifier le rechargement sans redémarrage complet de HA.
- Vérifier la conservation des identifiants uniques des capteurs inchangés.
- Tester une suppression de source entre l'aperçu et la confirmation, puis corriger.
- Vérifier qu'aucun service d'équipement n'est appelé.

Ces vérifications HA réelles restent à effectuer avant une release installable.
