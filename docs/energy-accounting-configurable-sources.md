# Bilans énergétiques — sources configurables et comparaison HA

Statut : spécification à implémenter et tester (aucune correction des calculs livrée par ce document).

## Constat (5 novembre 2026)
Comparaison sur la même journée affichée : solaire HA 14,60 kWh / EMS 10,91 kWh ; import HA 5,77 kWh / EMS 6,31 kWh ; export HA 0,58 kWh / EMS 0,94 kWh. Les 14,60 kWh HA comprennent la production toiture et la production de test. Ne pas attribuer ces écarts à une cause avant audit des sources, périodes et algorithmes.

## Contrat fonctionnel
- Séparer les capteurs de puissance instantanée (W), utilisés pour les flux, des compteurs d'énergie (Wh/kWh), utilisés pour les bilans.
- Pour **chaque direction réseau indépendamment** (import et export), proposer : un compteur d'énergie, plusieurs compteurs d'énergie complémentaires (HP/HC ou autre), ou intégration temporelle d'une puissance. Ne jamais imposer Zlinky, HP/HC, SEM ou Shelly.
- Autoriser les entités HA compatibles indépendamment de leur intégration (Shelly, SEM, Zlinky, MQTT, ESPHome, etc.).
- Permettre plusieurs sources de production PV, dont toiture + tests, sans doublon ; même principe pour charge et décharge des batteries.
- Ne jamais sommer un compteur total avec ses sous-compteurs. Signaler les chevauchements possibles et les unités incompatibles.
- Pour les compteurs cumulés, calculer les deltas sur la période locale choisie, en gérant les remises à zéro, changements d'état et données indisponibles ; pour HP/HC sommer les deltas individuels, sans supposer une activité simultanée.
- Pour le fallback W, intégrer séparément import et export à partir du signe convenu, gérer les trous de télémétrie et indiquer que la précision peut différer des compteurs.
- Ne pas modifier la formule de consommation maison instantanée : production + réseau signé - charge batterie + décharge batterie ; cumulus, VE et autres usages restent inclus.
- Préserver la configuration existante lors des migrations ; proposer une validation des sources sans réinitialiser les historiques.

## Diagnostic et validation
- Afficher pour chaque flux les entités retenues, méthode, unité, fenêtre temporelle, dernière mesure, état et éventuelles lacunes.
- Comparer à Home Assistant Énergie uniquement à sources et plages temporelles identiques, avec écart absolu et relatif.
- Tester : compteur unique import/export ; HP+HC ; solaire multi-sources ; batteries charge/décharge ; compteur cumulatif réinitialisé ; indisponibilité ; redémarrage ; passage minuit / changement d'heure ; absence de double comptage.
- Les valeurs doivent être cohérentes à l'arrondi près lorsque les sources et périodes sont identiques ; ne pas promettre une égalité en cas de sources différentes.

## Hors périmètre de ce document
Cette spécification ne prétend ni résoudre les écarts observés ni implémenter les sélecteurs de configuration. La PR actuelle contient par ailleurs un compteur d'énergie maison dérivé, à valider séparément.
