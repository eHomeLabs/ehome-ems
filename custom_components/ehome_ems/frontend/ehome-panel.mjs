// Managed view uses authenticated HA state; editable copies use public WS APIs.
export function newCopyToken(source = globalThis.crypto) {
  if (typeof source.randomUUID === "function") return source.randomUUID();
  return Array.from(source.getRandomValues(new Uint32Array(4)),
    value => value.toString(16).padStart(8, "0")).join("");
}
export async function createIndependentCopy(hass, dashboard, token = newCopyToken()) {
  if (!/^[a-zA-Z0-9-]+$/.test(token)) throw new Error("Invalid copy identifier");
  const url = "ehome-ems-copy-" + token.toLowerCase();
  await hass.callWS({
    type: "lovelace/dashboards/create", title: "eHome EMS · copie",
    url_path: url, icon: "mdi:home-lightning-bolt", show_in_sidebar: true, require_admin: true,
  });
  try {
    await hass.callWS({ type: "lovelace/config/save", url_path: url, config: structuredClone(dashboard) });
  } catch (error) {
    // Never delete or overwrite anything while recovering from a failed save.
    const failure = new Error("copy_save_failed");
    failure.createdPath = url;
    throw failure;
  }
  return url;
}

export function reading(states, entityId, attribute, language = "fr") {
  const state = states?.[entityId];
  const missing = !state || state.state === "unknown" || state.state === "unavailable";
  const unavailable = language.startsWith("fr") ? "Indisponible" : "Unavailable";
  if (missing) return { text: unavailable, number: null };
  const value = attribute ? state.attributes?.[attribute] : state.state;
  if (value === null || value === undefined) return { text: unavailable, number: null };
  const unit = attribute ? "" : state.attributes?.unit_of_measurement || "";
  const number = typeof value === "number" ? value :
    typeof value === "string" && value.trim() !== "" ? Number(value) : NaN;
  return { text: String(value) + (unit ? " " + unit : ""), number: Number.isFinite(number) ? number : null };
}

const BaseElement = globalThis.HTMLElement || class {};
export class EhomeEmsPanel extends BaseElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = 0;
    this._bindings = [];
    this._request = 0;
    this._holdCancels = [];
  }
  set hass(value) {
    this._hass = value;
    if (this._menu) this._menu.hass = value;
    if (this._panel && this._loadedKey !== this._key()) this._load();
    else if (this._snapshotData && this._renderedAdmin !== !!value?.user?.is_admin) this._render();
    else this._refresh();
  }
  set narrow(value) { this._narrow = value; if (this._menu) this._menu.narrow = value; }
  get narrow() { return !!this._narrow; }
  set panel(value) {
    this._panel = value;
    if (this._hass && this._loadedKey !== this._key()) this._load();
  }
  _key() { return this._panel?.config?.entry_id + ":" + this._panel?.config?.revision + ":" + (this._hass?.language || "fr"); }
  _fr() { return (this._hass?.language || "fr").startsWith("fr"); }
  _t(fr, en) { return this._fr() ? fr : en; }
  async _snapshot() {
    return this._hass.callWS({
      type: "ehome_ems/dashboard", entry_id: this._panel.config.entry_id,
      language: this._fr() ? "fr" : "en",
    });
  }
  async _load() {
    const request = ++this._request;
    const key = this._key();
    this._loadedKey = key;
    try {
      const snapshot = await this._snapshot();
      if (request !== this._request) return;
      this._snapshotData = snapshot;
      this._error = null;
      this._tab = Math.min(this._tab, snapshot.dashboard.views.length - 1);
    } catch (error) {
      if (request !== this._request) return;
      this._error = this._t("Vue momentanément indisponible. Actualisez après le chargement de l’intégration.",
                            "View temporarily unavailable. Refresh after the integration loads.");
    }
    this._render();
  }
  _node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }
  _button(text, action) {
    const button = this._node("button", text);
    button.type = "button";
    button.addEventListener("click", action);
    return button;
  }
  _render() {
    for (const cancel of this._holdCancels) cancel();
    this._holdCancels = [];
    if (this._dialog?.open) this._dialog.close();
    this._dialog = null;
    this.shadowRoot.replaceChildren();
    this._bindings = [];
    this._renderedAdmin = !!this._hass?.user?.is_admin;
    const style = this._node("style");
    style.textContent = `
      :host{display:block;height:100%;overflow:auto;background:var(--primary-background-color,#f4f6f8);color:var(--primary-text-color,#18232e);font:15px/1.5 system-ui,sans-serif}
      *{box-sizing:border-box}main{max-width:1240px;margin:auto;padding:24px}
      header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
      h1{margin:0;font-size:30px;letter-spacing:-.7px}h2{margin:0 0 16px;font-size:18px}h1,h2,.note{overflow-wrap:anywhere}
      .subtitle,.note{color:color-mix(in srgb,var(--primary-text-color,#18232e) 78%,var(--card-background-color,#fff))}.subtitle{margin:4px 0 0}
      .actions,nav{display:flex;gap:8px;flex-wrap:wrap}nav{margin:24px 0}
      button,a{font:inherit}button{min-height:44px;padding:8px 16px;border:1px solid var(--divider-color,#c7d0d8);border-radius:10px;background:var(--card-background-color,#fff);color:inherit;cursor:pointer}
      button:focus-visible,a:focus-visible{outline:3px solid var(--primary-color,#007b83);outline-offset:3px}
      button[aria-current="page"]{background:var(--primary-color,#007b83);color:var(--text-primary-color,#fff);border-color:transparent}
      button:disabled{opacity:.55;cursor:wait}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,310px),1fr));gap:16px}
      .card{background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#dce3e8);border-radius:16px;padding:20px;min-width:0}
      .stack{display:flex;flex-direction:column;gap:16px}.nested-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
      .row{display:flex;justify-content:space-between;align-items:baseline;gap:16px;padding:10px 0;border-bottom:1px solid var(--divider-color,#e2e7eb)}
      .row:last-child{border-bottom:0}.row>span{min-width:0;overflow-wrap:anywhere}.value{font-variant-numeric:tabular-nums;font-weight:650;overflow-wrap:anywhere;text-align:right}
      .metric{font-size:25px;margin:4px 0 10px}progress{width:100%;height:12px;accent-color:var(--primary-color,#007b83)}
      .note{font-size:14px;margin:8px 0;white-space:pre-line}.history button{display:block;width:100%;margin-top:8px;text-align:left}
      .status{margin:12px 0;white-space:pre-line}.warn{color:var(--error-color,#b3261e)}
      .editable{cursor:context-menu;touch-action:pan-y;user-select:none}.editable:focus-visible{outline:3px solid var(--primary-color,#007b83)}
      dialog{max-width:min(600px,calc(100vw - 32px));width:100%;max-height:85vh;overflow:auto;border:1px solid var(--divider-color,#ccc);border-radius:16px;padding:24px;background:var(--card-background-color,#fff);color:inherit}
      dialog::backdrop{background:#0008}dialog input,dialog select{display:block;width:100%;font:inherit;padding:12px;margin:12px 0;background:var(--card-background-color,#fff);color:inherit;border:1px solid var(--divider-color,#aaa);border-radius:8px}
      dialog .actions{justify-content:flex-end}
      a{color:var(--primary-color,#007b83);overflow-wrap:anywhere}
      @media(max-width:600px){main{padding:16px}h1{font-size:25px}.actions{width:100%}.actions button{flex:1}nav{gap:6px}nav button{flex:1 0 auto}.nested-grid{grid-template-columns:1fr}}
    `;
    this.shadowRoot.append(style);
    const main = this._node("main");
    const header = this._node("header");
    const title = this._node("div");
    title.append(this._node("h1", "eHome EMS"),
      this._node("p", this._t("Votre énergie · observation", "Your energy · observation"), "subtitle"));
    const actions = this._node("div", undefined, "actions");
    const menu = document.createElement("ha-menu-button");
    this._menu = menu;
    menu.hass = this._hass;
    menu.narrow = this.narrow;
    menu.setAttribute("aria-label", "Menu");
    header.append(menu);
    actions.append(this._button(this._t("Actualiser", "Refresh"), () => this._load()));
    if (this._hass?.user?.is_admin && this._snapshotData) {
      this._copyButton = this._button(this._t("Créer une copie modifiable", "Create editable copy"), () => this._copy());
      this._copyButton.disabled = !!this._copying;
      actions.append(this._copyButton);
    }
    header.append(title, actions); main.append(header);
    main.append(this._node("p", this._t(
      "Cette vue suit les réglages de l’intégration. Une copie modifiable reste indépendante des mises à jour.",
      "This view follows integration settings. An editable copy stays independent of updates."), "note"));
    if (this._hass?.user?.is_admin) main.append(this._node("p", this._t(
      "Appui prolongé sur une mesure pour changer sa source, ou Entrée au clavier.",
      "Hold a reading to change its source, or press Enter on the keyboard."), "note"));
    if (this._error) main.append(this._node("p", this._error, "status warn"));
    this._message = this._node("div", undefined, "status");
    this._message.setAttribute("role", "status"); main.append(this._message);
    const snapshot = this._snapshotData;
    if (snapshot) {
      if (snapshot.missing_entities?.length) main.append(this._node("p", this._t(
        "Certaines mesures sont manquantes ou désactivées. Vérifiez les associations dans l’intégration.",
        "Some readings are missing or disabled. Check integration mappings."), "note warn"));
      const nav = this._node("nav"); nav.setAttribute("aria-label", this._t("Vues énergie", "Energy views"));
      snapshot.dashboard.views.forEach((view, index) => {
        const button = this._button(view.title, () => { this._tab = index; this._render(); });
        if (index === this._tab) button.setAttribute("aria-current", "page");
        nav.append(button);
      });
      main.append(nav);
      const content = this._node("section", undefined, "cards");
      for (const card of snapshot.dashboard.views[this._tab]?.cards || []) content.append(this._card(card));
      main.append(content);
    }
    this.shadowRoot.append(main); this._refresh();
  }
  _bind(element, entity, attribute, gauge) {
    this._bindings.push({ element, entity, attribute, gauge });
  }
  _card(config) {
    const card = this._node("div", undefined, config.type === "vertical-stack" ? "stack" :
      config.type === "grid" ? "nested-grid" : "card");
    if (config.title) card.append(this._node("h2", config.title));
    if (config.type === "markdown") card.append(this._node("p", config.content, "note"));
    if (config.cards) config.cards.forEach(item => card.append(this._card(item)));
    if (config.type === "entities") for (const item of config.entities) {
      const row = this._node("div", undefined, "row");
      const value = this._node("span", undefined, "value");
      this._bind(value, item.entity, item.attribute);
      this._editable(row, item.entity);
      row.append(this._node("span", item.name), value); card.append(row);
    }
    if (config.type === "gauge") {
      this._editable(card, config.entity);
      const value = this._node("div", undefined, "metric value");
      const progress = this._node("progress");
      progress.max = config.max - config.min;
      progress.setAttribute("aria-label", config.name);
      this._bind(value, config.entity);
      this._bind(progress, config.entity, undefined, config);
      card.append(this._node("div", config.name, "note"), value, progress);
    }
    if (config.type === "history-graph") {
      card.classList.add("history");
      card.append(this._node("p", this._t("Ouvrir l’historique d’une mesure :", "Open a reading's history:"), "note"));
      for (const entityId of config.entities) {
        const name = this._hass?.states?.[entityId]?.attributes?.friendly_name || entityId;
        card.append(this._button(name, () => this.dispatchEvent(new CustomEvent("hass-more-info", {
          detail: { entityId }, bubbles: true, composed: true,
        }))));
      }
    }
    return card;
  }
  _refresh() {
    for (const binding of this._bindings) {
      const value = reading(this._hass?.states, binding.entity, binding.attribute, this._hass?.language || "fr");
      if (binding.gauge) {
        binding.element.hidden = value.number === null;
        if (value.number !== null) binding.element.value = Math.max(0,
          Math.min(binding.gauge.max - binding.gauge.min, value.number - binding.gauge.min));
      } else binding.element.textContent = value.text;
    }
  }
  _editable(element, entity) {
    if (!this._hass?.user?.is_admin || !this._snapshotData?.bindings?.[entity]) return;
    element.classList.add("editable"); element.tabIndex = 0;
    element.setAttribute("role", "button");
    element.setAttribute("aria-label", this._t("Modifier la source de ", "Change source of ") +
      (this._hass.states?.[entity]?.attributes?.friendly_name || entity));
    let timer, x, y;
    const cancel = () => clearTimeout(timer);
    this._holdCancels.push(cancel);
    element.addEventListener("pointerdown", event => {
      if (event.button !== 0) return;
      x = event.clientX; y = event.clientY;
      timer = setTimeout(() => this._edit(entity), 600);
    });
    element.addEventListener("pointermove", event => {
      if (Math.abs(event.clientX - x) + Math.abs(event.clientY - y) > 10) cancel();
    });
    for (const type of ["pointerup", "pointercancel", "pointerleave"]) element.addEventListener(type, cancel);
    element.addEventListener("contextmenu", event => { event.preventDefault(); cancel(); this._edit(entity); });
    element.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); this._edit(entity); }
    });
  }
  _edit(entity) {
    if (!this._hass?.user?.is_admin || this._dialog?.open) return;
    const binding = this._snapshotData?.bindings?.[entity];
    if (!binding) return;
    const revision = this._snapshotData.revision;
    const dialog = this._node("dialog");
    this._dialog = dialog;
    const title = this._node("h2", this._t("Changer la source", "Change source"));
    dialog.setAttribute("aria-labelledby", "source-title"); title.id = "source-title";
    dialog.append(title, this._node("p", this._hass.states?.[entity]?.attributes?.friendly_name || entity));
    if (binding.calculated_home) dialog.append(this._node("p", this._t(
      "Maison est calculée par EMS. Enregistrer une source ci-dessous remplacera ce calcul par un capteur existant.",
      "Home is calculated by EMS. Saving a source below switches it to an existing sensor."), "note warn"));
    dialog.append(this._node("p", this._t(
      "Vous modifiez l’association dans EMS, pas le capteur d’origine. Aucun équipement n’est commandé.",
      "This changes the EMS mapping, not the original sensor. No device is commanded."), "note"));
    const search = this._node("input");
    search.type = "search"; search.placeholder = this._t("Rechercher un capteur", "Search source");
    search.setAttribute("aria-label", search.placeholder);
    const select = this._node("select"); select.size = 6;
    select.setAttribute("aria-label", this._t("Nouvelle source", "New source"));
    const states = this._hass.states || {};
    const candidates = Object.entries(states).filter(([id, state]) =>
      binding.domains.includes(id.split(".")[0]) &&
      (!binding.units.length || binding.units.includes(state.attributes?.unit_of_measurement)) &&
      !this._snapshotData.bindings[id]);
    const fill = () => {
      const previous = select.value || binding.source;
      select.replaceChildren();
      for (const [id, state] of candidates.sort(([a], [b]) => a.localeCompare(b))) {
        const label = (state.attributes?.friendly_name || id) + " · " + id + " · " +
          state.state + " " + (state.attributes?.unit_of_measurement || "");
        if (!label.toLocaleLowerCase().includes(search.value.toLocaleLowerCase())) continue;
        const option = this._node("option", label); option.value = id;
        if (id === previous) option.selected = true;
        select.append(option);
      }
    };
    search.addEventListener("input", fill); fill();
    const message = this._node("p", "", "warn"); message.setAttribute("role", "status");
    const actions = this._node("div", undefined, "actions");
    const cancel = this._button(this._t("Annuler", "Cancel"), () => dialog.close());
    const save = this._button(this._t("Enregistrer la source", "Save source"), async () => {
      if (!select.value || save.disabled) return;
      save.disabled = true;
      try {
        await this._hass.callWS({ type: "ehome_ems/remap_source", entry_id: this._panel.config.entry_id,
          entity_id: entity, source_id: select.value, expected_source: binding.source, revision });
        dialog.close(); await this._load();
      } catch (error) {
        message.textContent = error.code === "conflict" ? this._t(
          "La configuration a changé. Annulez et actualisez avant de réessayer.",
          "Configuration changed. Cancel and refresh before retrying.") : this._t(
          "Association refusée : vérifiez l’unité, les doublons et le rôle du capteur. Les réglages précédents sont conservés.",
          "Mapping rejected: check units, duplicates and source role. Previous settings are preserved.");
      } finally { save.disabled = false; }
    });
    actions.append(cancel, save); dialog.append(search, select, message, actions);
    dialog.addEventListener("close", () => { dialog.remove(); this._dialog = null; });
    this.shadowRoot.append(dialog); dialog.showModal(); search.focus();
  }
  async _copy() {
    if (this._copying || !this._hass?.user?.is_admin) return;
    this._copying = true; this._copyButton.disabled = true;
    this._message.textContent = this._t("Création de la copie…", "Creating copy…");
    try {
      const snapshot = await this._snapshot();
      if (snapshot.missing_entities?.length) throw new Error("missing_entities");
      const path = await createIndependentCopy(this._hass, snapshot.dashboard);
      this._message.replaceChildren(this._node("span", this._t("Copie créée. ", "Copy created. ")));
      const link = this._node("a", this._t("Ouvrir la copie", "Open copy"));
      link.href = "/" + path; this._message.append(link);
    } catch (error) {
      this._message.textContent = error.createdPath ?
        this._t("Une copie vide a été créée, mais son contenu n’a pas été enregistré. Votre vue automatique reste disponible.",
                "An empty copy was created, but its content was not saved. Your automatic view remains available.") :
        this._t("Copie impossible pour le moment. Vérifiez les mesures et réessayez. Aucun dashboard existant n’a été remplacé.",
                "Copy unavailable for now. Check readings and retry. No existing dashboard was replaced.");
      if (error.createdPath) {
        const link = this._node("a", this._t(" Ouvrir la copie vide", " Open empty copy"));
        link.href = "/" + error.createdPath; this._message.append(link);
      }
    } finally {
      this._copying = false; this._copyButton.disabled = false;
    }
  }
}
if (globalThis.customElements && !customElements.get("ehome-ems-panel")) {
  customElements.define("ehome-ems-panel", EhomeEmsPanel);
}
