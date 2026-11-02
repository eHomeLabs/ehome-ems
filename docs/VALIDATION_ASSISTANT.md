# Assistant et validation — 0.2.3

L'assistant initialise les associations. Après la première configuration, les raccourcis du panneau permettent les modifications ciblées ; la roue de l'intégration permet volontairement de reprendre le parcours.

1. Associer les sources réseau puis solaire.
2. Choisir une source Conso Maison existante ou le bilan automatique AC.
3. Déclarer les batteries et leurs rôles, puis les usages et appareils.
4. Associer les compteurs quotidiens, le tarif fixe et la météo facultative.
5. Vérifier le résumé : valid vert ; autres qualités rouges. Corriger les groupes via leurs raccourcis.
6. **Continuer vers la confirmation**, en dernière position, puis enregistrer.

Annuler abandonne les modifications non enregistrées. Renommer un équipement conserve ses identifiants. La qualité numérique ne valide pas le périmètre physique ; vérifier les signes et les unités en comparant aux sources.

## Reproduire les contrôles

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -q
python -m compileall -q custom_components tests scripts
node --test tests/test_panel_frontend.mjs
```

Pour le navigateur : installer les dépendances de test, préparer les icônes puis Chromium comme dans la CI et lancer `node scripts/validate_panel_browser.cjs`. La CI exécute aussi `scripts/validate_home_assistant.py` avec HA 2026.9.1 et 2026.11.0b0 sous Python 3.14, puis construit l'archive et son SHA-256.

Les tests couvrent bilans, signes, unités, refus des boucles de sources, stock batterie, SOC, droits administrateur, conflits de modification, préservation des associations, cycle reload/unload, tendances, calcul journalier, fuseau HA et rendu desktop/mobile. Les captures sont produites avec des données simulées, sans connexion à une installation personnelle.

Le retour utilisateur confirme que la b15 fonctionne sur son installation. Cela ne constitue pas une certification de tous les matériels ni une validation officielle HACS. La 0.2.3 conserve ce socle fonctionnel ; les résultats détaillés de sa passe sont dans [REVUE_0_2_3.md](REVUE_0_2_3.md).
