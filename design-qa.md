# Validation — priorités et scénarios manuels 0.2.0b10

final result: passed

## Référence et preuves

Direction visuelle : maquette globale validée `generated_images/exec-f13f025c-7b57-4a86-adef-ef9e1745b156.png` (1536 × 1024), avec navigation haute demandée ensuite. La vue d'ensemble conserve cette organisation. Les nouveaux formulaires étendent les composants existants ; aucune maquette détaillée du formulaire n'avait été demandée.

Code vérifié : `c6cead66114069ec56efeaf9a0926477b9920985`.
Exécution réussie : https://github.com/eHomeLabs/ehome-ems/actions/runs/41246726433.
Artefact `panel-preview-simulated` : desktop.png, mobile.png, captures du flux au repos, du sélecteur de source et des nouveaux formulaires/résultats.

Viewports CSS : 1440 × 1600 et 390 × 844, densité 1. Captures régionales : simulation-editor-desktop.png (1350 × 292), simulation-editor-mobile.png (316 × 598), simulation-result-desktop.png (1350 × 283), simulation-result-mobile.png (316 × 526).

La maquette et la capture desktop ont été juxtaposées à largeur commune 768 px, sans étirement. Les formulaires et résultats ont été ouverts à leur résolution native pour le contrôle régional. La navigation sticky peut couvrir le bord supérieur d'une capture isolée lorsqu'elle est prise pendant le défilement ; elle ne masque pas durablement une ligne du formulaire.

## Parcours inspecté

- Paramètres initiaux : tous les équipements exclus du scénario, limites à zéro.
- Inclusion de Zendure, plafond 1000 W, déplacement de Cumulus au-dessus de Zendure, sauvegarde.
- Budget hypothétique 1500 W : Zendure reçoit 1000 W, Cumulus et véhicule exclus, reliquat 500 W.
- Chaque résultat montre les minima/plafonds utilisés et la raison, sans modifier le flux réel.
- Lecteur : paramètres en lecture seule, pas de bouton d'enregistrement ; simulation sur configuration enregistrée autorisée.

Le banc navigateur utilise un résultat connu pour contrôler l'interface. Le moteur Python est testé séparément sur les contraintes et la conservation ; le scénario HA utilise les vrais endpoints WebSocket.

## Surfaces vérifiées

- Typographie : police et hiérarchie HA conservées, valeurs et unités lisibles. Libellés explicites des champs et des boutons Monter/Descendre.
- Espacement : grille desktop, deux champs côte à côte sur mobile, nom et commandes de déplacement sur une ligne dédiée. Résultats repliés sans débordement horizontal du dashboard.
- Couleurs : palette précédente conservée, contrôle coché distinct d'un interrupteur matériel. Badge Observation toujours visible ; pas d'état automatique présenté comme actif.
- Images : maison et MDI inchangés. Aucune nouvelle illustration ou icône dessinée comme substitut.
- Texte : budget hypothétique explicite, pas d'inférence à partir de l'injection. Hypothèses, limites non matérielles, absence de contraintes SOC/échéances/régulations et absence de commande expliquées. Allocations distinctes de consommations supplémentaires à additionner.

Aucun écart P0/P1/P2 constaté. La navigation haute et la densité plus aérée que l'image de présentation sont des adaptations déjà retenues. P3 : améliorer encore le maintien du focus après déplacement d'une ligne au clavier ; le déplacement par boutons fonctionne et reste accessible.

## Validation fonctionnelle

- Tests du répartiteur : priorité, minimum non atteint, plafond, exclusion secours/DC, configuration absente/invalide, identifiants inconnus/dupliqués, type/limites du budget et changements concurrents.
- 200 scénarios déterministes vérifient conservation du budget et respect des bornes ; le même watt n'est pas attribué deux fois.
- Sauvegarde des priorités préservant les sources ; copie indépendante des réglages au démarrage de l'assistant de modification.
- Moteurs HA 2026.9.1 et 2026.11.0b0 : sauvegarde/reload, refus de révision périmée, refus d'écriture pour lecteur, lecteur autorisé à simuler, journal limité à 20 entrées et conservé sur reload.
- Écoute des événements call_service pendant les simulations HA : aucun appel émis.
- Chromium : formulaire, ordre sauvegardé, paramètres non enregistrés bloquant la simulation, résultat/reliquat, affichage des raisons et limites, accès lecteur, absence d'erreurs JavaScript.
- Régressions du flux 10 W, batterie au repos, appui prolongé, copie native, historique et module versionné conservées dans la même validation.

## Limites du lot

Pas de budget calculé depuis les mesures, pas de boucle d'arbitrage en temps réel, pas de contrainte SOC/réserve/échéance, pas de consigne matérielle. Le journal est en mémoire (20 résultats), perdu au redémarrage HA ou au retrait de l'entrée. Les priorités persistent dans les options HA.

La validation sur le shell Android et le RPi4 physique reste à confirmer. Ce lot est un répartiteur hypothétique explicable, pas une validation de pilotage automatique ou du fonctionnement matériel des équipements.
