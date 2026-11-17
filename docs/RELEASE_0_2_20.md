# eHome EMS 0.2.20 — Énergie quotidienne de tous les appareils

- Les compteurs déclarés Aujourd’hui sont lus directement en Wh/kWh, même sans historique ou rapport récent.
- Les compteurs cumulatifs utilisent la différence depuis minuit. Si l’historique manque mais que l’état courant HA est resté valide et inchangé depuis avant minuit, il constitue lui-même la référence : 0 kWh aujourd’hui, y compris pour une borne sans recharge.
- Cette logique commune s’applique aux appareils, usages et équipements photovoltaïques. Une puissance au repos ne suffit jamais pour inventer une énergie nulle. Un compteur absent, invalide ou sans référence exploitable reste indisponible.
- Dans la vue d’ensemble, le coût de la borne correspond désormais à son énergie du jour ; le détail des sessions reste dans Usages. Un compteur de session seul ne permet pas de reconstituer une journée et n’est pas assimilé à un compteur cumulatif.

Mise à jour : actualiser les informations du dépôt dans HACS, installer **0.2.20**, redémarrer HA puis rouvrir le tableau de bord. Les associations sont conservées. Vérifier que la période configurée pour chaque compteur correspond à sa nature réelle (Aujourd’hui / Cumul total / Session).

Tests simulés : compteur stable avant minuit, première mesure après minuit, compteurs journaliers, Wh/kWh, énergie absente/invalide, borne à 0 kWh et coût nul, conservation des sessions. Aucun équipement réel commandé.
