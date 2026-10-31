# Premier dashboard natif — branche de développement

Cette étape génère une configuration Lovelace modifiable avec les cartes natives
de Home Assistant, sans dépendance frontend supplémentaire. Elle n'est pas encore
le dashboard animé de la V2 et n'est pas une release HACS.

## Contenu

- Synthèse : puissances normalisées et jauges réseau/solaire/maison disponibles.
- Stockage : une section par batterie, avec rôle actif/secours et couplage AC/DC.
- Historique : courbes de puissance sur 24 h, si Recorder conserve ces entités.
- Qualité : attribut data_quality des mesures. La fraîcheur n'est pas encore évaluée.

Le SOC est en %, l'énergie restante mesurée en kWh. La jauge d'énergie n'est
proposée que si une capacité utile a été déclarée. Les jauges de puissance
utilisent par défaut 10 000 W, une échelle d'affichage indicative à personnaliser,
pas une limite de puissance commandée. Le réseau signé conserve la convention
de la source. Aucune interprétation du sens import/export n'est inventée.
Les capteurs séparés import/export restent des mesures indépendantes.

Les batteries actives, de secours et DC restent visibles séparément. Aucun total
de stockage, taux solaire, bilan d'énergie du jour ni flux animé n'est calculé.
Les états indisponibles sont laissés aux cartes natives, sans conversion à zéro.

## Génération sur une instance de développement

Après installation du code de cette branche et configuration de l'intégration :

1. Ouvrir Outils de développement → Actions.
2. Appeler ehome_ems.generate_dashboard avec, facultativement :

```yaml
action: ehome_ems.generate_dashboard
data:
  language: fr
  max_power_w: 10000
```

3. La réponse contient dashboard (configuration complète) et missing_entities.
   Copier uniquement le contenu de dashboard dans l'éditeur de configuration
   brute d'un NOUVEAU dashboard vierge, au format YAML ou JSON.
4. Vérifier les entités et échelles, puis enregistrer cette copie et la personnaliser.

L'action est en lecture seule : elle ne crée ni fichier, ni ressource frontend,
ni dashboard, et n'écrase aucun dashboard existant. Une nouvelle génération
renvoie une nouvelle copie ; elle ne met pas à jour la copie personnalisée.
L'ajout/retrait d'une batterie nécessite donc de générer une nouvelle configuration
et de reporter les changements choisis. La génération gérée et la stratégie
frontend restent à développer.

Les identifiants des miroirs sont résolus depuis le registre : un capteur renommé
est retrouvé à partir de son identifiant unique. Les entités désactivées ou
introuvables sont signalées dans missing_entities, sans utiliser silencieusement
la source brute. Corriger leur état puis régénérer si nécessaire.

## Validation

Les tests vérifient la génération, l'isolation des entrées, les échelles par unité,
les sources renommées/désactivées, l'action à réponse seule et l'absence de
commandes ou de modification de dashboard. Les tests d'API utilisent des doubles HA.

Restent à valider dans HA : disponibilité de l'action, restitution de la réponse,
collage de la configuration, rendu mobile/tablette/PC, états indisponibles,
historique Recorder et conservation de la copie après modification des options.
La génération native est une base fonctionnelle ; elle ne vaut pas validation
visuelle du dashboard V2 final.
