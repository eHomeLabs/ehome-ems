# 07 — Valider l’installation et la V1

[Accueil](Home.md) · [Précédent](06-Configuration-sources.md) · [Suite : sauvegarde](08-Sauvegarde-et-restauration.md)

La recette sera remplie avec la date, la version testée et un résultat observé. **Aucun test sur le matériel réel n’a été effectué lors de la rédaction.**

## A. Socle matériel — à faire dès maintenant

- [ ] Le RPi démarre deux fois sans microSD.
- [ ] La racine et le démarrage sont sur NVMe.
- [ ] L’architecture est ARM64.
- [ ] SSH et la réservation DHCP restent fonctionnels.
- [ ] Horloge synchronisée, stockage disponible et alimentation stables.
- [ ] Docker et Compose passent leurs contrôles.

## B. Application — quand le prototype existe

| Scénario | Résultat attendu |
| --- | --- |
| Démonstration sans HA | L’interface fonctionne avec les données simulées |
| PV nul la nuit | Aucune production inventée |
| Import puis export simulés | Deux sens correctement identifiés |
| Charge puis décharge simulées | Sens batterie correct et SOC cohérent |
| Sous-compteur déjà inclus | Pas de double comptage |
| Source indisponible | État visible « indisponible », pas un faux zéro |
| Valeur trop ancienne | État visible « périmé » et dernière date connue |
| Unité inattendue | Mesure rejetée ou signalée explicitement |
| Redémarrage du service | Configuration et historique conservés |
| Redémarrage du RPi | Reprise des services et des volumes persistants |
| Affichage mobile | Flux et avertissements lisibles en français |
| Historique 24 h / bilan journalier | Bornes temporelles et unités correctes |

Faire d’abord ces tests avec des données simulées. Pour les sources réelles, observer les états existants sans provoquer de commande aux appareils depuis l’EMS.

## C. Contrôle de cohérence

Pour un périmètre où tous les flux sont mesurés au même point de référence :

```text
production PV + import réseau + décharge batterie
≈ consommation maison + export réseau + charge batterie
```

Cette relation est une vérification de cohérence, pas une formule à appliquer à tous les montages. Pertes, points de mesure AC/DC et décalages temporels peuvent créer un écart. Définir le périmètre et la tolérance avec les mesures réelles, sans masquer un écart inexpliqué.

Vérifier aussi les remises à zéro des compteurs, les trous de collecte et le passage de minuit. Un essai simulé à 1 000 W constants pendant une heure doit produire 1 000 Wh.

## D. Conditions de validation V1

- [ ] Aucun chemin de commande aux appareils.
- [ ] Aucun secret dans le dépôt, le frontend ou les journaux.
- [ ] Sources comparées à leurs mesures de référence.
- [ ] Historique conservé après redémarrage.
- [ ] Sauvegarde et restauration testées sur une copie.
- [ ] Écarts et décisions consignés dans le journal.

La V2 nécessite une validation distincte ; réussir la V1 n’autorise pas le pilotage.
