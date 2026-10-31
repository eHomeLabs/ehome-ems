"""Pure generation of an editable, native-card observation dashboard."""
from .const import SOURCES, BATTERY_SOURCES, CONF_BATTERIES

LABELS = {
    "fr": {
        "summary": "Synthèse", "storage": "Stockage", "history": "Historique",
        "quality": "Qualité des données", "power": "Puissances",
        "grid_power": "Réseau signé", "grid_import": "Import réseau",
        "grid_export": "Injection réseau", "solar_power": "Production solaire",
        "home_power": "Maison", "charge_power": "Charge", "discharge_power": "Décharge",
        "soc": "État de charge", "remaining_energy": "Énergie restante",
        "active": "Active", "backup": "Secours",
        "notice": "Observation · aucune commande. Réseau signé selon la convention de la source. "
                  "Échelles indicatives et modifiables, sans seuil de sécurité. "
                  "Les mesures absentes restent indisponibles ; aucun bilan solaire n’est estimé.",
        "empty": "Aucune mesure disponible dans le registre. Vérifiez les associations et les entités désactivées.",
        "storage_only": "Les mesures disponibles sont dans la vue Stockage.",
    },
    "en": {
        "summary": "Overview", "storage": "Storage", "history": "History",
        "quality": "Data quality", "power": "Power readings",
        "grid_power": "Signed grid", "grid_import": "Grid import",
        "grid_export": "Grid export", "solar_power": "Solar production",
        "home_power": "Home", "charge_power": "Charge", "discharge_power": "Discharge",
        "soc": "State of charge", "remaining_energy": "Remaining energy",
        "active": "Active", "backup": "Backup",
        "notice": "Observation · no commands. Signed grid follows the source convention. "
                  "Scales are indicative and editable, without safety thresholds. "
                  "Missing readings stay unavailable; no solar balance is estimated.",
        "empty": "No readings available in the registry. Check mappings and disabled entities.",
        "storage_only": "Available readings are in the Storage view.",
    },
}


def build_dashboard(mapping, entities, *, language="fr", max_power_w=10000):
    """Build a new configuration; never modify mapping, registry or dashboards.

    entities maps stable suffixes (grid_power, batteryid_soc, etc.) to registered
    mirror entity IDs. Source IDs are never substituted for missing mirrors.
    """
    labels = LABELS.get(language, LABELS["fr"])
    missing = []
    powers = []
    quality = []

    def entity_for(suffix):
        entity = entities.get(suffix)
        if not entity:
            missing.append(suffix)
        return entity

    def row(entity, name):
        return {"entity": entity, "name": name, "tap_action": {"action": "none"},
                "hold_action": {"action": "none"}, "double_tap_action": {"action": "none"}}

    def entities_card(title, rows):
        return {"type": "entities", "title": title, "show_header_toggle": False,
                "entities": rows}

    def gauge(entity, name, minimum=0, maximum=max_power_w):
        return {"type": "gauge", "entity": entity, "name": name,
                "min": minimum, "max": maximum,
                "tap_action": {"action": "none"}}

    def quality_row(entity, name):
        quality.append({"type": "attribute", "entity": entity,
                        "attribute": "data_quality", "name": name})

    summary_cards = [{"type": "markdown", "content": labels["notice"]}]
    main_rows, gauges = [], []
    for key in SOURCES:
        if not mapping.get(key):
            continue
        entity = entity_for(key)
        if not entity:
            continue
        main_rows.append(row(entity, labels[key]))
        gauges.append(gauge(entity, labels[key], -max_power_w if key == "grid_power" else 0))
        powers.append(entity)
        quality_row(entity, labels[key])
    if main_rows:
        summary_cards += [
            entities_card(labels["power"], main_rows),
            {"type": "grid", "columns": 2, "square": False, "cards": gauges},
        ]

    storage_cards = []
    for battery_id, battery in mapping.get(CONF_BATTERIES, {}).items():
        title = f"{battery['name']} · {labels[battery['role']]} · {battery['coupling'].upper()}"
        rows, battery_gauges = [], []
        for key in BATTERY_SOURCES:
            if not battery.get(key):
                continue
            entity = entity_for(f"{battery_id}_{key}")
            if not entity:
                continue
            rows.append(row(entity, labels[key]))
            quality_row(entity, f"{battery['name']} / {labels[key]}")
            if key == "soc":
                battery_gauges.append(gauge(entity, labels[key], maximum=100))
            elif key in ("charge_power", "discharge_power"):
                battery_gauges.append(gauge(entity, labels[key]))
                powers.append(entity)
            elif battery.get("capacity_kwh"):
                battery_gauges.append(gauge(entity, labels[key], maximum=battery["capacity_kwh"]))
        if rows:
            cards = [entities_card(title, rows)]
            if battery_gauges:
                cards.append({"type": "grid", "columns": 2, "square": False, "cards": battery_gauges})
            storage_cards.append({"type": "vertical-stack", "cards": cards})

    if not main_rows:
        summary_cards.append({"type": "markdown", "content": labels["storage_only"] if storage_cards else labels["empty"]})
    views = [{"title": labels["summary"], "path": "summary", "icon": "mdi:home-lightning-bolt",
              "cards": summary_cards}]
    if storage_cards:
        views.append({"title": labels["storage"], "path": "storage",
                      "icon": "mdi:battery", "cards": storage_cards})
    if powers:
        views.append({"title": labels["history"], "path": "history", "icon": "mdi:chart-line",
                      "cards": [{"type": "history-graph", "title": labels["power"],
                                 "hours_to_show": 24, "entities": powers}]})
    if quality:
        views.append({"title": labels["quality"], "path": "quality", "icon": "mdi:check-network",
                      "cards": [entities_card(labels["quality"], quality)]})
    return {"dashboard": {"title": "eHome EMS", "views": views}, "missing_entities": missing}
