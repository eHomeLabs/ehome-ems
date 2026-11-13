export function rankEntityOptions(options,deviceName="") {
  const normal=value=>String(value||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
  const name=normal(deviceName),tokens=name.split(" ").filter(t=>t.length>2&&!['les','des','une','pour','the'].includes(t));
  const score=([id,label])=>{const text=normal(id+" "+label);return (name&&text.includes(name)?50:0)+tokens.reduce((total,t)=>total+(text.split(" ").includes(t)?10:0),0);};
  return [...options].sort((a,b)=>score(b)-score(a)||String(a[1]).localeCompare(String(b[1]),"fr",{numeric:true,sensitivity:"base"})||a[0].localeCompare(b[0]));
}
export function pvProductionSources(items, resolve=id=>id) {
  const seen=new Set();return (items||[]).flatMap(item=>{
    const entity=item.dc_power || (item.kind!=="hybrid_inverter"?item.power:null);
    const source=resolve(entity);if(!source||seen.has(source))return [];
    seen.add(source);return [{...item,production:entity}];
  });
}
export function strictSum(values) {return values.length&&values.every(v=>typeof v==="number"&&Number.isFinite(v)&&v>=0)?values.reduce((a,b)=>a+b,0):null;}
export function situationFacts({solar,home,imported,exported,charge,discharge,water}) {
  const valid=n=>typeof n==="number"&&Number.isFinite(n)&&n>=0,active=n=>valid(n)&&n>=10;
  const facts=[];
  if(!valid(solar)||!valid(home)||!valid(imported)||!valid(exported))facts.push("incomplete");
  else if(active(imported))facts.push("import");
  else if(solar>home+10)facts.push("surplus");
  else if(active(solar))facts.push("solar");else facts.push("no_solar");
  if(active(water))facts.push("water");
  if(active(charge))facts.push("charge");
  if(active(discharge))facts.push("discharge");
  if(active(exported))facts.push("export");
  return facts;
}
export const PRODUCT_ICONS = ["auto","mdi:power-plug","mdi:washing-machine","mdi:dishwasher","mdi:tumble-dryer","mdi:fridge","mdi:radiator","mdi:air-conditioner","mdi:pool","mdi:coffee-maker","mdi:printer-3d-nozzle","mdi:lightbulb","mdi:television","mdi:desktop-classic","mdi:water-boiler","mdi:ev-station"];
export function dailyGoalPercent(energy,goal) {
  return typeof energy==="number"&&Number.isFinite(energy)&&energy>=0&&typeof goal==="number"&&Number.isFinite(goal)&&goal>0?energy/goal*100:null;
}
export function productIcon(config={}) {
  if(PRODUCT_ICONS.includes(config.icon)&&config.icon!=="auto")return config.icon;
  if(["solar_router","water_heater"].includes(config.kind))return "mdi:water-boiler";
  if(config.kind==="ev_charger")return "mdi:ev-station";
  const name=(config.name||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
  for(const [pattern,icon] of [[/vaisselle|dishwash/,"dishwasher"],[/seche.*linge|dryer/,"tumble-dryer"],[/lave.*linge|washing/,"washing-machine"],[/frigo|congel|refriger|fridge|freezer/,"fridge"],[/serviette|radiateur|radiator/,"radiator"],[/clim|chaleur|heat.pump/,"air-conditioner"],[/piscine|pool|filtration/,"pool"],[/expresso|cafe|coffee/,"coffee-maker"],[/imprimante|printer/,"printer-3d-nozzle"],[/eclairage|lampe|light/,"lightbulb"],[/television|\btv\b/,"television"],[/ordinateur|informatique|computer/,"desktop-classic"]])if(pattern.test(name))return "mdi:"+icon;
  return "mdi:power-plug";
}
// Managed view uses authenticated HA state; editable copies use public WS APIs.
export const UI_VERSION = "0.2.17";
export const PANEL_TAG = `ehome-ems-panel-${UI_VERSION.replaceAll(".", "-")}`;
export const FLOW_MIN_WATTS = 10;
export function flowActive(states, entity) {
  const power = flowPower(states, entity);
  return power !== null && power >= FLOW_MIN_WATTS;
}
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
  if(unit && ["W","kW","Wh","kWh","%","°C","°F"].includes(unit) && !Number.isFinite(number))return {text:unavailable,number:null};
  return { text: (Number.isFinite(number) ? (unit==="%"?percent(number,language):displayNumber(number, language)) : String(value)) + (unit ? " " + unit : ""), number: Number.isFinite(number) ? number : null };
}

export function displayNumber(value, language="fr") {
  return new Intl.NumberFormat(language, {maximumFractionDigits:2,useGrouping:false}).format(Math.abs(value)<.005?0:value);
}
export function localDayStart(now=new Date(), timeZone="UTC") {
  const parts=date=>Object.fromEntries(new Intl.DateTimeFormat("en-GB",{timeZone,year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"}).formatToParts(date).filter(p=>p.type!=="literal").map(p=>[p.type,Number(p.value)]));
  const p=parts(now),target=Date.UTC(p.year,p.month-1,p.day);let guess=target;
  for(let i=0;i<4;i++){const q=parts(new Date(guess));guess+=target-Date.UTC(q.year,q.month-1,q.day,q.hour,q.minute,q.second);}
  return guess;
}
export function quarterTrends(records, now=Date.now()) {
  const step=900000,end=Math.floor(now/step)*step,start=end-24*step,bins=Array.from({length:24},()=>[]);
  for(const r of records||[]){const t=Date.parse(r.last_changed||r.last_updated),raw=r.state,v=raw===null||raw===undefined||String(raw).trim()===""?NaN:Number(raw),index=Math.floor((t-start)/step);if(index>=0&&index<24&&Number.isFinite(v))bins[index].push(v);}
  const means=bins.map(b=>b.length?b.reduce((a,v)=>a+v,0)/b.length:null);
  return means.map((v,i)=>({time:start+i*step,value:v,direction:v===null||i===0||means[i-1]===null?null:Math.abs(v-means[i-1])<.005?0:v>means[i-1]?1:-1}));
}
export function dailyFromCounter(records, current, unit, start, now=Date.now()) {
  const factor=u=>({wh:.001,kwh:1}[String(u||"").trim().toLowerCase()]);
  if(!Number.isFinite(current)||current<0||!factor(unit))return null;
  const points=(records||[]).map(r=>({time:Date.parse(r.last_changed||r.last_updated),value:r.state===null||r.state===undefined||String(r.state).trim()===""?NaN:Number(r.state)*factor(r.attributes?.unit_of_measurement||unit)})).filter(p=>Number.isFinite(p.time)&&Number.isFinite(p.value)&&p.value>=0&&p.time<=now).sort((a,b)=>a.time-b.time);
  const baseline=points.filter(p=>p.time<=start).at(-1);if(!baseline)return null;
  let previous=baseline.value,total=0;
  for(const p of [...points.filter(p=>p.time>start),{time:now,value:current*factor(unit)}]){const delta=p.value-previous;total+=delta>=-0.000001?Math.max(0,delta):p.value;previous=p.value;}
  return Math.round(total*1000000)/1000000;
}
export function percent(value,language="fr") {return new Intl.NumberFormat(language,{maximumFractionDigits:0,useGrouping:false}).format(value);}

export function houseMode(now=new Date(), timeZone="UTC") {
  const hour=Number(new Intl.DateTimeFormat("en-GB",{hour:"2-digit",hourCycle:"h23",timeZone}).format(now));
  return hour>=7 && hour<19 ? "day" : "night";
}
export function dailyIndicators({home,solar,imported,exported}) {
  const valid=n=>typeof n==="number"&&Number.isFinite(n)&&n>=0;
  return {
    autonomy:valid(home)&&home>0&&valid(imported)&&imported<=home?100*(1-imported/home):null,
    selfConsumption:valid(solar)&&solar>0&&valid(exported)&&exported<=solar?100*(1-exported/solar):null,
    importShare:valid(imported)&&valid(exported)&&imported+exported>0?100*imported/(imported+exported):null,
    exportShare:valid(imported)&&valid(exported)&&imported+exported>0?100*exported/(imported+exported):null,
  };
}
export function curveSegments(records) {
  return historySegments(records).map(segment=>{
    const buckets=new Map();
    for(const p of segment){const key=Math.floor(p.time/300000);const b=buckets.get(key)||{time:0,value:0,count:0};b.time+=p.time;b.value+=p.value;b.count++;buckets.set(key,b);}
    return [...buckets.values()].map(b=>({time:b.time/b.count,value:b.value/b.count}));
  });
}

export function historySegments(records) {
  const segments=[];let current=[];let lastTime;
  for(const record of records) {
    const time=Date.parse(record.last_changed || record.last_updated),raw=record.state;
    const value=raw===null||raw===undefined||String(raw).trim()===""?NaN:Number(raw);
    if(!Number.isFinite(time)||!Number.isFinite(value)) {if(current.length)segments.push(current);current=[];lastTime=undefined;continue;}
    if(lastTime!==undefined && (time<lastTime||time-lastTime>1800000)) {if(current.length)segments.push(current);current=[];}
    current.push({time,value});lastTime=time;
  }
  if(current.length)segments.push(current);return segments;
}

const BaseElement = globalThis.HTMLElement || class {};
export function flowPower(states, entity) {
  const value = reading(states, entity);
  const unit = states?.[entity]?.attributes?.unit_of_measurement;
  return value.number === null || !["W", "kW"].includes(unit) || value.number < 0 ? null :
    value.number * (unit === "kW" ? 1000 : 1);
}

export class EhomeEmsPanel extends BaseElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = 0;
    this._bindings = [];
    this._flowUpdates = [];
    this._request = 0;
    this._layoutObservers = [];
    this._holdCancels = [];
    this._history = {};
    this._historyAt = 0;
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
  disconnectedCallback() {
    clearInterval(this._clock); clearTimeout(this._settleRefresh);
    this._weatherGeneration=(this._weatherGeneration||0)+1;this._weatherUnsubscribe?.();this._weatherUnsubscribe=null;this._weatherKey=null;
    for (const observer of this._layoutObservers || []) observer.disconnect();
    for (const cancel of this._holdCancels || []) cancel();
  }
  connectedCallback() { clearInterval(this._clock); this._clock=setInterval(()=>this._refresh(),30000); if (this._snapshotData) this._render(); }
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
    const tabKey="ehome-ems-tab:"+(this._hass?.user?.id||"user")+":"+this._panel.config.entry_id;
    if(this._tabStorageKey!==tabKey){this._tabStorageKey=tabKey;try{const value=sessionStorage.getItem(tabKey);this._tab=value!==null&&/^\d+$/.test(value)?Math.max(0,Math.min(9,Number(value))):0;}catch{}}
    this._loadedKey = key;
    try {
      const snapshot = await this._snapshot();
      if (request !== this._request) return;
      if (JSON.stringify(snapshot.bindings) !== JSON.stringify(this._snapshotData?.bindings)) { this._historyAt = 0; this._history = {}; }
      this._snapshotData = snapshot;
      this._error = null;
      this._tab = Math.min(this._tab, 9);
      this._loadHistory();
    } catch (error) {
      if (request !== this._request) return;
      this._error = this._t("Vue momentanément indisponible. Actualisez après le chargement de l’intégration.",
                            "View temporarily unavailable. Refresh after the integration loads.");
    }
    if(!this._dialog?.open)this._render();
    if(this._snapshotData?.missing_entities?.length && this._settingsRetries>0 && !this._dialog?.open){
      clearTimeout(this._settleRefresh);this._settleRefresh=setTimeout(()=>{this._settingsRetries--;if(!this._dialog?.open)this._load();},500);
    }else if(!this._snapshotData?.missing_entities?.length)this._settingsRetries=0;
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
    if(this._tabStorageKey)try{sessionStorage.setItem(this._tabStorageKey,String(this._tab));}catch{}
    for (const observer of this._layoutObservers || []) observer.disconnect();
    this._layoutObservers = [];
    for (const cancel of this._holdCancels) cancel();
    this._holdCancels = [];
    if (this._dialog?.open) this._dialog.close();
    this._dialog = null;
    this.shadowRoot.replaceChildren();
    this._bindings = [];
    this._flowUpdates = [];
    this._renderedAdmin = !!this._hass?.user?.is_admin;
    const style = this._node("style");
    style.textContent = `
      :host{display:block;height:100%;overflow:auto;background:var(--primary-background-color,#f4f6f8);color:var(--primary-text-color,#18232e);font:15px/1.5 system-ui,sans-serif}
      .integration-meta{font-size:12px;margin:6px 0 0}.equipment-name{cursor:context-menu;text-decoration:underline dotted;text-underline-offset:4px;touch-action:pan-y}.equipment-name:focus-visible{outline:3px solid var(--primary-color,#007b83);outline-offset:3px}.battery-direction .flow-small{color:inherit}
      .pv-meta{font-size:15px;color:var(--secondary-text-color,#91a4b8)}.flow-day-energy{display:block;font-size:12px;line-height:1.45;margin-top:3px;overflow-wrap:anywhere;letter-spacing:0}.flow-house .flow-day-energy{font-size:13px;margin-left:20%;max-width:80%}
      .heater-layout{display:grid;grid-template-columns:minmax(100px,35%) minmax(0,1fr);gap:20px;align-items:center;margin:18px 0 24px}.heater-details{min-width:0}.heater-details .vessel-main{color:#ffa000;font-size:32px}.cumulus-visual{position:relative;width:min(100%,140px);height:205px;margin:10px auto 18px;border:3px solid #e9a23d;border-radius:45% / 12%;background:#173144;overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:inset 12px 0 20px #0004}.cumulus-visual:after{content:"";position:absolute;top:7%;left:10%;right:10%;height:2px;background:#e9a23d99}.cumulus-visual ha-icon{position:relative;z-index:1;--mdc-icon-size:70px;color:#ffb74d}.cumulus-fill{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(#ffa00088,#fb6c20cc);transition:height .3s}.heater-details .energy-value{font-size:24px}@media(max-width:450px){.heater-layout{grid-template-columns:90px minmax(0,1fr);gap:12px}.cumulus-visual{height:170px}.heater-details .vessel-main{font-size:26px}.heater-details .energy-value{font-size:21px}}
      .alert-rule{border:1px solid var(--divider-color,#738391);border-radius:10px;padding:10px 12px}.alert-rule summary{cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;min-height:24px}.alert-rule fieldset{margin-top:12px}
      .overview-daily-energy{font-size:16px;font-weight:650;line-height:1.5;margin:10px 0 0;min-height:48px;overflow-wrap:anywhere}.load-grid .cost{min-height:42px;margin:6px 0 0}
      .entity-picker{width:100%}.entity-options{max-height:260px;overflow:auto;border:1px solid var(--divider-color,#738391);border-radius:10px;padding:8px}.entity-options button{display:block;width:100%;text-align:left;white-space:normal;overflow-wrap:anywhere;margin:6px 0}
      .history-value{cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:5px}.history-value:focus-visible{outline:3px solid var(--primary-color,#007b83)}
      .settings-primary{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;width:100%;margin-bottom:20px}.settings-primary button{border:2px solid var(--primary-color,#007b83);font-weight:700;padding:18px;text-align:left;background:color-mix(in srgb,var(--primary-color,#007b83) 12%,var(--card-background-color,#fff))}
      .situation-comment{font-size:17px;line-height:1.8;border-left:4px solid #42bfa0;padding:12px 16px}.reading-history{width:min(900px,95vw);max-height:90vh;overflow:auto}.history-series svg{width:100%;height:200px;background:color-mix(in srgb,var(--primary-color,#007b83) 5%,transparent)}
      .alert-form{display:grid;gap:16px}.alert-form fieldset{border:1px solid var(--divider-color,#738391);border-radius:12px;display:grid;gap:12px;min-width:0}.alert-form label{display:grid;gap:6px}.alert-form input:not([type=checkbox]),.alert-form select{max-width:100%;width:100%;padding:12px;border-radius:8px;background:var(--card-background-color,#fff);color:inherit;border:1px solid var(--divider-color,#738391);font:inherit}.alert-form input[type=checkbox]{width:24px;height:24px}
      *{box-sizing:border-box}main{max-width:1700px;margin:auto;padding:24px}
      header{display:flex;align-items:center;justify-content:flex-start;gap:16px;flex-wrap:wrap}
      h1{margin:0;font-size:30px;letter-spacing:-.7px}h2{margin:0 0 16px;font-size:18px}h1,h2,.note{overflow-wrap:anywhere}
      .subtitle,.note{color:color-mix(in srgb,var(--primary-text-color,#18232e) 78%,var(--card-background-color,#fff))}.subtitle{margin:4px 0 0}
      .actions,nav{display:flex;gap:8px;flex-wrap:wrap}.actions{margin-left:auto}nav{margin:24px 0}
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
      dialog::backdrop{background:#0008}dialog input:not([type=checkbox]),dialog select{display:block;width:100%;font:inherit;padding:12px;margin:12px 0;background:var(--card-background-color,#fff);color:inherit;border:1px solid var(--divider-color,#aaa);border-radius:8px}
      dialog .actions{justify-content:flex-end;position:sticky;bottom:-24px;background:var(--card-background-color,#15222d);padding:12px 0}.settings-form{display:grid;gap:8px}.settings-form label{display:block;font-size:14px}.settings-form label:has(input[type=checkbox]){display:flex;align-items:center;gap:10px;padding:12px 0}.settings-form input[type=checkbox]{width:22px;height:22px}.equipment-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}.settings-shortcuts{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}.ratios{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:24px 0}.ratios .kpi-label{padding-right:0}.ratio-value{font-size:36px;font-weight:750;color:#51d593}.exchange-bar{height:12px;display:flex;border-radius:8px;overflow:hidden;background:#526579;margin:10px 0}.exchange-bar>span:first-child{background:#ff6565}.exchange-bar>span:last-child{background:#58aeff}.charger-icon{color:#bb86fc}.charger-icon ha-icon{--mdc-icon-size:190px;width:190px;height:190px}.charger-card .vessel-main{color:#bb86fc}.charger-card .vessel-layout{grid-template-columns:40% 1fr}.charger-card .vessel-main{font-size:clamp(28px,3vw,45px)}
      a{color:var(--primary-color,#007b83);overflow-wrap:anywhere}
      .top-nav{position:sticky;top:0;z-index:2;padding:12px 0;background:var(--primary-background-color,#f4f6f8);flex-wrap:nowrap;overflow-x:auto;scrollbar-width:thin}.top-nav button{white-space:nowrap;flex:none}
      .kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin:16px 0}
      .kpi{border:1px solid var(--divider-color,#3b536b);border-radius:14px;padding:16px;background:var(--card-background-color,#14212d);min-width:0}
      .kpi ha-icon{display:inline-block;margin-right:8px;--mdc-icon-size:28px}.kpi .value{display:block;text-align:left;font-size:clamp(21px,2.4vw,32px);margin:6px 0;line-height:1.2}.kpi-label{display:block;font-size:14px;color:var(--primary-text-color,#e9f1fc)}
      .overview-grid{display:grid;grid-template-columns:minmax(0,2.5fr) minmax(280px,1fr);gap:16px;align-items:start}.overview-grid>.flow{margin:0;grid-column:1;grid-row:1}.overview-grid>.strategy{grid-column:2;grid-row:1}.overview-grid>.secondary{grid-column:1;grid-row:2}.overview-grid>.quality-panel{grid-column:2;grid-row:2}
      .observation{display:inline-block;border:1px solid var(--primary-color,#70a246);border-radius:20px;padding:3px 10px;font-size:13px;margin-bottom:12px}.strategy .row{align-items:center}.strategy .row .value{white-space:nowrap}.strategy .row>span:first-child{font-size:14px}.strategy button{margin-top:12px}
      .load-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:12px}.load-grid .kpi{padding:12px}.load-grid .value{font-size:24px}
      .home-diagnostic{margin:16px 0}.home-diagnostic summary{cursor:pointer;font-weight:650;min-height:32px}.home-diagnostic .source-item{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.home-diagnostic .source-item span{overflow-wrap:anywhere}.source-list{display:grid;gap:12px}.source-item{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;border-bottom:1px solid var(--divider-color,#3b536b);padding:12px 0}.source-item code{display:block;overflow-wrap:anywhere;font-size:12px}.config-links{display:flex;gap:16px;flex-wrap:wrap;margin:16px 0}
      .simulation-editor{display:grid;gap:12px;margin:16px 0}.simulation-row{display:grid;grid-template-columns:minmax(180px,2fr) repeat(2,minmax(100px,1fr)) auto;align-items:end;gap:12px;border-bottom:1px solid var(--divider-color,#3b536b);padding:12px 0}
      .simulation-row label,.scenario-budget{display:block;font-size:14px}.simulation-row input[type=number],.scenario-budget input{display:block;max-width:100%;width:100%;font:inherit;padding:10px;background:var(--card-background-color,#15222d);color:inherit;border:1px solid var(--divider-color,#3b536b);border-radius:8px}.scenario-budget{max-width:360px;margin:16px 0}.scenario-result{margin:16px 0;padding:16px;border:1px solid var(--divider-color,#3b536b);border-radius:12px}.scenario-result .row{flex-wrap:wrap}.scenario-history details{margin:12px 0}.scenario-history summary{cursor:pointer;padding:10px 0}.simulation-row .move-buttons{display:flex;gap:6px}
      @media(max-width:700px){.simulation-row{grid-template-columns:1fr 1fr}.simulation-target,.simulation-row .move-buttons{grid-column:1/-1}}
      @media(min-width:1051px){.overview-grid .flow-stage{aspect-ratio:1000/600}.overview-grid .flow-house{left:29%;top:26%;width:54%}.overview-grid .flow-solar,.overview-grid .flow-grid{width:36%}.overview-grid .flow-battery{top:50%}}
      @media(max-width:1050px){.kpis{grid-template-columns:repeat(3,minmax(0,1fr))}.overview-grid{grid-template-columns:1fr}.overview-grid>.strategy{grid-column:1;grid-row:3}.overview-grid>.secondary{grid-row:2}.overview-grid>.quality-panel{grid-column:1;grid-row:4}}
      @media(max-width:600px){.home-diagnostic .source-item{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.kpi{padding:12px}.top-nav{margin:12px 0}.top-nav button{flex:none}.source-item{grid-template-columns:1fr}.source-item button{justify-self:start}}
      .flow{background:#101923;color:#e9f1fc;border:1px solid #30475c;border-radius:20px;padding:clamp(12px,3vw,28px);margin:20px 0;overflow:hidden}
      .flow h2{font-size:22px;margin:0}.flow .flow-note{color:#aabbd0;font-size:13px;margin:6px 0 14px}
      .flow-stage{position:relative;aspect-ratio:1000/830;max-width:900px;margin:auto}
      .flow-scene-wrap{position:relative}.flow-scene-wrap .flow-stage{width:100%}
      .flow-tile{position:absolute;border:1px solid #3b536b;border-radius:14px;background:#14212d;padding:clamp(8px,2vw,20px);min-width:0;overflow-wrap:anywhere}
      .flow-tile ha-icon{--mdc-icon-size:clamp(22px,4vw,42px);display:inline-block;margin-right:8px}
      .flow-title{font-size:clamp(12px,2.3vw,20px);font-weight:500}.flow-number{display:block;font-size:clamp(18px,4vw,34px);font-weight:700;font-variant-numeric:tabular-nums;line-height:1.3}
      .flow-small{display:block;font-size:clamp(11px,1.7vw,15px);color:#b4c4d7;line-height:1.4}
      .flow-solar{left:0;top:0;width:46%;color:#ffce45}.flow-grid{right:0;top:0;width:46%;color:#52d7ee}
      .flow-house{position:absolute;left:24%;top:29%;width:64%;text-align:center;color:#edf4ff}
      .flow-house img{display:block;width:100%;height:auto;object-fit:contain}.flow-house .flow-number{font-size:clamp(24px,5vw,46px)}
      .flow-battery{left:0;top:58%;width:31%;color:#50e49b}.flow-battery progress{accent-color:#50e49b;margin:8px 0}
      .flow-links{position:absolute;inset:0;width:100%;height:100%;overflow:visible;pointer-events:none}
      .flow-links path,.flow-branches path{fill:none;stroke:currentColor;stroke-width:3;opacity:.18;vector-effect:non-scaling-stroke}
      .flow-links path.active,.flow-branches path.active{opacity:1;stroke-dasharray:10 16;animation:flow-dash 1.5s linear infinite;filter:drop-shadow(0 0 3px currentColor)}
      .flow-links path.reverse{animation-direction:reverse}.flow-links path.unknown{stroke-dasharray:2 7;opacity:.4}
      .flow-usage-title{text-align:center;font-size:15px;margin:8px 0 16px;color:#b8c9dc}
      .flow-branches{display:block;width:100%;height:34px;color:#edf4ff;margin-bottom:8px}
      .flow-usages{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,140px),1fr));gap:12px}
      .flow-usage{position:relative;border:1px solid #3b536b;border-radius:14px;padding:16px;text-align:center;min-width:0;background:#14212d}
      .flow-usage ha-icon{display:block;margin:0 auto 8px;--mdc-icon-size:34px}.flow-usage .flow-title{font-size:15px}.flow-usage .flow-number{font-size:24px}
      .flow-extra{display:flex;gap:12px;flex-wrap:wrap;margin-top:14px}.flow-extra .flow-usage{flex:1;min-width:150px}
      @keyframes flow-dash{to{stroke-dashoffset:-52}}
      @media(prefers-reduced-motion:reduce){.flow-links path.active,.flow-branches path.active{animation:none;stroke-dasharray:none}}
      @media(max-width:600px){.flow-stage{aspect-ratio:auto;height:350px}.flow-tile{border-radius:10px}.flow-battery{width:34%;top:57%}.flow-house{left:24%;top:32%;width:64%}.flow-grid .flow-number{font-size:18px}.flow-usages{grid-template-columns:repeat(2,minmax(0,1fr))}.flow-usage{padding:12px}}
      @media(max-width:600px){main{padding:16px}h1{font-size:25px}.actions{width:100%}.actions button{flex:1}nav{gap:6px}nav button{flex:1 0 auto}.nested-grid{grid-template-columns:1fr}}

      :host{--ems-panel:#0a1724;--ems-line:#29465e;--ems-blue:#58baff}
      .kpi{position:relative;overflow:hidden;padding:18px 18px 12px;border-radius:18px;min-height:142px;border-color:color-mix(in srgb,var(--tone,#5bb8ff) 35%,var(--divider-color,#29465e));background:var(--card-background-color,#101e2a)}
      .kpi ha-icon{float:right;color:var(--tone);--mdc-icon-size:30px;margin:0 0 8px 8px}.kpi .value{font-size:clamp(25px,2.6vw,36px);letter-spacing:-.6px;font-weight:750;color:var(--tone);margin:12px 0}.kpi .value{font-size:clamp(21px,2vw,30px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.kpi-label{font-weight:600}.vessel-main.missing{font-size:clamp(18px,2vw,27px);overflow-wrap:anywhere}.warning{color:#ffbf44!important}.bad{color:#ff6565!important}.good{color:#51d593!important}.value.missing,.flow-number.missing{font-size:18px!important;overflow-wrap:normal}.spark{margin:6px -18px -12px;position:relative;min-height:32px}.spark canvas{display:block;width:100%;height:54px}.spark-note{display:block;font-size:10px;color:var(--secondary-text-color,#91a4b8);padding:0 18px 6px}.energy-value{font-size:24px;font-weight:700;margin:8px 0 0}.cost{color:#65c487}.kpi .note{font-size:12px}
      .vessel-card{padding:26px}.vessel-layout{display:grid;grid-template-columns:minmax(90px,40%) 1fr;gap:20px;align-items:center}.vessel-icon{position:relative;width:100%;height:260px;display:grid;place-items:center;color:#42dca4}.vessel-icon>ha-icon,.vessel-fill>ha-icon{--mdc-icon-size:210px;display:block;width:210px;height:210px}.vessel-icon>ha-icon{color:var(--divider-color,#647382);position:absolute;left:50%;top:50%;transform:translate(-50%,-50%)}.vessel-fill{position:absolute;left:50%;top:50%;width:210px;height:210px;transform:translate(-50%,-50%);display:grid;place-items:center;clip-path:inset(calc(100% - var(--fill,0%)) 0 0 0)}.vessel-main{font-size:clamp(38px,4.5vw,64px);font-weight:750;line-height:1.1;color:var(--tone);letter-spacing:-1px}.vessel-direction{font-size:27px;font-weight:700;color:var(--tone);margin:10px 0 0}.vessel-details .note{font-size:12px;margin:4px 0}.vessel-details .cost{font-size:16px}.today .cards{margin:20px 0}.today .kpi{background:color-mix(in srgb,var(--tone) 8%,var(--card-background-color,#101e2a))}
      .flow{background:#081827;border-color:#254b65;border-radius:18px}.flow-tile,.flow-usage{background:#0a1b29;border-color:currentColor;box-shadow:0 0 16px #0003}.flow-stage{aspect-ratio:auto;height:490px;max-width:none}.flow-solar,.flow-grid{width:25%;padding:12px}.flow-tile ha-icon{--mdc-icon-size:28px}.flow-title{font-size:15px}.flow-number{font-size:25px}.flow-small{font-size:12px}.flow-house{left:25%;top:20%;width:56%}.flow-house .flow-number{font-size:36px}.flow-battery{top:48%;width:23%;padding:12px}.flow-battery .flow-number{font-size:22px}.flow-extra .flow-usage{text-align:left;flex:0 1 250px}.flow-extra .flow-number{font-size:21px}.flow-usage-title{font-size:12px;margin:4px 0}.flow-usages{max-width:620px;margin:auto}.flow-usage{padding:12px;text-align:left}.flow-usage ha-icon{float:left;margin:0 12px 0 0}.flow-links path.active,.flow-branches path.active{stroke-width:4;stroke-dasharray:15 20;filter:drop-shadow(0 0 5px currentColor)}
      @media(min-width:1051px){.overview-grid .flow-stage{aspect-ratio:auto;height:440px}.overview-grid .flow-house{left:25%;top:22%;width:58%}.overview-grid .flow-solar,.overview-grid .flow-grid{width:26%}.overview-grid .flow-battery{top:47%;width:24%}}
      @media(max-width:700px){.vessel-card{padding:20px}.vessel-icon{height:220px}.vessel-icon>ha-icon,.vessel-fill>ha-icon{--mdc-icon-size:170px;width:170px;height:170px}.vessel-fill{width:170px;height:170px}.vessel-layout{gap:12px}.vessel-main{font-size:43px}.flow-stage{height:460px}.flow-house{left:17%;top:28%;width:80%}.flow-battery{top:60%;width:36%}.flow-solar{width:43%}.flow-grid{width:43%}.flow-house .flow-title{font-size:12px}.flow-house .flow-number{font-size:27px}.flow-tile .flow-number{font-size:21px}.flow-grid .flow-number{font-size:21px}.kpi-label{font-size:12px}.kpi ha-icon{--mdc-icon-size:24px}.flow-usage .flow-title{font-size:12px}.flow-usage .flow-number{font-size:21px}}
      .kpi{display:flex;flex-direction:column;min-width:0;box-sizing:border-box}.kpi>ha-icon{position:absolute;right:16px;top:18px;margin:0}.kpi-label{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;box-sizing:border-box;min-height:42px;height:42px;line-height:21px;padding-right:40px;overflow-wrap:anywhere}.kpi>.value{display:block;min-height:38px;line-height:38px;margin:6px 0 10px}.spark{margin:0;min-height:62px;height:62px;box-sizing:border-box}.trend-head{font-size:29px;font-weight:700;line-height:30px}[hidden]{display:none!important}.router-settings form{display:grid;gap:12px;margin-top:14px}.router-settings label{display:grid;gap:6px}.router-settings input,.router-settings select{width:100%;box-sizing:border-box;padding:12px;border:1px solid #3a596e;border-radius:10px;background:var(--secondary-background-color,#102333);color:var(--primary-text-color,#edf4ff);font:inherit}.pv-card .cards{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}.history-row{display:grid;grid-template-columns:minmax(170px,1fr) minmax(0,3fr);gap:16px;align-items:center;margin:12px 0}.history-chart svg{width:100%;height:70px;display:block}@media(max-width:600px){.history-row{grid-template-columns:1fr}}.spark-note{padding:3px 0 0;font-size:10px;min-height:24px}.appliance-card .usage-energy{min-height:105px}.appliance-card .cost{min-height:42px}.equipment-status{min-height:20px}.appliance-card .equipment-actions{margin-top:auto}.usage-energy .note{overflow-wrap:anywhere}.cards{align-items:stretch}.today .cards>.kpi{min-height:210px;height:210px}.weather-card .weather-detail{min-height:40px}.weather-card .value{font-size:24px}
    `;
    this.shadowRoot.append(style);
    const main = this._node("main");
    const header = this._node("header");
    const title = this._node("div");
    title.append(this._node("h1", "eHome EMS"),
      this._node("p", this._t("Votre énergie · observation", "Your energy · observation"), "subtitle"));
    const meta=this._node("p",this._t("Interface ","Interface ")+UI_VERSION+this._t(" · Intégration "," · Integration ")+(this._snapshotData?.version||this._t("chargement…","loading…")),"integration-meta note");
    if(this._hass?.config?.version)meta.textContent+=" · HA "+this._hass.config.version;
    const equipmentCount=this._snapshotData?.flow?.usages?.length;if(equipmentCount!==undefined)meta.textContent+=" · "+equipmentCount+this._t(" usages/appareils suivis"," monitored loads/devices");title.append(meta);
    const actions = this._node("div", undefined, "actions");
    const menu = document.createElement("ha-menu-button");
    this._menu = menu;
    menu.hass = this._hass;
    menu.narrow = this.narrow;
    menu.setAttribute("aria-label", "Menu");
    header.append(menu);
    actions.append(this._button(this._t("Actualiser", "Refresh"), () => this._load()));
    header.append(title, actions); main.append(header);
    if (this._error) main.append(this._node("p", this._error, "status warn"));
    this._message = this._node("div", undefined, "status");
    this._message.setAttribute("role", "status"); main.append(this._message);
    const snapshot = this._snapshotData;
    if (snapshot) {
      if (snapshot.missing_entities?.length) main.append(this._node("p", this._t(
        "Certaines mesures sont manquantes ou désactivées. Vérifiez les associations dans l’intégration.",
        "Some readings are missing or disabled. Check integration mappings."), "note warn"));
      const nav = this._node("nav", undefined, "top-nav"); nav.setAttribute("aria-label", this._t("Vues énergie", "Energy views"));
      const sections = [[this._t("Vue d’ensemble", "Overview"), "summary"], [this._t("Mes Appareils", "My Appliances"), "appliances"],
        [this._t("Stockage", "Storage"), "storage"], [this._t("Photovoltaïque", "Photovoltaic"), "photovoltaic"], [this._t("Usages", "Loads"), "usages"], [this._t("Historique", "History"), "history"],
        [this._t("Aujourd’hui", "Today"), "today"], [this._t("Stratégie", "Strategy"), "strategy"], [this._t("Configuration", "Configuration"), "configuration"], [this._t("Alertes et Notifications", "Alerts and Notifications"), "alerts"]];
      sections.forEach(([title], index) => {
        const button = this._button(title, () => { this._tab = index; this._render(); });
        if (index === this._tab) button.setAttribute("aria-current", "page");
        nav.append(button);
      });
      main.append(nav);
      if (this._tab === 0) main.append(this._overview(snapshot));
      else if (this._tab === 7) main.append(this._strategy(snapshot.flow, true));
      else if (this._tab === 8) main.append(this._configuration(snapshot));
      else if (this._tab === 9) main.append(this._alerts());
      else if (this._tab === 2) main.append(this._storage(snapshot));
      else if (this._tab === 3) main.append(this._photovoltaic(snapshot));
      else if (this._tab === 4 || this._tab === 1) main.append(this._loads(snapshot, this._tab === 1));
      else if (this._tab === 6) main.append(this._today(snapshot));
      else {
        const path = sections[this._tab][1];
        const view = snapshot.dashboard.views.find(view => view.path === path);
        const content = this._node("section", undefined, "cards");
        for (const card of view?.cards || []) content.append(this._card(card));
        const pvPowers=(snapshot.flow?.photovoltaic||[]).flatMap(p=>[p.power,p.dc_power]).filter(Boolean);if(pvPowers.length)content.append(this._card({type:"history-graph",title:this._t("Photovoltaïque","Photovoltaic"),entities:[...new Set(pvPowers)]}));
        if (!view) content.append(this._node("p", this._t("Aucune mesure configurée pour cette vue.", "No readings configured for this view."), "note"));
        main.append(content);
      }
    }
    if (this._hass?.user?.is_admin) main.append(this._node("p", this._t("Cliquez sur une valeur pour son historique. Appui prolongé sur un nom : modifier ou retirer. Appui prolongé sur une mesure : changer sa source.", "Click a value for history. Hold a name to edit or remove. Hold a reading to change its source."), "note"));
    this.shadowRoot.append(main); this._refresh();
  }
  _bind(element, entity, attribute, gauge) {
    this._bindings.push({ element, entity, attribute, gauge });
    if(!attribute && !gauge)this._historyLink(element,entity);
  }
  _icon(name) { const el = this._node("ha-icon"); el.setAttribute("icon", name); return el; }
  _metricTile(label, entity, icon, color, valueProvider=null) {
    const tile = this._node("div", undefined, "kpi");
    tile.append(this._icon(icon), this._node("span", label, "kpi-label"));
    const value = this._node("span", undefined, "value");
    tile.style.setProperty("--tone", color || "#69b8ff");
    if (color) { value.style.color = color; tile.firstChild.style.color = color; }
    if(valueProvider)this._historyLink(value,entity);
    if(valueProvider)this._flowUpdates.push(()=>{const n=valueProvider();value.textContent=n===null?this._t("Indisponible","Unavailable"):displayNumber(n,this._hass?.language)+" kWh";value.classList.toggle("bad",n===null);});else this._bind(value, entity); tile.append(value);
    if (["W", "kW", "%"].includes(this._hass?.states?.[entity]?.attributes?.unit_of_measurement)) tile.append(this._spark(entity, color || "#69b8ff"));
    if (entity) this._editable(tile, entity);
    return tile;
  }
  _tone(entity) {
    const f = this._snapshotData?.flow;
    if (entity && entity === f?.entities?.solar_power) return "#ffc83d";
    if(entity && entity === f?.entities?.grid_import)return "#ff6565";
    if(entity && [f?.entities?.grid_export,f?.entities?.grid_power].includes(entity))return "#58aeff";
    if(f?.batteries?.some(b=>b.discharge_power===entity))return "#58aeff";
    if (f?.batteries?.some(b => Object.values(b).includes(entity))) return "#42dca4";
    const u = f?.usages?.find(u => Object.values(u).includes(entity));
    return ["solar_router","water_heater"].includes(u?.kind) ? "#ffa000" : u?.kind === "ev_charger" ? "#bb86fc" : "#5bb8ff";
  }
  _entityIcon(entity) {
    const f = this._snapshotData?.flow;
    if (entity && entity === f?.entities?.solar_power) return "mdi:white-balance-sunny";
    if (f?.batteries?.some(b => Object.values(b).includes(entity))) return "mdi:battery-high";
    const u = f?.usages?.find(u => Object.values(u).includes(entity));
    return u ? productIcon(u) : "mdi:home";
  }
  async _loadHistory() {
    // One bounded request per five minutes, using source history (also works just after installing).
    if (this._historyBusy || Date.now() - this._historyAt < 300000 || !this._hass?.callApi) return;
    const flow = this._snapshotData?.flow;
    if (!flow) return;
    const ids = [...new Set([...Object.values(flow.entities || {}), ...(flow.batteries || []).flatMap(b => [b.charge_power, b.discharge_power,b.soc]), ...(flow.usages || []).map(u => u.power),...(flow.photovoltaic||[]).flatMap(p=>[p.power,p.dc_power])].filter(Boolean))].slice(0, 100);
    const sources = ids.map(id => this._snapshotData.bindings?.[id]?.source || id);
    if (!ids.length) return;
    this._historyBusy = true;
    const mappingKey=JSON.stringify(this._snapshotData?.bindings);
    const start = new Date(Date.now() - 6 * 3600000).toISOString();
    try {
      const result = await this._hass.callApi("GET", `history/period/${start}?filter_entity_id=${encodeURIComponent([...new Set(sources)].join(","))}&minimal_response&no_attributes&significant_changes_only=0`);
      if(mappingKey!==JSON.stringify(this._snapshotData?.bindings)) return;
      if (!Array.isArray(result)) throw new Error("history unavailable");
      this._history = {};
      for (const records of result) {
        const source = records[0]?.entity_id;
        for (const id of ids.filter((id, index) => sources[index] === source)) this._history[id] = records;
      }
      this._historyAt = Date.now();
      for (const update of this._flowUpdates || []) update();
    } catch { this._history = {}; this._historyAt = Date.now(); }
    finally { this._historyBusy = false; }
  }
  async _loadHistory24() {
    if(this._tab!==5||this._history24Busy||!this._hass?.callApi)return;
    const ids=[...new Set([...this.shadowRoot.querySelectorAll(".history-chart")].map(el=>el.dataset.entity))].slice(0,100),sources=ids.map(id=>this._snapshotData?.bindings?.[id]?.source||id),key=JSON.stringify([ids,sources]);
    if(!ids.length||(key===this._history24Key&&Date.now()-(this._history24At||0)<300000))return;
    this._history24Busy=true;this._history24Key=key;
    try{
      const end=Date.now(),start=end-86400000;
      const response=await this._hass.callApi("GET",`history/period/${new Date(start).toISOString()}?filter_entity_id=${encodeURIComponent([...new Set(sources)].join(","))}&end_time=${new Date(end).toISOString()}&minimal_response&no_attributes&significant_changes_only=0`);
      if(key!==this._history24Key)return;
      this._history24={};for(const records of response||[]){for(const [i,id] of ids.entries())if(sources[i]===records[0]?.entity_id)this._history24[id]=records;}
      this._history24At=Date.now();
    }catch{this._history24={};this._history24At=Date.now();}finally{this._history24Busy=false;for(const update of this._flowUpdates||[])update();}
  }
  _historyChart(entity) {
    const root=this._node("div",undefined,"history-chart");root.dataset.entity=entity;
    this._flowUpdates.push(()=>{
      const records=this._history24?.[entity]||[],now=Date.now(),start=now-86400000,segments=historySegments(records).map(segment=>segment.filter(p=>p.time>=start&&p.time<=now)).filter(segment=>segment.length),values=segments.flat().map(p=>p.value);
      root.replaceChildren();
      const source=this._snapshotData?.bindings?.[entity]?.source||entity,unit=this._hass?.states?.[source]?.attributes?.unit_of_measurement||"";
      if(!values.length){root.append(this._node("span",this._t("Historique 24 h indisponible","24 h history unavailable"),"note"));return;}
      const low=Math.min(...values),high=Math.max(...values),svg=document.createElementNS("http://www.w3.org/2000/svg","svg");svg.setAttribute("viewBox","0 0 600 70");svg.setAttribute("preserveAspectRatio","none");svg.setAttribute("role","img");svg.setAttribute("aria-label",this._t("Historique des 24 dernières heures","History of the last 24 hours")+` · ${low}–${high} ${unit}`);
      for(const segment of segments){const path=document.createElementNS(svg.namespaceURI,"path");path.setAttribute("d",segment.map((p,i)=>`${i?"L":"M"}${(p.time-start)/86400000*600},${60-(p.value-low)/(high-low||1)*50}`).join(" "));path.setAttribute("fill","none");path.setAttribute("stroke","#5bb8ff");path.setAttribute("stroke-width","2");path.setAttribute("vector-effect","non-scaling-stroke");svg.append(path);}
      const format=t=>new Intl.DateTimeFormat(this._hass?.language||"fr",{timeZone:this._snapshotData?.time_zone||"UTC",hour:"2-digit",minute:"2-digit"}).format(t);
      root.append(svg,this._node("span",`${format(start)} → ${format(now)} · 24 h · ${unit}`,"note"));
    });return root;
  }
  _spark(entity, color) {
    const box=this._node("div",undefined,"spark trend"),head=this._node("div",undefined,"trend-head"),note=this._node("span",undefined,"spark-note");box.append(head,note);
    this._flowUpdates.push(()=>{
      const power=flowPower(this._hass?.states,entity);
      const flow=this._snapshotData?.flow,producing=entity===flow?.entities?.solar_power||entity===flow?.entities?.grid_export||flow?.photovoltaic?.some(p=>[p.power,p.dc_power].includes(entity))||flow?.batteries?.some(b=>entity===b.discharge_power);
      box.style.color=!producing&&power!==null&&power>0?"#ff6565":"#5bb8ff";
      const bins=quarterTrends(this._history[entity]||[]),direction=bins.at(-1).direction;
      head.textContent=direction===1?"↗":direction===-1?"↘":"→";
      head.setAttribute("aria-label",direction===null?this._t("Tendance inconnue : flèche horizontale","Unknown trend: horizontal arrow"):direction>0?this._t("En hausse","Rising"):direction<0?this._t("En baisse","Falling"):this._t("Stable","Stable"));
      note.textContent=this._t("Tendance sur 15 mn","15 min trend");note.title=bins.some(b=>b.value!==null)?this._t("Comparaison des moyennes par quart d’heure ; historique sur 6 h.","Quarter-hour mean comparison; 6 h history."):this._t("Données insuffisantes : flèche horizontale.","Insufficient data: horizontal arrow.");
    });return box;
  }
  _dayStart() {
    const now=Date.now(),zone=this._snapshotData?.time_zone||"UTC",cached=this._calendar;
    if(cached?.zone===zone&&now>=cached.start&&now<cached.end)return cached.start;
    const start=localDayStart(new Date(now),zone),end=localDayStart(new Date(start+36*3600000),zone);this._calendar={zone,start,end};return start;
  }
  async _loadUsageHistory() {
    if(!this._hass?.callApi||this._energyBusy)return;
    const start=this._dayStart(),ids=[...new Set([...(this._snapshotData?.flow?.usages||[]),...(this._snapshotData?.flow?.photovoltaic||[])].filter(u=>u.energy&&u.energy_period!=="session").map(u=>u.energy))].slice(0,100),sources=ids.map(id=>this._snapshotData?.bindings?.[id]?.source||id),key=JSON.stringify([start,sources]);
    if(key===this._energyKey && Date.now()-(this._energyAt||0)<300000)return;
    this._energyKey=key;this._energyStart=start;this._energyBusy=true;this._energyAt=Date.now();this._dailyHistory={};
    try{if(!ids.length)return;const response=await this._hass.callApi("GET",`history/period/${new Date(start).toISOString()}?filter_entity_id=${encodeURIComponent([...new Set(sources)].join(","))}&end_time=${new Date().toISOString()}&minimal_response&significant_changes_only=0`);
      if(this._energyKey!==key)return;
      for(const records of Array.isArray(response)?response:[])for(const id of ids.filter((id,i)=>sources[i]===records[0]?.entity_id))this._dailyHistory[id]=records;
    }catch{this._dailyHistory={};}finally{this._energyBusy=false;for(const update of this._flowUpdates||[])update();}
  }
  _dayEnergy(config) {
    if(config.energy_period==="session")return null;
    const source=this._snapshotData?.bindings?.[config.energy]?.source||config.energy,state=this._hass?.states?.[source],value=reading(this._hass?.states,source).number;
    if(value===null)return null;
    const start=this._dayStart(),records=this._dailyHistory?.[config.energy];
    if(this._energyStart!==start||records?.[0]?.entity_id!==source)return null;
    this._dayEnergyCache??=new Map();const unit=state?.attributes?.unit_of_measurement,cached=this._dayEnergyCache.get(config.energy);
    if(cached?.records===records&&cached.source===source&&cached.value===value&&cached.unit===unit&&cached.start===start)return cached.result;
    const result=dailyFromCounter(records,value,unit,start);this._dayEnergyCache.set(config.energy,{records,source,value,unit,start,result});return result;
  }
  _usageEnergy(config) {
    const box=this._node("div",undefined,"usage-energy"),daily=this._node("p",undefined,"energy-value"),caption=this._node("p",undefined,"note"),raw=this._node("p",undefined,"note");const progress=this._node("p",undefined,"note goal-progress");box.append(daily,caption,progress);
    this._flowUpdates.push(()=>{if(config.kind==="ev_charger"){
      const session=config.ev_session||{},last=session.last_session||{},shown=session.active?session:last;
      daily.textContent=shown.energy_kwh==null?this._t("Session indisponible","Session unavailable"):displayNumber(shown.energy_kwh,this._hass?.language)+" kWh";
      daily.classList.toggle("bad",shown.energy_kwh==null);
      caption.textContent=session.active?this._t("Recharge en cours · depuis le début de session","Charging · since session start"):this._t("Dernière recharge terminée","Last completed charging session");
      progress.hidden=true;return;
    }const n=this._dayEnergy(config),session=config.energy_period==="session";
      daily.textContent=session?reading(this._hass?.states,config.energy,undefined,this._hass?.language).text:n===null?this._t("Jour indisponible","Daily unavailable"):displayNumber(n,this._hass?.language)+" kWh";
      daily.classList.toggle("bad",!session&&n===null);
      const goal=dailyGoalPercent(n,config.daily_energy_goal_kwh);progress.hidden=!config.daily_energy_goal_kwh;progress.textContent=goal===null?this._t("Objectif : données du jour indisponibles","Goal: daily data unavailable"):percent(goal,this._hass?.language)+this._t(" % de l’objectif quotidien ("," % of daily goal (")+displayNumber(config.daily_energy_goal_kwh,this._hass?.language)+" kWh)";
      caption.textContent=session?this._t("Énergie de session · pas un compteur du jour","Session energy · not a daily counter"):this._t("Aujourd’hui · calcul depuis le compteur","Today · calculated from counter");
      raw.textContent=(session?this._t("Énergie de session : ","Session energy: "):this._t("Énergie Totale : ","Total energy: "))+reading(this._hass?.states,config.energy,undefined,this._hass?.language).text+(n===null&&!session?this._t(" · référence à minuit absente"," · missing midnight baseline"):"");
    });if(config.energy){this._historyLink(daily,config.energy);this._historyLink(raw,config.energy);this._editable(box,config.energy);}return box;
  }
  _usageCost(config) {
    const el=this._node("p",undefined,"cost note");this._flowUpdates.push(()=>{if(config.kind==="ev_charger"){
      const session=config.ev_session||{},shown=session.active?session:session.last_session||{},value=shown.cost_eur;
      el.classList.toggle("bad",value==null);
      el.textContent=value==null?this._t("Coût de session indisponible","Session cost unavailable"):"≈ "+new Intl.NumberFormat(this._hass?.language||"fr",{style:"currency",currency:"EUR"}).format(value)+this._t(" · session estimée"," · estimated session");
      return;
    }const n=this._dayEnergy(config),tariff=this._snapshotData?.tariff_eur_kwh;
      el.classList.toggle("bad",n===null||typeof tariff!=="number"||!Number.isFinite(tariff));
      el.textContent=n!==null&&typeof tariff==="number"&&Number.isFinite(tariff)?"≈ "+new Intl.NumberFormat(this._hass?.language||"fr",{style:"currency",currency:"EUR"}).format(n*tariff)+this._t(" aujourd’hui · estimation"," today · estimate"):this._t("€ du jour indisponible : historique à minuit et tarif requis","Daily EUR unavailable: midnight history and tariff required");
    });return el;
  }
  _energy(entity) {
    const value = reading(this._hass?.states, entity).number;
    const unit = this._hass?.states?.[entity]?.attributes?.unit_of_measurement;
    return value !== null && value >= 0 && ["Wh","kWh"].includes(unit) ? value * (unit === "Wh" ? .001 : 1) : null;
  }
  _cost(entity, period) {
    const el = this._node("p", undefined, "cost note");
    this._flowUpdates.push(() => {
      const energy = period === "today" ? this._energy(entity) : null;
      const tariff = this._snapshotData?.tariff_eur_kwh;
      el.textContent = energy !== null && typeof tariff === "number" && Number.isFinite(tariff) ?
        `≈ ${new Intl.NumberFormat(this._hass?.language || "fr", {style:"currency",currency:"EUR"}).format(energy * tariff)} ` + this._t("aujourd’hui · estimation", "today · estimate") :
        this._t(period === "today" ? "€ : renseigner un tarif et une énergie du jour" : "€ du jour : compteur journalier nécessaire", period === "today" ? "EUR: configure tariff and daily energy" : "Daily EUR requires a daily counter");
    });return el;
  }
  _integrationLink(text) {
    const a = this._node("a", text); a.href = "/config/integrations/integration/ehome_ems"; return a;
  }
  _photovoltaic(snapshot) {
    const root=this._node("section",undefined,"stack");root.append(this._node("h2",this._t("Photovoltaïque","Photovoltaic")),this._node("p",this._t("Total des productions déclarées : une seule puissance par équipement (DC si disponible, sinon AC). Pour un hybride, une source DC solaire est nécessaire. Ce total indicatif ne remplace pas le bilan Maison AC.","Declared production total: one power per equipment (DC when available, otherwise AC). A hybrid requires a solar DC source. This indicative total does not replace the AC Home balance."),"note"));
    const items=snapshot.flow?.photovoltaic||[],resolve=id=>snapshot.bindings?.[id]?.source||id;
    const productions=pvProductionSources(items,resolve),energyItems=items.filter(item=>item.kind!=="hybrid_inverter"&&item.energy&&item.energy_period!=="session").filter((item,i,all)=>all.findIndex(other=>resolve(other.energy)===resolve(item.energy))===i);
    const totals=this._node("div",undefined,"cards pv-totals"),powerTile=this._node("div",undefined,"card"),energyTile=this._node("div",undefined,"card");
    const powerValue=this._node("span",undefined,"value"),energyValue=this._node("span",undefined,"value"),coverage=this._node("p",undefined,"note");
    powerTile.append(this._node("h3",this._t("Production globale","Total production")),powerValue);energyTile.append(this._node("h3",this._t("Énergie produite aujourd’hui","Energy produced today")),energyValue);totals.append(powerTile,energyTile);root.append(totals,coverage);
    const maximum=this._node("span",undefined,"pv-meta"),savings=this._node("span",undefined,"pv-meta");powerTile.append(maximum);energyTile.append(savings);
    this._historyLink(powerValue,productions.map(p=>p.production));this._historyLink(energyValue,energyItems.map(p=>p.energy));
    this._flowUpdates.push(()=>{
      const power=strictSum(productions.map(p=>flowPower(this._hass?.states,p.production))),energy=strictSum(energyItems.map(p=>this._dayEnergy(p)));
      powerValue.textContent=power===null?this._t("Indisponible","Unavailable"):displayNumber(power,this._hass?.language)+" W";
      energyValue.textContent=energy===null?this._t("Indisponible","Unavailable"):displayNumber(energy,this._hass?.language)+" kWh";
      const nominal=strictSum(productions.map(p=>p.nominal_power_w??null)),tariff=snapshot.tariff_eur_kwh;
      maximum.textContent=nominal===null?this._t(" · maximum déclaré non renseigné"," · declared maximum not configured"):" · "+displayNumber(nominal,this._hass.language)+this._t(" W max déclarés"," W declared max");
      savings.textContent=energy!==null&&typeof tariff==="number"&&Number.isFinite(tariff)?" · ≈ "+new Intl.NumberFormat(this._hass.language,{style:"currency",currency:"EUR"}).format(energy*tariff)+this._t(" d’économie potentielle"," potential savings"):this._t(" · valorisation indisponible"," · valuation unavailable");
      savings.title=this._t("Production valorisée au tarif fixe : estimation maximale si toute cette énergie remplace un achat réseau, sans déduction des exports.","Production valued at the flat tariff: maximum estimate if all energy replaces grid purchases, before deducting exports.");
      coverage.textContent=this._t("Sources additionnées : ","Summed sources: ")+productions.length+" / "+items.length+this._t(" équipements (puissance), "," equipment (power), ")+energyItems.length+this._t(" compteurs d’énergie uniques. Une source manquante rend le total suivi indisponible. Les périmètres chevauchants doivent être retirés du suivi. L’énergie des hybrides est exclue : une sortie AC peut inclure la batterie."," unique energy counters. A missing source makes the monitored total unavailable. Overlapping scopes must be removed from monitoring.");
    });
    root.append(this._node("p",this._t("Économie potentielle : production valorisée au tarif configuré, avant déduction de l’export. Le maximum est la somme des puissances nominales renseignées, pas un pic mesuré.","Potential savings: production valued at the configured tariff before deducting exports. Maximum is the sum of configured nominal powers, not a measured peak."),"note"));
    if(this._hass?.user?.is_admin)root.append(this._button(this._t("Ajouter un équipement photovoltaïque","Add PV equipment"),()=>this._settingsDialog("photovoltaic")));
    const grid=this._node("div",undefined,"cards");
    for(const item of snapshot.flow?.photovoltaic||[]){
      const card=this._node("section",undefined,"card pv-card");card.append(this._node("h2",item.name),this._node("p",({micro_inverter:this._t("Micro-onduleur","Microinverter"),dc_inverter:this._t("Onduleur DC","DC inverter"),hybrid_inverter:this._t("Onduleur hybride","Hybrid inverter")}[item.kind]||item.kind)+" · "+[item.manufacturer,item.model].filter(Boolean).join(" "),"note"));
      if(item.nominal_power_w)card.append(this._node("p",this._t("Puissance nominale : ","Nominal power: ")+displayNumber(item.nominal_power_w,this._hass?.language)+" W","note"));
      const measurements=this._node("div",undefined,"cards");
      for(const [key,fr,en] of [["power","Sortie AC","AC output"],["dc_power","Production DC","DC production"],["charge_power","Charge batterie (source déclarée)","Battery charge (declared source)"],["discharge_power","Décharge batterie (source déclarée)","Battery discharge (declared source)"]])if(item[key])measurements.append(this._metricTile(this._t(fr,en),item[key],"mdi:white-balance-sunny","#ffc83d"));
      card.append(measurements);if(item.energy)card.append(this._usageEnergy(item));
      for(const [key,fr,en] of [["temperature","Température","Temperature"],["status","État","Status"]])if(item[key]){const row=this._node("p",undefined,"note"),value=this._node("span");this._bind(value,item[key]);row.append(this._t(fr,en)+" : ",value);card.append(row);}
      this._equipmentActions(card,item,"photovoltaic");grid.append(card);
    }
    if(!grid.childElementCount)grid.append(this._node("p",this._t("Ajoutez vos micro-onduleurs, onduleurs DC ou hybrides depuis leurs entités HA existantes.","Add microinverters, DC or hybrid inverters using existing HA entities."),"note"));root.append(grid);return root;
  }
  _heaterSummary(config) {
    const root=this._node("div",undefined,"heater-layout"),visual=this._node("div",undefined,"cumulus-visual"),fill=this._node("div",undefined,"cumulus-fill");
    visual.setAttribute("aria-label",this._t("Cumulus · progression de l’objectif énergétique","Water heater · energy goal progress"));visual.append(fill,this._icon("mdi:water-boiler"));
    const details=this._node("div",undefined,"heater-details"),power=this._node("div",undefined,"vessel-main");this._bind(power,config.power);details.append(power,this._usageEnergy(config),this._usageCost(config));
    const caption=this._node("p",this._t("Progression énergétique du jour ; ne mesure pas la chaleur restante.","Today’s energy progress; not remaining heat."),"note");
    this._flowUpdates.push(()=>{const level=dailyGoalPercent(this._dayEnergy(config),config.daily_energy_goal_kwh);fill.style.height=(level===null?0:Math.max(0,Math.min(100,level)))+"%";caption.hidden=!config.daily_energy_goal_kwh;});
    root.append(visual,details);details.append(caption);return root;
  }
  _routerCard(config) {
    if(config.router_connection==="http")return this._routerHttpCard(config);
    const root=this._node("section",undefined,"card router-card"),details=this._node("details",undefined,"router-settings");root.append(this._node("h2",config.name),this._node("p","F1ATB · "+(config.router_output||"ssr").toUpperCase(),"note"));
    root.append(this._heaterSummary(config));


    for(const [key,fr,en] of [["temperature","Température","Temperature"],["status","État","Status"]])if(config[key]){const line=this._node("p",undefined,"note"),value=this._node("span");this._bind(value,config[key]);line.append(this._t(fr,en)+" : ",value);root.append(line);}
    if(!config.power&&!config.energy&&!config.status)root.append(this._node("p",this._t("Mesures non associées : aucune puissance supposée.","No readings mapped: no assumed power."),"note"));details.append(this._node("summary",this._t("Paramétrage F1ATB","F1ATB settings")));
    details.append(this._node("p",this._t("Commandes MQTT manuelles V15+ : temporaires, non sauvegardées par le routeur. Vérifiez le firmware et le retour d’état. Les horaires complets, sécurités et paramètres réseau restent gérés dans la page native.","Manual V15+ MQTT commands: temporary, not saved by the router. Check firmware and state feedback. Full schedules, protections and network settings remain on the native page."),"note"));
    if(config.router_url){const link=this._node("a",this._t("Ouvrir la page du routeur","Open router page"));link.href=config.router_url;link.target="_blank";link.rel="noopener noreferrer";details.append(link);}
    const doc=this._node("a",this._t("Documentation officielle F1ATB","Official F1ATB documentation"));doc.href="https://f1atb.fr/fr/documentation-routeur-photovoltaique-f1atb/pages-web-ihm/action/actions-via-mqtt/";doc.target="_blank";doc.rel="noopener noreferrer";details.append(this._node("p"));details.append(doc);
    if(!config.router_mqtt_enabled){details.append(this._node("p",this._t("Associez le topic de l’action et activez volontairement les commandes dans Modifier. Dans F1ATB, activer la souscription au forçage des actions via MQTT.","Map the action topic and explicitly enable commands in Edit. Enable MQTT action forcing subscription in F1ATB."),"note"));root.append(details);return root;}
    const form=this._node("form",undefined,"settings-form"),fields={};
    const add=(key,label,type="number",options=null)=>{const row=this._node("label",label),el=this._node(options?"select":"input");if(options){for(const option of options){const o=this._node("option",option);o.value=option;el.append(o);}}else{el.type=type;el.step="1";}el.setAttribute("aria-label",label);fields[key]=el;row.append(el);form.append(row);return el;};
    const minutes=add("minutes",this._t("Durée du forçage (minutes)","Override duration (minutes)"));minutes.min=1;minutes.max=1440;minutes.value=30;minutes.required=true;
    const period=add("period",this._t("Index de période F1ATB (0–7)","F1ATB period index (0–7)"));period.min=0;period.max=7;period.value=0;period.required=true;
    const modes={ssr:["Inactif","OnOff","Demi","Multi","Train"],triac:["Inactif","Decoupe","Demi","Multi","Train"],pwm:["Inactif","PWM"]};add("mode",this._t("Mode immédiat de l’action (facultatif)","Immediate action mode (optional)"),"text",["",...(modes[config.router_output||"ssr"]||[])]);
    for(const [key,fr,en,min,max] of [["opening_max","Ouverture maximale (%)","Maximum opening (%)",0,100],["threshold_on","Seuil On (W)","On threshold (W)",-100000,100000],["threshold_off","Seuil Off (W)","Off threshold (W)",-100000,100000]]){const input=add(key,this._t(fr,en));input.min=min;input.max=max;}
    const feedback=this._node("p",undefined,"note");feedback.setAttribute("role","status");let busy=false;const buttons=[];
    form.addEventListener("submit",event=>event.preventDefault());
    const send=async(action)=>{if(busy||!this._hass?.user?.is_admin)return;let values={};if(action==="force_on"||action==="force_off"){if(!minutes.reportValidity())return;values={minutes:Number(minutes.value)};}else if(action==="parameters"){for(const key of ["period","mode","opening_max","threshold_on","threshold_off"])if(!fields[key].reportValidity())return;values.period=Number(period.value);for(const key of ["mode","opening_max","threshold_on","threshold_off"])if(fields[key].value!=="")values[key]=key==="mode"?fields[key].value:Number(fields[key].value);if(Object.keys(values).length===1){feedback.textContent=this._t("Choisissez au moins un réglage à appliquer.","Choose at least one setting to apply.");return;}}
      busy=true;for(const b of buttons)b.disabled=true;try{await this._hass.callWS({type:"ehome_ems/router_command",entry_id:this._panel.config.entry_id,identifier:config.id,revision:this._snapshotData.revision,action,values});feedback.textContent=this._t("Ordre MQTT publié, réception par le routeur non confirmée. Contrôlez ses mesures et sa page native.","MQTT command published; router receipt not confirmed. Check readings and its native page.");}catch{feedback.textContent=this._t("Commande refusée ou publication MQTT impossible. Vérifiez la configuration et actualisez.","Command rejected or MQTT publication failed. Check settings and refresh.");}finally{busy=false;for(const b of buttons)b.disabled=!this._hass?.user?.is_admin;}};
    for(const [action,fr,en] of [["force_on","Forcer On temporairement","Temporary On"],["force_off","Forcer Off temporairement","Temporary Off"],["release","Libérer le forçage","Release override"],["parameters","Appliquer les réglages MQTT","Apply MQTT settings"]]){const button=this._button(this._t(fr,en),()=>send(action));button.disabled=!this._hass?.user?.is_admin;buttons.push(button);form.append(button);}
    details.append(this._node("p",this._t("L’index vise une période déjà créée sur le routeur. Le mode concerne l’action et peut prendre effet immédiatement, indépendamment de cette période.","The index targets an existing router period. Mode affects the action and may take effect immediately, independently of that period."),"note"),form,feedback);root.append(details);return root;
  }
  _routerHttpCard(config) {
    const root=this._node("section",undefined,"card router-card native-router"),native=config.router_native||{},entities=config.router_entities||{},selected=(native.actions||[]).find(a=>a.index===config.router_action);
    root.append(this._node("h2",config.name),this._node("p",this._t("F1ATB · connexion locale directe","F1ATB · direct local connection"),"note"));
    const status=this._node("p",undefined,"note"),state=this._node("span");status.append(this._t("Action : ","Action: ")+(selected?.name||String(config.router_action??0))+" · ",state);root.append(status);
    root.append(this._heaterSummary(config));
    for(const [key,fr,en] of [["opening","Ouverture de l’action","Action opening"],["force_minutes","Forçage restant (+ On / − Off)","Override remaining (+ On / − Off)"]])if(entities[key])root.append(this._metricTile(this._t(fr,en),entities[key],"mdi:white-balance-sunny","#ffa000"));
    const meter=this._node("details");meter.append(this._node("summary",this._t("Mesures du routeur","Router measurements")));
    meter.append(this._node("p",this._t("La seconde voie de mesure est globale au routeur. Elle n’est pas attribuée à cette action et n’est pas ajoutée au bilan Maison. Une ouverture n’est pas une mesure de puissance.","The second measurement channel belongs to the router. It is not assigned to this action or added to Home balance. Opening is not a power measurement."),"note"));
    for(const [key,fr,en] of [["probe_power","Puissance mesurée · seconde voie","Measured power · second channel"],["probe_energy_total_kwh","Énergie cumulée · seconde voie","Lifetime energy · second channel"],["grid_import_power","Soutirage réseau","Grid import"],["grid_export_power","Injection réseau","Grid export"]])if(entities[key])meter.append(this._metricTile(this._t(fr,en),entities[key],"mdi:white-balance-sunny","#ffa000"));
    for(let i=0;i<4;i++)if(entities["temperature_"+i])meter.append(this._metricTile(this._t("Température ","Temperature ")+i,entities["temperature_"+i],"mdi:water-boiler","#ffa000"));
    this._flowUpdates.push(()=>{const value=this._hass?.states?.[entities.status]?.state;state.textContent=({auto:this._t("Automatique","Automatic"),forced_on:this._t("Marche forcée","Forced On"),forced_off:this._t("Arrêt forcé","Forced Off")})[value]||this._t("Indisponible ou action inactive","Unavailable or inactive action");});
    root.append(meter);

    const link=this._node("a",this._t("Ouvrir la page du routeur","Open router page"));link.href=config.router_url?.includes("://")?config.router_url:"http://"+config.router_url;link.target="_blank";link.rel="noopener noreferrer";root.append(link);
    const details=this._node("details",undefined,"router-settings");details.append(this._node("summary",this._t("Paramétrage F1ATB","F1ATB settings")));
    if(!config.router_http_enabled){details.append(this._node("p",this._t("Lecture seule. Activez les commandes HTTP manuelles dans Modifier pour piloter cette action.","Read only. Enable manual HTTP commands in Edit to control this action."),"note"));root.append(details);return root;}
    const form=this._node("form",undefined,"settings-form"),fields={},buttons=[];form.addEventListener("submit",e=>e.preventDefault());
    const add=(key,label,value,min,max,options)=>{const row=this._node("label",label),el=this._node(options?"select":"input");if(options){for(const [v,text] of options){const o=this._node("option",text);o.value=v;el.append(o);}}else{el.type="number";el.min=min;el.max=max;el.step=1;}el.value=value??"";el.setAttribute("aria-label",label);fields[key]=el;row.append(el);form.append(row);return el;};
    const minutes=add("minutes",this._t("Durée du forçage (minutes)","Override duration (minutes)"),30,1,1440);minutes.required=true;
    const feedback=this._node("p",undefined,"note");feedback.setAttribute("role","status");let busy=false;
    const send=async(action)=>{
      if(busy||!this._hass?.user?.is_admin)return;
      let values={};
      if(action==="force_on"||action==="force_off"){if(!minutes.reportValidity())return;values.minutes=Number(minutes.value);}
      if(action==="boost_hour")values.config_token=native.config_token;
      if(action==="http_parameters"){
        values.config_token=native.config_token;
        for(const key of ["mode","forced_opening","opening_max"]){if(!fields[key].reportValidity())return;if(fields[key].value!=="")values[key]=Number(fields[key].value);}
        if("opening_max" in values){if(!fields.period.value){feedback.textContent=this._t("Choisissez une période compatible.","Choose a compatible period.");return;}values.period=Number(fields.period.value);}
        if(Object.keys(values).length===1){feedback.textContent=this._t("Choisissez au moins un réglage.","Choose at least one setting.");return;}
      }
      busy=true;buttons.forEach(b=>b.disabled=true);
      try{const result=await this._hass.callWS({type:"ehome_ems/router_command",entry_id:this._panel.config.entry_id,identifier:config.id,revision:this._snapshotData.revision,action,values});
        feedback.textContent=result.confirmed_by_router?this._t("Réglage confirmé par relecture du routeur.","Setting confirmed by router readback."):this._t("Ordre envoyé, résultat non confirmé. Actualisez avant toute nouvelle commande.","Command sent, result unconfirmed. Refresh before another command.");
        if(action==="http_parameters"||action==="boost_hour")native.config_token=null;
      }catch(error){feedback.textContent=this._t("Commande refusée ou communication impossible. Actualisez et vérifiez le routeur : ","Command rejected or communication failed. Refresh and check router: ")+(error.code||"");}
      finally{busy=false;updateButtons();}
    };
    for(const [action,fr,en] of [["force_on","Forcer On temporairement","Temporary On"],["force_off","Forcer Off temporairement","Temporary Off"],["release","Libérer le forçage","Release override"]]){const b=this._button(this._t(fr,en),()=>send(action));b.dataset.action=action;buttons.push(b);form.append(b);}
    const boost=this._button(this._t("Forcer 1 h à 100 %","Force 1 h at 100%"),()=>send("boost_hour"));boost.dataset.action="boost_hour";buttons.push(boost);root.append(boost);
    root.append(this._node("p",this._t("Action manuelle prioritaire : règle l’ouverture de marche forcée à 100 %, puis force 60 minutes. Le réglage 100 % reste enregistré. Retour Auto à expiration ; thermostat du cumulus conservé.","Manual priority: sets forced opening to 100%, then forces 60 minutes. The 100% setting remains saved. Auto resumes on expiry; heater thermostat remains in control."),"note"));
    form.append(this._node("p",this._t("Réglages enregistrés dans le routeur : seules les valeurs renseignées sont modifiées. Les horaires, protections et paramètres réseau sont conservés.","Settings saved in the router: only filled values change. Schedules, protections and network settings are preserved."),"note"));
    add("mode",this._t("Forme d’onde (facultatif)","Waveform (optional)"),"",null,null,[["",this._t("Conserver","Keep")],[0,this._t("Inactif","Inactive")],[1,config.router_action===0?this._t("Découpe sinus","Phase cut"):"On/Off"],[5,this._t("Demi-sinus","Half sine")],[2,this._t("Multi-sinus","Multi sine")],[3,this._t("Train de sinus","Burst fire")],[4,"PWM"]]);
    add("forced_opening",this._t("Ouverture en marche forcée (%)","Forced On opening (%)"),"",0,100);
    const ps=(selected?.periods||[]).flatMap((p,i)=>p.Type===4&&(config.router_action===0||selected.mode>1)?[[String(i),this._t("Période ","Period ")+i+" · "+p.Vmax+" %"]]:[]);
    add("period",this._t("Période à limiter","Period to limit"),"",null,null,[["",this._t("Choisir une période","Choose a period")],...ps]);
    add("opening_max",this._t("Ouverture maximale de cette période (%)","Maximum opening for this period (%)"),"",0,100);
    const apply=this._button(this._t("Enregistrer les réglages sur le routeur","Save settings to router"),()=>send("http_parameters"));apply.dataset.action="http_parameters";buttons.push(apply);form.append(apply);
    const updateButtons=()=>{
      const online=entities.connection?this._hass?.states?.[entities.connection]?.state==="online":native.available;
      const actionAvailable=!!this._hass?.states?.[entities.status]&&!['unknown','unavailable'].includes(this._hass.states[entities.status].state);
      for(const b of buttons)b.disabled=busy||!this._hass?.user?.is_admin||!online||(["http_parameters","boost_hour"].includes(b.dataset.action)?!native.config_token||!actionAvailable:!actionAvailable);
    };
    updateButtons();this._flowUpdates.push(updateButtons);details.append(form);root.append(feedback,details);return root;
  }
  _loads(snapshot, appliances) {
    const root=this._node("section",undefined,"stack");
    root.append(this._node("h2",appliances?this._t("Mes Appareils","My Appliances"):this._t("Usages","Loads")),

      this._node("p",this._t("Sous-comptages inclus dans le total maison. On/Off manuel uniquement si associé et activé.", "Submetering included in home total. Manual On/Off only when mapped and enabled."),"note"));
    if(this._hass?.user?.is_admin)root.append(this._button(appliances?this._t("Ajouter un appareil","Add appliance"):this._t("Ajouter un usage","Add load"),()=>this._settingsDialog(appliances?"appliances":"usages")));
    const grid=this._node("div",undefined,"cards");
    const usages=(snapshot.flow?.usages||[]).filter(u => (u.kind === "appliance") === appliances);
    for(const u of usages) {
      if(["solar_router","water_heater"].includes(u.kind)) { const card=u.kind==="solar_router"&&u.router_type==="f1atb"?this._routerCard(u):this._vessel(u,true);this._equipmentActions(card,u,appliances?"appliances":"usages");grid.append(card);continue; }
      if(u.kind === "ev_charger") {const card=this._charger(u);this._equipmentActions(card,u,"usages");grid.append(card);continue;}
      const tile=this._metricTile(u.name,u.power,productIcon(u),this._tone(u.power));
      tile.classList.add("appliance-card");
      tile.append(this._usageEnergy(u),this._usageCost(u));
      tile.append(this._manualControl(u,appliances?"appliances":"usages"));
      this._equipmentActions(tile,u,appliances?"appliances":"usages");grid.append(tile);
    }
    if(!usages.length)grid.append(this._node("p",this._t("Aucun appareil associé. Utilisez Ajouter un appareil.","No appliances mapped. Use Add appliance."),"note"));
    root.append(grid);return root;
  }
  _manualControl(config,section="usages") {
    const root=this._node("div",undefined,"equipment-status"),note=this._node("span",undefined,"note");
    if(!config.control_enabled||!config.control_entity){
      if(config.status)this._bind(note,config.status);root.append(note);
      if(this._hass?.user?.is_admin)root.append(this._button(this._t("Associer On/Off","Map On/Off"),()=>this._settingsDialog(section,config.id)));
      return root;
    }
    let pending=false;
    const button=this._button("",async()=>{
      const state=this._hass?.states?.[config.control_entity]?.state;
      if(pending||!["on","off"].includes(state)||!this._hass?.user?.is_admin)return;
      pending=true;update();note.textContent=this._t("Commande en cours…","Sending command…");
      try{await this._hass.callWS({type:"ehome_ems/manual_control",entry_id:this._panel.config.entry_id,identifier:config.id,revision:this._snapshotData.revision,desired_on:state!=="on",expected_state:state});note.textContent=this._t("Commande envoyée ; état HA affiché.","Command sent; showing HA state.");}
      catch(error){note.textContent=error.code==="state_changed"||error.code==="conflict"?this._t("État ou configuration modifié : actualisez.","State or settings changed: refresh."):this._t("Commande refusée ou en échec. Vérifiez l’association.","Command rejected or failed. Check the mapping.");}
      finally{pending=false;update();}
    });
    button.classList.add("manual-toggle");
    const update=()=>{const state=this._hass?.states?.[config.control_entity]?.state,known=["on","off"].includes(state);button.textContent=pending?this._t("En cours…","Sending…"):known?(state==="on"?"On":"Off"):this._t("Indisponible","Unavailable");button.disabled=pending||!known||!this._hass?.user?.is_admin;button.setAttribute("aria-pressed",String(state==="on"));button.setAttribute("aria-label",(state==="on"?this._t("Éteindre ","Turn off "):this._t("Allumer ","Turn on "))+config.name);button.classList.toggle("ok",state==="on");};
    note.setAttribute("role","status");root.append(button,note);this._flowUpdates.push(update);update();return root;
  }
  _vessel(config, thermal=false) {
    const card=this._node("section",undefined,"card vessel-card");
    card.style.setProperty("--tone",thermal?"#ffa000":"#42dca4");
    card.append(this._node("h2",config.name));
    const layout=this._node("div",undefined,"vessel-layout"),visual=this._node("div",undefined,"vessel-icon");
    // The real HA/MDI icon is used as the silhouette; fill is a measured SOC overlay.
    const mdi=thermal?"mdi:water-boiler":"mdi:battery-outline";
    visual.append(this._icon(mdi));
    const fill=this._node("div",undefined,"vessel-fill");fill.append(this._icon(thermal ? mdi : "mdi:battery"));visual.append(fill);
    const details=this._node("div",undefined,"vessel-details");
    const main=this._node("div",undefined,"vessel-main");if(!thermal)this._bind(main,config.soc);else this._flowUpdates.push(()=>{const value=reading(this._hass?.states,config.temperature,undefined,this._hass?.language),goal=config.daily_energy_goal_kwh,progress=dailyGoalPercent(this._dayEnergy(config),goal);main.textContent=goal?progress===null?this._t("Objectif : données indisponibles","Goal: data unavailable"):percent(progress,this._hass?.language)+" %":value.number!==null?value.text:config.temperature?this._t("Température indisponible","Temperature unavailable"):this._t("Température non associée","Temperature not mapped");main.classList.toggle("bad",goal?progress===null:!!config.temperature&&value.number===null);main.style.fontSize=(goal?progress===null:value.number===null)?"20px":"";});if(!thermal||!config.daily_energy_goal_kwh)this._editable(main,thermal?config.temperature:config.soc);
    const direction=this._node("p",undefined,"vessel-direction"),mode=this._node("p",undefined,"note"),energy=this._node("p",undefined,"energy-value");
    if(!thermal){this._bind(energy,config.remaining_energy);this._editable(energy,config.remaining_energy);}
    this._historyLink(direction,thermal?config.power:[config.charge_power,config.discharge_power]);
    const caption=this._node("p",thermal?this._t("Énergie · ","Energy · ") + ({today:this._t("aujourd’hui","today"),session:"session",total:this._t("compteur cumulé","lifetime counter")}[config.energy_period]||this._t("non associée","not mapped")):this._t("disponibles · énergie mesurée","available · measured energy"),"note");
    const autonomy=this._node("p",undefined,"note");
    this._flowUpdates.push(() => {
      const soc=reading(this._hass?.states,config.soc).number;
      const temperature = reading(this._hass?.states,config.temperature).number;
      const level = thermal ? config.daily_energy_goal_kwh?dailyGoalPercent(this._dayEnergy(config),config.daily_energy_goal_kwh):temperature : soc;
      visual.style.setProperty("--fill",level!==null?`${Math.max(0,Math.min(100,level))}%`:"0%");
      fill.style.clipPath = !thermal && soc !== null ? `inset(${88 - Math.max(0,Math.min(100,soc)) * .72}% 0 12% 0)` : "";
      visual.style.color=thermal?"#ffa000":soc===null?"#8291a2":soc<20?"#ff5959":soc<50?"#ffbf44":"#42dca4";
      card.style.setProperty("--tone", thermal ? "#ffa000" : visual.style.color);
      const charge=flowPower(this._hass?.states,thermal?config.power:config.charge_power), discharge=thermal?0:flowPower(this._hass?.states,config.discharge_power);
      direction.textContent=thermal?reading(this._hass?.states,config.power).text:charge===null&&discharge===null?this._t("Puissance indisponible","Power unavailable"):
        `${charge>=FLOW_MIN_WATTS?"↓ ":discharge>=FLOW_MIN_WATTS?"↑ ":""}${displayNumber(charge>=FLOW_MIN_WATTS?charge:discharge??charge,this._hass?.language)} W`;
      direction.style.color = thermal ? "#ffa000" : charge>=10?"#50e49b":discharge>=10?"#58aeff":"#65c487";
      mode.textContent=thermal?(charge>=10?this._t("Je chauffe l’eau","Heating water"):charge===null?this._t("Puissance non associée","Power not mapped"):this._t("Veille / faible puissance","Idle / low power")):
        charge>=10?this._t("Je stocke","Charging"):discharge>=10?this._t("Je restitue","Discharging"):charge===null||discharge===null?this._t("Mesure de puissance incomplète","Incomplete power readings"):this._t("Au repos / faible puissance","Idle / low power");
      if(!thermal) {
        const stock=this._energy(config.remaining_energy),load=flowPower(this._hass?.states,this._snapshotData?.flow?.entities?.home_power);
        autonomy.textContent=stock!==null&&load>=10?this._t("Autonomie indicative ≈ ","Indicative runtime ≈ ")+ (stock*1000/load).toFixed(1)+" h · "+this._t("charge maison actuelle, pertes exclues","current home load, losses excluded"):this._t("Autonomie : données insuffisantes","Runtime: insufficient data");
      } else autonomy.textContent=config.daily_energy_goal_kwh?this._t("Objectif quotidien : ","Daily goal: ")+displayNumber(config.daily_energy_goal_kwh,this._hass?.language)+this._t(" kWh · énergie consommée, pas chaleur restante. Température : "," kWh · consumed energy, not remaining heat. Temperature: ")+reading(this._hass?.states,config.temperature,undefined,this._hass?.language).text:this._t("Échelle température : 0–100 °C, pas un stock thermique.","Temperature scale: 0–100 °C, not thermal energy storage.");
    });
    details.append(main,direction,mode,thermal?this._usageEnergy(config):energy,thermal?this._usageCost(config):caption);
    if(!thermal)details.append(autonomy);
    if(thermal)details.append(autonomy);else details.append(this._node("p",`${config.role === "active"?this._t("Active","Active"):this._t("Secours","Backup")} · ${config.coupling?.toUpperCase()}`,"note"));
    if(thermal&&(config.router_type!=="f1atb"||config.control_enabled))details.append(this._manualControl(config));
    layout.append(visual,details);card.append(layout);return card;
  }
  _storage(snapshot) {
    const root=this._node("section",undefined,"stack");root.append(this._node("h2",this._t("Batteries électriques","Electrical batteries")));
    const grid=this._node("div",undefined,"cards");
    for(const b of snapshot.flow?.batteries||[]){const card=this._vessel(b);this._equipmentActions(card,b,"batteries");grid.append(card);}
    if(this._hass?.user?.is_admin)root.append(this._button(this._t("Ajouter une batterie","Add battery"),()=>this._settingsDialog("batteries")));
    if(!grid.childElementCount)grid.append(this._integrationLink(this._t("Associer des batteries électriques","Map electrical batteries")));
    root.append(grid);return root;
  }
  _subscribeWeather() {
    const entity=this._snapshotData?.weather_entity||null;
    if(this._weatherKey===entity)return;
    const generation=this._weatherGeneration=(this._weatherGeneration||0)+1;this._weatherUnsubscribe?.();this._weatherUnsubscribe=null;this._weatherKey=entity;this._forecast=null;
    if(!entity||!this._hass?.connection?.subscribeMessage)return;
    this._hass.connection.subscribeMessage(event=>{if(generation!==this._weatherGeneration)return;this._forecast=event?.forecast||null;for(const update of this._flowUpdates||[])update();},{type:"weather/subscribe_forecast",entity_id:entity,forecast_type:"daily"}).then(unsubscribe=>{if(generation!==this._weatherGeneration)unsubscribe();else this._weatherUnsubscribe=unsubscribe;}).catch(()=>{if(generation===this._weatherGeneration)this._forecast=null;});
  }
  _weatherCard(snapshot) {
    const tile=this._node("section",undefined,"kpi weather-card");tile.style.setProperty("--tone","#90caf9");tile.append(this._icon("mdi:weather-partly-cloudy"),this._node("span",this._t("Météo du jour","Today's weather"),"kpi-label"));
    const value=this._node("div",undefined,"value"),detail=this._node("p",undefined,"note weather-detail"),kind=this._node("p",undefined,"note");tile.append(value,detail,kind);
    const labels={sunny:["Ensoleillé","Sunny"],"clear-night":["Ciel dégagé","Clear"],cloudy:["Nuageux","Cloudy"],partlycloudy:["Éclaircies","Partly cloudy"],rainy:["Pluvieux","Rainy"],pouring:["Fortes pluies","Pouring"],snowy:["Neige","Snowy"],"snowy-rainy":["Pluie et neige","Snow and rain"],fog:["Brouillard","Fog"],lightning:["Orage","Thunderstorm"],"lightning-rainy":["Orage et pluie","Thunderstorm and rain"],windy:["Venteux","Windy"],"windy-variant":["Venteux et nuageux","Windy and cloudy"],hail:["Grêle","Hail"],exceptional:["Conditions exceptionnelles","Exceptional conditions"]};
    this._flowUpdates.push(()=>{
      const state=this._hass?.states?.[snapshot.weather_entity],a=state?.attributes||{},zone=snapshot.time_zone||"UTC",today=localDayStart(new Date(),zone),forecast=this._forecast?.find(f=>Number.isFinite(Date.parse(f.datetime))&&localDayStart(new Date(f.datetime),zone)===today);
      if(!state||["unknown","unavailable"].includes(state.state)){value.textContent=this._t("Indisponible","Unavailable");value.classList.add("bad");detail.textContent=this._t("Associer la météo dans Configuration → Compteurs du jour et tarif","Map weather in Configuration → Daily counters and tariff");kind.textContent="";return;}
      value.classList.remove("bad");const condition=forecast?.condition||state.state,temperature=forecast?.temperature??a.temperature,low=forecast?.templow,unit=a.temperature_unit||this._hass?.config?.unit_system?.temperature||"°C";
      value.textContent=labels[condition]?this._t(...labels[condition]):condition;
      detail.textContent=(Number.isFinite(low)?displayNumber(low,this._hass?.language)+" / ":"")+(Number.isFinite(temperature)?displayNumber(temperature,this._hass?.language)+" "+unit:this._t("Température indisponible","Temperature unavailable"));
      if(Number.isFinite(forecast?.precipitation))detail.textContent+=this._t(" · Pluie : "," · Rain: ")+displayNumber(forecast.precipitation,this._hass?.language)+" "+(a.precipitation_unit||"mm");
      if(Number.isFinite(forecast?.precipitation_probability))detail.textContent+=" · "+percent(forecast.precipitation_probability,this._hass?.language)+" %";
      kind.textContent=forecast?this._t("Prévision du jour","Daily forecast"):this._t("Actuellement · prévision du jour indisponible","Current conditions · daily forecast unavailable");
    });
    return tile;
  }

  _today(snapshot) {
    const root=this._node("section",undefined,"card today");root.append(this._node("h2",this._t("Aujourd’hui","Today")),this._node("p",this._t("Compteurs journaliers associés · prix fixe estimatif, hors abonnement et revente. Charge/restitution toutes origines, aucun gain solaire déduit.","Mapped daily counters · estimated flat price excluding standing charges and export revenue. Charge/discharge includes all energy origins; no solar savings inferred."),"note"));
    const grid=this._node("div",undefined,"cards");
    for(const [key,fr,en,icon,color] of [["solar","J’ai produit","Produced","mdi:white-balance-sunny","#ffcc45"],["home","J’ai consommé","Consumed","mdi:home","#5bb8ff"],["charge","J’ai stocké","Charged","mdi:battery-charging","#42dca4"],["discharge","J’ai restitué","Discharged","mdi:battery-high","#58aeff"],["import","J’ai importé","Imported","mdi:transmission-tower","#ff6565"],["export","J’ai exporté","Exported","mdi:transmission-tower","#58aeff"]]) {
      const entity=snapshot.daily?.[key],tile=this._metricTile(this._t(fr,en),entity,icon,color);
      if(key!=="export")tile.append(this._cost(entity,"today"));else tile.append(this._node("p",this._t("Revente non valorisée","Export revenue not valued"),"note"));grid.append(tile);
    }
    for(const usage of snapshot.flow?.usages || []) if(["solar_router","water_heater"].includes(usage.kind) && usage.energy_period !== "session") {
      const tile=this._metricTile(usage.name,usage.energy,"mdi:water-boiler","#ffa000",()=>this._dayEnergy(usage));tile.append(this._usageCost(usage));grid.append(tile);
    }
    grid.append(this._weatherCard(snapshot));
    root.append(grid); if(this._hass?.user?.is_admin)root.append(this._button(this._t("Modifier les compteurs du jour et le tarif","Edit daily counters and tariff"),()=>this._settingsDialog("daily")));
    root.append(this._dailyRatios(snapshot));
    return root;
  }
  _overview(snapshot) {
    const root = this._node("div");
    if (!snapshot.flow) {
      const notice = this._node("div", undefined, "card warn");
      notice.setAttribute("role", "alert");
      notice.append(this._node("h2", this._t("Flux indisponible dans cette version chargée", "Flow unavailable in the loaded version")),
        this._node("p", this._t("Le serveur n’a pas fourni le flux. Vérifiez que tout le dossier ehome_ems a été remplacé, puis redémarrez Home Assistant et rechargez l’application.",
        "The server did not provide flow data. Check the complete ehome_ems folder was replaced, restart Home Assistant and reload the app.")));
      root.append(notice); return root;
    }
    const flow = snapshot.flow, entities = flow.entities || {};
    const primary = flow.batteries?.find(b => b.role === "active" && b.coupling === "ac");
    const kpis = this._node("section", undefined, "kpis"); kpis.setAttribute("aria-label", this._t("Mesures principales", "Main readings"));
    for (const args of [
      [this._t("Solaire", "Solar"), entities.solar_power, "mdi:white-balance-sunny", "#e9af22"],
      [this._t("Conso Maison", "Home consumption"), entities.home_power, "mdi:home", "#6eafff"],
      [this._t("Import réseau", "Grid import"), entities.grid_import, "mdi:transmission-tower", "#ff6565"],
      [this._t("Export réseau", "Grid export"), entities.grid_export, "mdi:transmission-tower", "#58aeff"],
      [(primary?.name || this._t("Batterie", "Battery")) + this._t(" · charge", " · charge"), primary?.charge_power, "mdi:battery-charging", "#28b482"],
      [this._t("État de charge", "State of charge"), primary?.soc, "mdi:battery-high", "#28b482"],
    ]) kpis.append(this._metricTile(...args));
    root.append(kpis);
    if(flow.home_calculated)root.append(this._homeDiagnostic(entities.home_power));
    const grid = this._node("div", undefined, "overview-grid");
    grid.append(this._flow(flow), this._strategy(flow));
    const secondary = this._node("section", undefined, "card secondary");
    secondary.append(this._node("h2", this._t("Usages et équipements", "Loads and equipment")));
    const loads = this._node("div", undefined, "load-grid");
    for (const usage of flow.usages || []) {
      const tile=this._metricTile(usage.name,usage.power,productIcon(usage),
        ["solar_router","water_heater"].includes(usage.kind)?"#e9a23d":usage.kind==="ev_charger"?"#ab78e2":"#6eafff");
      const energy=this._node("p",undefined,"overview-daily-energy"),cost=this._usageCost(usage);
      this._historyLink(energy,usage.energy);
      this._flowUpdates.push(()=>{
        const value=this._dayEnergy(usage);
        energy.textContent=value===null?this._t(usage.energy?"Énergie du jour indisponible":"Énergie du jour non associée",usage.energy?"Daily energy unavailable":"Daily energy not mapped"):
          displayNumber(value,this._hass.language)+this._t(" kWh aujourd’hui"," kWh today");
        energy.classList.toggle("bad",value===null);
      });
      tile.append(energy,cost);this._equipmentActions(tile,usage,usage.kind==="appliance"?"appliances":"usages");loads.append(tile);
    }
    if (!flow.usages?.length) loads.append(this._node("p", this._t("Ajoutez des usages dans la configuration de l’intégration.", "Add loads in integration configuration."), "note"));
    secondary.append(loads); grid.append(secondary);
    const quality = this._node("section", undefined, "card quality-panel");
    quality.append(this._node("h2", this._t("Qualité des données", "Data quality")),
      this._node("p", flow.home_calculated ? this._t("Conso Maison : tous les usages inclus, calcul EMS.", "Home boundary: EMS calculated total.") :
        this._t("Conso Maison : le capteur existant doit inclure le cumulus, la borne et tous les usages.", "Home boundary: source boundary. Check whether the water heater is included."), "note"),
      this._button(this._t("Vérifier les associations", "Check mappings"), () => { this._tab = 8; this._render(); }));
    const available = this._node("p", undefined, "note"); quality.append(available);
    this._flowUpdates.push(() => {
      const ids = Object.keys(snapshot.bindings || {});
      const missing = ids.filter(id => !this._hass?.states[id] || ["unknown", "unavailable"].includes(this._hass.states[id].state));
      available.textContent = this._t("Mesures indisponibles : ", "Unavailable readings: ") + (missing.length + (snapshot.missing_entities?.length || 0));
    });
    grid.append(quality); root.append(grid); return root;
  }
  _homeDiagnostic(entity) {
    const root=this._node("details",undefined,"card home-diagnostic"),summary=this._node("summary",this._t("Conso Maison · détail du calcul EMS","Home consumption · EMS balance details"));root.append(summary);
    const status=this._node("p"),rows=this._node("div"),note=this._node("p",this._t("Solaire + Réseau − Charge batterie + Décharge batterie. Cumulus, borne et tous les appareils restent inclus. Réseau = Import − Export ; les sous-compteurs ne modifient jamais ce total.","Solar + Grid − Battery charge + Battery discharge. Water heater, EV and all appliances remain included. Grid = Import − Export; submeters never change this total."),"note");root.append(status,note,rows);
    const names={grid_power:this._t("Réseau signé","Signed grid"),grid_import:this._t("Import","Import"),grid_export:this._t("Export","Export"),solar_power:this._t("Production solaire","Solar production"),charge_power:this._t("Charge batterie","Battery charge"),discharge_power:this._t("Décharge batterie","Battery discharge")};
    const reasons={valid:this._t("Valide","Valid"),unavailable:this._t("Source absente ou indisponible","Missing or unavailable source"),stale_source:this._t("Source périmée : vérifier son dernier rapport et le délai configuré","Stale source: check last report and configured timeout"),missing_source:this._t("Association manquante : vérifier réseau et batteries actives","Missing mapping: check grid and active batteries"),missing_grid_source:this._t("Sélectionnez un réseau signé ou les deux capteurs Import/Export","Select a signed grid sensor or both Import/Export sensors"),boundary_unconfirmed:this._t("Périmètre AC à confirmer dans Conso Maison","Confirm the AC boundary in Home consumption"),solar_configuration:this._t("Déclaration solaire incohérente avec les associations","Solar declaration disagrees with mappings"),storage_configuration:this._t("Déclaration stockage incohérente avec les batteries actives","Storage declaration disagrees with active batteries"),unsupported_topology:this._t("Batterie DC : ce bilan nécessite des puissances côté AC","DC battery: this balance requires AC-side powers"),negative_balance:this._t("Bilan négatif : vérifier signes, périmètre et synchronisation","Negative balance: check signs, boundary and timing"),unsupported_unit:this._t("Unité incompatible : W ou kW attendus","Unsupported unit: expected W or kW"),unexpected_direction:this._t("Signe inattendu sur une puissance non signée","Unexpected sign on an unsigned power"),invalid_value:this._t("Valeur non numérique ou invalide","Invalid or nonnumeric value"),duplicate_source:this._t("Une même source est comptée deux fois","A source is counted twice"),grid_configuration:this._t("Mode réseau invalide","Invalid grid mode")};
    let previousQuality;
    this._flowUpdates.push(()=>{
      const state=this._hass?.states?.[entity],a=state?.attributes||{},quality=a.data_quality||"unavailable";
      if(quality!==previousQuality&&quality!=="valid")root.open=true;previousQuality=quality;
      summary.textContent=this._t("Conso Maison · calcul EMS : ","Home consumption · EMS calculation: ")+(quality==="valid"?this._t("Valide","Valid"):this._t("Indisponible — ouvrir le diagnostic","Unavailable — open diagnostics"));
      status.textContent=(reasons[quality]||quality)+" · "+reading(this._hass?.states,entity,undefined,this._hass?.language).text;status.className=quality==="valid"?"good":"bad";if(a.source_age_warning&&a.freshness_policy!=="strict")summary.textContent+=this._t(" · rapports anciens"," · old reports");
      rows.replaceChildren();
      for(const input of a.balance_inputs||[]) {
        const row=this._node("div",undefined,"source-item"),name=this._node("span",(names[input.role]||input.role)+" · "+input.entity_id),value=this._node("span");
        value.textContent=(input.contribution_w===null?this._t("Indisponible","Unavailable"):(input.contribution_w>=0?"+":"")+displayNumber(input.contribution_w,this._hass?.language)+" W")+" · "+(reasons[input.quality]||input.quality)+(input.age_seconds===null?"":" · "+displayNumber(input.age_seconds,this._hass?.language)+" s");value.className=input.quality==="valid"?"good":input.quality==="stale_source"&&a.freshness_policy!=="strict"?"warning":"bad";row.append(name,value);rows.append(row);
      }
      if(a.source_age_warning && a.freshness_policy!=="strict")rows.append(this._node("p",this._t("Rapports anciens : bilan maintenu en observation. Vérifiez les sources signalées et leur rythme de publication.","Old reports: balance retained in observation. Check flagged sources and their reporting interval."),"note"));
      if(a.freshness_check_enabled===false)rows.append(this._node("p",this._t("Contrôle de fraîcheur désactivé explicitement : les âges restent visibles.","Freshness check explicitly disabled: source ages remain visible."),"note"));
    });
    if(this._hass?.user?.is_admin)root.append(this._button(this._t("Configurer Conso Maison","Configure Home consumption"),()=>this._settingsDialog("home")));
    return root;
  }
  _strategy(flow, expanded = false) {
    const automatic=(this._snapshotData?.energy_goals||[]).filter(goal=>goal.mode==="auto").length;
    const panel = this._node("section", undefined, "card strategy");
    panel.append(this._node("h2", this._t("Stratégie EMS", "EMS strategy")), this._node("span", automatic?this._t("Complément automatique autorisé","Automatic top-up permitted"):this._t("Observation", "Observation"), "observation"));
    panel.append(this._node("h3", this._t("Situation actuelle", "Current situation")));
    const interpretation=this._node("p",undefined,"situation-comment");interpretation.setAttribute("aria-live","polite");panel.append(interpretation);
    this._flowUpdates.push(()=>{
      const e=flow?.entities||{},power=id=>flowPower(this._hass?.states,id);
      const sum=items=>strictSum(items.map(power));
      const facts=situationFacts({solar:power(e.solar_power),home:power(e.home_power),imported:power(e.grid_import),exported:power(e.grid_export),
        charge:sum((flow?.batteries||[]).filter(b=>b.role==="active").map(b=>b.charge_power)),
        discharge:sum((flow?.batteries||[]).filter(b=>b.role==="active").map(b=>b.discharge_power)),
        water:sum([...new Set((flow?.usages||[]).filter(u=>["water_heater","solar_router"].includes(u.kind)).map(u=>u.power).filter(Boolean))])});
      const phrases={incomplete:["Certaines mesures sont indisponibles : la situation ne peut pas être interprétée complètement.","Some readings are unavailable: the situation cannot be fully interpreted."],import:["Le réseau complète actuellement les besoins de votre installation.","The grid is currently supplementing your installation’s needs."],surplus:["Vous produisez plus que la maison ne consomme.","You are producing more than your home consumes."],solar:["Votre production solaire contribue aux besoins de la maison.","Solar production is contributing to your home’s needs."],no_solar:["La production solaire est faible ou nulle actuellement.","Solar production is currently low or zero."],water:["Le cumulus ou le circuit de routage suivi consomme de l’énergie.","The monitored water heater or routing circuit is consuming energy."],charge:["La batterie est en charge et stocke de l’énergie.","The battery is charging and storing energy."],discharge:["La batterie fournit de l’énergie à l’installation.","The battery is supplying energy to the installation."],export:["Une partie de l’énergie est également injectée sur le réseau.","Some energy is also being exported to the grid."]};
      interpretation.textContent=facts.map(f=>this._t(...phrases[f])).join(" ");
    });
    panel.append(this._node("h3", this._t("Décisions et priorités", "Decisions and priorities")),
      this._node("p", automatic?this._t("Complément automatique activé pour ","Automatic top-up enabled for ")+automatic+this._t(" objectif(s)."," goal(s)."):
      this._t("Les objectifs en observation et les scénarios ne commandent aucun équipement.","Observation goals and scenarios do not command equipment."), "note"));
    if (expanded) panel.append(this._energyGoals(),this._simulation());
    else {
      panel.append(this._node("h3", this._t("Priorités de simulation", "Simulation priorities")));
      const active = (this._snapshotData?.simulation?.targets || []).filter(item => item.enabled);
      const list = this._node("ol");
      for (const item of active) list.append(this._node("li", item.name));
      if (active.length) panel.append(list);
      else panel.append(this._node("p", this._t("Aucun équipement inclus dans un scénario.", "No equipment included in a scenario."), "note"));
      panel.append(this._button(this._t("Ouvrir Stratégie", "Open Strategy"), () => { this._tab = 7; this._render(); }));
    }
    panel.append(this._node("p", automatic?this._t("Seuls les objectifs explicitement activés peuvent commander leur routeur.","Only explicitly enabled goals may control their router."):this._t("Aucune commande automatique", "No automatic commands"), "note")); return panel;
  }
  _energyGoals() {
    const root=this._node("section",undefined,"energy-goals"),snapshot=this._snapshotData;
    root.append(this._node("h2",this._t("Objectif d’énergie avant une échéance","Energy target by a deadline")),
      this._node("p",this._t("Le cycle va de l’échéance de la veille à celle du jour : le solaire reçu avant minuit compte pour le matin suivant. Le complément réseau est limité au créneau autorisé. Un objectif en kWh ne mesure pas la chaleur restante.","The cycle runs from yesterday’s deadline to today’s: solar received before midnight counts towards the following morning. Grid top-up stays within its allowed window. A kWh target is not remaining heat."),"note"));
    const stateBox=this._node("div",undefined,"goal-results");stateBox.setAttribute("aria-live","polite");
    const reasons={lease_too_short:["Fin du créneau : aucun nouveau forçage","Window ending: no new override"],target_reached:["Objectif atteint","Target reached"],solar_priority:["Priorité au solaire","Solar priority"],waiting_window:["En attente du créneau autorisé","Waiting for allowed window"],complement_due:["Complément nécessaire maintenant","Top-up needed now"],insufficient_window:["Créneau insuffisant pour atteindre l’objectif","Window too short to reach target"],energy_unavailable:["Énergie du cycle indisponible","Cycle energy unavailable"],baseline_missing:["Référence de début de cycle absente dans History/Recorder","Cycle-start baseline missing from History/Recorder"],history_unavailable:["History/Recorder indisponible","History/Recorder unavailable"],counter_reset:["Baisse du compteur détectée : vérifier la source ; complément suspendu","Counter decrease detected: check source; top-up suspended"],stale_energy:["Compteur d’énergie trop ancien : complément suspendu","Energy counter too old: top-up suspended"],stale_energy_idle_confirmed:["Compteur stable · puissance au repos confirmée","Stable counter · idle power confirmed"],manual_full_due:["Full · complément en cours","Full · goal top-up in progress"],manual_timed_override:["Forçage manuel temporisé · automatique en pause","Timed manual override · automatic paused"],manual_override:["Commande manuelle prioritaire : cycle suspendu","Manual override takes priority: cycle suspended"],command_unconfirmed:["Commande non confirmée : vérifier puis réarmer","Unconfirmed command: check and re-arm"],runtime_unavailable:["Suivi interrompu : vérifier puis réarmer si nécessaire","Monitoring interrupted: check and re-arm if needed"],router_requires_full_opening:["Configurer la marche forcée du F1ATB à 100 %","Set F1ATB forced opening to 100%"],router_unavailable:["Routeur indisponible","Router unavailable"],router_already_managed:["Action déjà gérée par un autre objectif","Action already managed by another goal"],configuration_changed:["Configuration modifiée : rechargement nécessaire","Configuration changed: reload required"]};
    const draw=values=>{stateBox.replaceChildren();for(const goal of values||[]){const card=this._node("div",undefined,"card"),label=reasons[goal.reason]||[goal.reason,goal.reason];card.append(this._node("h3",goal.name),this._node("p",(goal.mode==="auto"?this._t("Automatique","Automatic"):this._t("Observation","Observation"))+" · "+this._t(...label)));
      if(goal.goal_kwh!==undefined)card.append(this._node("p",this._t("Objectif : ","Target: ")+displayNumber(goal.goal_kwh,this._hass?.language)+" kWh · "+this._t("Reçu sur le cycle : ","Received this cycle: ")+(goal.consumed_kwh==null?this._t("Indisponible","Unavailable"):displayNumber(goal.consumed_kwh,this._hass?.language)+" kWh")));
      if(goal.weather_stage)card.append(this._node("p",this._t("Complément météo HC · objectif intermédiaire : ","Weather off-peak top-up · intermediate target: ")+displayNumber(goal.goal_kwh,this._hass?.language)+" kWh / "+displayNumber(goal.cycle_goal_kwh,this._hass?.language)+" kWh","note"));
      if(goal.manual_full)card.append(this._node("p",this._t("Mode Full : chauffe pilotée jusqu’à l’objectif du cycle ou à 07h.","Full mode: controlled heating until the cycle target or 07:00."),"note"));
      if(goal.missing_kwh!=null)card.append(this._node("p",this._t("À compléter : ","Top-up needed: ")+displayNumber(goal.missing_kwh,this._hass?.language)+" kWh · "+this._t("Chauffe estimée : ","Estimated heating: ")+goal.needed_minutes+" min"));
      const day=this._node("p",this._t("Énergie consommée aujourd’hui (depuis minuit) : ","Energy consumed today (since midnight): ")+(goal.day_energy_kwh===null||goal.day_energy_kwh===undefined?this._t("Indisponible","Unavailable"):displayNumber(goal.day_energy_kwh,this._hass.language)+" kWh"),"note");this._historyLink(day,goal.energy_entity);card.append(day);
      card.append(this._node("p",this._t("Cycle : ","Cycle: ")+(goal.cycle_start?new Date(goal.cycle_start).toLocaleString(this._hass.language,{timeZone:snapshot.time_zone}):"—")+this._t(" → échéance ci-dessous"," → deadline below"),"note"));
      if(goal.warning==="stale_energy_idle_confirmed")card.append(this._node("p",this._t("Compteur d’énergie stable, puissance du cumulus récemment confirmée à l’arrêt : seul un forçage bref est autorisé, puis nouvelle vérification du compteur.","Energy counter stable, heater power freshly confirmed idle: only a short initial lease is permitted before meter recheck."),"note"));
      if(goal.warning==="stale_energy")card.append(this._node("p",this._t("Dernier rapport du compteur ancien. Une valeur stable peut être normale hors chauffe ; aucun nouveau complément ne sera lancé sans rapport récent.","The last meter report is old. A stable value can be normal while idle; no new top-up starts without a recent report."),"note warn"));
      if(goal.reason==="target_reached")card.append(this._node("p",this._t("Objectif atteint — aucun complément nécessaire","Target reached — no top-up needed"),"good"));
      for(const [key,fr,en] of [["deadline","Échéance : ","Deadline: "],["latest_start","Début estimé du complément : ","Estimated top-up start: "]])if(goal[key]&&(key!=="latest_start"||goal.missing_kwh>0))card.append(this._node("p",this._t(fr,en)+new Date(goal[key]).toLocaleString(this._hass?.language||"fr",{timeZone:snapshot.time_zone}),"note"));
      card.append(this._node("p",goal.running?this._t("Complément EMS en cours · forçage temporisé","EMS top-up running · timed override"):this._t("Aucun forçage détenu par EMS","No override owned by EMS"),"note"));
      const router=snapshot.flow?.usages?.find(u=>u.id===(goal.router_usage||snapshot.settings?.energy_goals?.[goal.id]?.router_usage));
      if(this._hass?.user?.is_admin&&router?.router_connection==="http"&&router.router_http_enabled){
        const message=this._node("p",undefined,"note");message.setAttribute("role","status");
        const durations=this._node("select");durations.setAttribute("aria-label",this._t("Durée du forçage manuel","Manual override duration"));
        for(const [minutes,label] of [[30,"30 min"],[60,"1 h"],["full","Full · objectif du cycle"]]){const option=this._node("option",label);option.value=String(minutes);durations.append(option);}
        durations.value="60";
        const boost=this._button(this._t("Forcer à 100 %","Override at 100%"),async()=>{
          boost.disabled=true;
          try{
            const full=durations.value==="full",minutes=Number(durations.value);
            if(full){
              await this._hass.callWS({type:"ehome_ems/full_energy_goal",entry_id:this._panel.config.entry_id,identifier:goal.id,revision:snapshot.revision});
              message.textContent=this._t("Full accepté : suivi jusqu’à l’objectif du cycle, sous réserve des sécurités du compteur et du routeur.","Full accepted: tracked to the cycle target, subject to meter and router safety checks.");
            }else{
              const result=await this._hass.callWS({type:"ehome_ems/router_command",entry_id:this._panel.config.entry_id,identifier:router.id,revision:snapshot.revision,action:"boost_duration",values:{config_token:router.router_native.config_token,minutes}});
              message.textContent=result.confirmed_by_router?this._t("Forçage confirmé : ","Override confirmed: ")+minutes+" min":this._t("Envoi non confirmé : vérifier le routeur avant de réessayer.","Send unconfirmed: check router before retrying.");
            }
          }catch(error){message.textContent=this._t("Forçage refusé : ","Override rejected: ")+(error.code||"");}
          finally{boost.disabled=false;}
        });
        boost.disabled=!router.router_native?.available||!router.router_native?.config_token;
        card.append(durations,boost,message);
      }
      if(this._hass?.user?.is_admin&&["manual_override","command_unconfirmed","runtime_unavailable"].includes(goal.reason))card.append(this._button(this._t("Réarmer après vérification","Re-arm after checking"),async()=>{try{await this._hass.callWS({type:"ehome_ems/rearm_energy_goal",entry_id:this._panel.config.entry_id,identifier:goal.id,revision:snapshot.revision});await refresh();}catch{this._message.textContent=this._t("Réarmement refusé. Actualisez.","Re-arm rejected. Refresh.");}}));stateBox.append(card);}};
    draw(snapshot.energy_goals||[]);root.append(stateBox);
    let loading=false,last=Date.now();const refresh=async()=>{if(loading)return;loading=true;try{const values=await this._hass.callWS({type:"ehome_ems/energy_goals",entry_id:this._panel.config.entry_id});snapshot.energy_goals=values;draw(values);}catch{stateBox.textContent=this._t("Suivi des objectifs indisponible.","Goal monitoring unavailable.");}finally{loading=false;last=Date.now();}};
    root.append(this._button(this._t("Actualiser les objectifs","Refresh goals"),refresh));this._flowUpdates.push(()=>{if(Date.now()-last>=30000)refresh();});
    if(!this._hass?.user?.is_admin)return root;
    const usages=snapshot.settings?.usages||{},goals=snapshot.settings?.energy_goals||{},routers=Object.entries(usages).filter(([,u])=>u.kind==="solar_router"&&u.router_type==="f1atb"&&u.router_connection==="http"&&u.router_http_enabled);
    for(const [id,usage] of Object.entries(usages).filter(([,u])=>["water_heater","solar_router"].includes(u.kind))){
      const existing=goals[id],details=this._node("details",undefined,"router-settings goal-editor");details.append(this._node("summary",this._t("Configurer l’objectif · ","Configure goal · ")+usage.name));
      const form=this._node("form",undefined,"settings-form"),controls={};form.addEventListener("submit",e=>e.preventDefault());
      const add=(key,fr,en,type,value,options)=>{const row=this._node("label",this._t(fr,en)),input=this._node(options?"select":"input");if(options){for(const [v,text] of options){const o=this._node("option",text);o.value=v;input.append(o);}}else input.type=type;input.setAttribute("aria-label",this._t(fr,en)+" · "+usage.name);input.value=existing?.[key]??value;if(type==="checkbox")input.checked=!!existing?.[key];controls[key]=input;row.append(input);form.append(row);return input;};
      add("mode","Mode de l’objectif","Goal mode","text","observe",[["observe",this._t("Observation · aucune commande","Observation · no commands")],["auto",this._t("Complément automatique autorisé","Automatic top-up permitted")]]);
      for(const [key,fr,en,value,min,max,step] of [["goal_kwh","Objectif du cycle (kWh)","Cycle target (kWh)",usage.daily_energy_goal_kwh||3,.01,100,.01],["nominal_power_w","Puissance de chauffe à pleine ouverture (W)","Heating power at full opening (W)",1800,100,15000,1],["margin_minutes","Marge de démarrage (minutes)","Start margin (minutes)",5,0,120,1],["max_age_seconds","Ancienneté maximale du compteur (secondes)","Maximum counter age (seconds)",300,30,3600,1]]){const i=add(key,fr,en,"number",value);Object.assign(i,{min,max,step,required:true});}
      for(const [key,fr,en,value] of [["deadline","Eau prête à","Water ready by","07:00"],["window_start","Début du complément autorisé","Allowed top-up starts","01:00"],["window_end","Fin du complément autorisé","Allowed top-up ends","07:00"]]){const i=add(key,fr,en,"time",value);i.required=true;}
      const energyOptions=[["",this._t("Choisir le compteur du cumulus","Choose water-heater counter")],...Object.entries(this._hass.states||{}).filter(([entity,state])=>entity.startsWith("sensor.")&&["Wh","kWh"].includes(state.attributes?.unit_of_measurement)).map(([entity,state])=>[entity,(state.attributes?.friendly_name||entity)+" · "+entity])];
      const e=add("energy_entity","Compteur cumulé dédié au cumulus","Dedicated cumulative water-heater counter","text",usage.energy_period==="total"?snapshot.bindings?.[usage.energy]?.source||usage.energy||"":"");e.required=true;this._entityPicker(e.parentElement,e,energyOptions.filter(([id])=>id),()=>usage.name);
      add("counter_confirmed","Je confirme que ce compteur est cumulatif et ne se remet pas à zéro à minuit","I confirm this is a lifetime counter with no midnight reset","checkbox",false);
      const heaterPower=add("power_entity","Puissance réelle du cumulus (sécurité compteur stable)","Actual heater power (stable meter safety)","text",usage.power||"");
      this._entityPicker(heaterPower.parentElement,heaterPower,Object.entries(this._hass?.states||{}).filter(([id,state])=>id.startsWith("sensor.")&&["W","kW"].includes(state.attributes?.unit_of_measurement)).map(([id,state])=>[id,(state.attributes?.friendly_name||id)+" · "+id]),()=>usage.name);
      add("weather_enabled","Activer le complément météo en heures creuses","Enable weather-triggered off-peak top-up","checkbox",false);
      const weatherOptions=[["",this._t("Choisir une entité météo","Choose weather entity")],...Object.entries(this._hass?.states||{}).filter(([id])=>id.startsWith("weather.")).map(([id,state])=>[id,(state.attributes?.friendly_name||id)+" · "+id])];
      add("weather_entity","Entité de prévision météo","Weather forecast entity","text","",weatherOptions);
      for(const [key,fr,en,value] of [["weather_window_start","Début du créneau météo HC","Weather off-peak window starts","12:30"],["weather_window_end","Fin du créneau météo HC","Weather off-peak window ends","14:30"]])add(key,fr,en,"time",value);
      const fraction=add("weather_fraction","Fraction minimale de l’objectif en cas de mauvais temps (0,5 = 50 %)","Minimum target fraction on poor weather (0.5 = 50%)","number",0.5);Object.assign(fraction,{min:"0.01",max:"1",step:"0.05"});
      form.append(this._node("p",this._t("Sur prévision horaire de pluie ou ciel couvert, viser la fraction choisie pendant ce créneau. Le complément nocturne vise toujours l’objectif total. Sans prévision exploitable, aucun complément météo.","On hourly forecast of rain or overcast skies, target the selected fraction during this window. Night top-up still targets the full cycle. No forecast means no weather-triggered heating."),"note"));

      add("router_usage","Routeur F1ATB HTTP à commander","F1ATB HTTP router to control","text",routers.length===1?routers[0][0]:"",[["",this._t("Non associé · observation seulement","Not mapped · observation only")],...routers.map(([key,u])=>[key,u.name])]);
      form.append(this._node("p",this._t("L’activation du mode automatique autorise de vrais compléments réseau dans ce créneau. Choisir le compteur du seul cumulus. L’ouverture de marche forcée F1ATB doit être à 100 %. Une seule échéance par cycle ; le thermostat et les protections restent ceux du cumulus.","Enabling automatic mode permits real grid top-ups within this window. Choose the water-heater-only counter. F1ATB forced opening must be 100%. One deadline per cycle; thermostat and protections remain with the water heater."),"note"));
      const feedback=this._node("p",undefined,"note");feedback.setAttribute("role","status");
      const save=this._button(this._t("Enregistrer l’objectif","Save goal"),async()=>{if(!form.reportValidity())return;const values={};for(const [key,input] of Object.entries(controls))values[key]=input.type==="checkbox"?input.checked:input.type==="number"?Number(input.value):input.value;save.disabled=true;try{await this._hass.callWS({type:"ehome_ems/save_energy_goal",entry_id:this._panel.config.entry_id,identifier:id,revision:snapshot.revision,values});this._settingsRetries=5;await this._load();}catch(error){feedback.textContent=this._t("Objectif refusé : ","Goal rejected: ")+(error.code||"");}finally{save.disabled=false;}});
      const modeLabel=()=>{save.textContent=controls.mode.value==="auto"?this._t("Activer et enregistrer le complément automatique","Enable and save automatic top-up"):this._t("Enregistrer l’objectif en observation","Save observation goal");};controls.mode.addEventListener("change",modeLabel);modeLabel();form.append(save);
      if(existing)form.append(this._button(this._t("Retirer cet objectif","Remove this goal"),async()=>{try{await this._hass.callWS({type:"ehome_ems/save_energy_goal",entry_id:this._panel.config.entry_id,identifier:id,revision:snapshot.revision,values:{},remove:true});this._settingsRetries=5;await this._load();}catch(error){feedback.textContent=error.code||"Erreur";}}));
      details.append(form,feedback);root.append(details);
    }
    return root;
  }
  _simulationResult(result) {
    const root = this._node("div", undefined, "scenario-result");
    root.append(this._node("strong", this._t("Scénario hypothétique · aucune commande", "Hypothetical scenario · no commands")),
      this._node("p", this._t("Budget : ", "Budget: ") + result.budget_w + " W · " + this._t("Alloué : ", "Allocated: ") + result.allocated_w + " W · " + this._t("Non alloué : ", "Unallocated: ") + result.remaining_w + " W"));
    const reasons = {
      disabled: this._t("Exclu du scénario", "Excluded from scenario"),
      budget_exhausted: this._t("Budget épuisé par les priorités précédentes", "Budget exhausted by earlier priorities"),
      below_minimum: this._t("Budget restant inférieur au minimum déclaré", "Remaining budget below declared minimum"),
      ceiling_reached: this._t("Plafond déclaré atteint", "Declared ceiling reached"),
      allocated: this._t("Allocation dans les limites déclarées", "Allocation within declared limits"),
    };
    for (const item of result.targets || []) {
      const row = this._node("div", undefined, "row");
      row.append(this._node("span", item.name), this._node("span", item.allocated_w + " W", "value"),
        this._node("span", reasons[item.reason] || item.reason, "note"),
        this._node("span", this._t("Minimum : ", "Minimum: ") + item.min_w + " W · " + this._t("Plafond : ", "Ceiling: ") + item.max_w + " W", "note")); root.append(row);
    }
    return root;
  }
  _simulation() {
    const root = this._node("section", undefined, "simulation");
    root.append(this._node("h2", this._t("Priorités et simulation manuelle", "Priorities and manual simulation")),
      this._node("p", this._t("Répartissez un budget hypothétique selon des limites que vous déclarez. Ce budget n’est pas déduit de l’injection réseau. Les plafonds ne constituent pas des capacités matérielles vérifiées.",
        "Allocate a hypothetical budget using limits you declare. This budget is not inferred from grid export. Ceilings are not verified hardware capabilities."), "note"),
      this._node("p", this._t("Cette simulation ne tient pas encore compte du SOC, des échéances, des pertes, des régulations natives ou de la fraîcheur des mesures. Ce n’est pas une consigne à appliquer au matériel.",
        "This simulation does not yet account for SOC, deadlines, losses, native regulation or reading freshness. It is not a setpoint to apply to hardware."), "note"),
      this._node("p", this._t("Les allocations ne s’ajoutent pas aux consommations en cours. Aucune puissance mesurée n’est automatiquement ajoutée ou retranchée au budget saisi.",
        "Allocations do not add to current consumption. No measured power is automatically added to or subtracted from the entered budget."), "note"));
    const snapshot = this._snapshotData;
    const targets = structuredClone(snapshot.simulation?.targets || []);
    if (!targets.length) {
      root.append(this._node("p", this._t("Ajoutez un usage ou une batterie active AC dans Configuration pour préparer un scénario. Les batteries de secours et DC sont exclues de cette première simulation.",
        "Add a load or an active AC battery in Configuration to prepare a scenario. Backup and DC batteries are excluded from this first simulation."), "note")); return root;
    }
    let dirty = false, run;
    const status = this._node("p", "", "note"); status.setAttribute("role", "status");
    const editor = this._node("div", undefined, "simulation-editor");
    const markDirty = () => { dirty = true; if (run) run.disabled = true; status.textContent = this._t("Paramètres modifiés : enregistrez avant de simuler.", "Settings changed: save before simulating."); };
    const editable = !!this._hass?.user?.is_admin;
    const draw = () => {
      editor.replaceChildren();
      targets.forEach((target, index) => {
        const row = this._node("div", undefined, "simulation-row");
        const name = this._node("label", undefined, "simulation-target");
        const enabled = this._node("input"); enabled.type = "checkbox"; enabled.checked = target.enabled; enabled.disabled = !editable;
        enabled.setAttribute("aria-label", this._t("Inclure ", "Include ") + target.name);
        enabled.addEventListener("change", () => { target.enabled = enabled.checked; markDirty(); });
        name.append(enabled, this._node("strong", ` ${index + 1}. ${target.name}`)); row.append(name);
        for (const [key, title] of [["min_w", this._t("Minimum (W)", "Minimum (W)")], ["max_w", this._t("Plafond (W)", "Ceiling (W)")]]) {
          const label = this._node("label", title), input = this._node("input");
          input.type = "number"; input.min = 0; input.max = 1000000; input.step = 1; input.required = true;
          input.value = target[key]; input.disabled = !editable;
          input.setAttribute("aria-label", title + " · " + target.name);
          input.addEventListener("input", () => { target[key] = Number(input.value); markDirty(); }); label.append(input); row.append(label);
        }
        if (editable) {
          const moves = this._node("div", undefined, "move-buttons");
          for (const [delta, title] of [[-1, this._t("Monter", "Move up")], [1, this._t("Descendre", "Move down")]]) {
            const button = this._button(title, () => { [targets[index], targets[index + delta]] = [targets[index + delta], targets[index]]; markDirty(); draw(); });
            button.disabled = index + delta < 0 || index + delta >= targets.length;
            button.setAttribute("aria-label", title + " · " + target.name); moves.append(button);
          }
          row.append(moves);
        }
        editor.append(row);
      });
    };
    draw(); root.append(editor, status);
    if (editable) {
      const save = this._button(this._t("Enregistrer les priorités de simulation", "Save simulation priorities"), async () => {
        if (![...editor.querySelectorAll("input[type=number]")].every(input => input.reportValidity())) return;
        save.disabled = true; editor.inert = true; if (run) run.disabled = true;
        try {
          await this._hass.callWS({type:"ehome_ems/save_simulation", entry_id:this._panel.config.entry_id, revision:snapshot.revision,
            targets:targets.map(({id, enabled, min_w, max_w}) => ({id, enabled, min_w, max_w}))});
          await this._load(); this._message.textContent = this._t("Priorités de simulation enregistrées. Aucun équipement modifié.", "Simulation priorities saved. No equipment changed.");
        } catch (error) {
          status.textContent = error.code === "conflict" || error.code === "targets_changed" ? this._t("La configuration a changé. Actualisez avant de réessayer.", "Configuration changed. Refresh before retrying.") :
            this._t("Paramètres refusés : minimum ≤ plafond, plafond positif pour un équipement inclus, valeurs entières entre 0 et 1 000 000 W.", "Settings rejected: minimum ≤ ceiling, positive ceiling for included equipment, integer values from 0 to 1,000,000 W.");
        } finally { editor.inert = false; save.disabled = false; if (run) run.disabled = dirty; }
      }); root.append(save);
    }
    const budgetLabel = this._node("label", this._t("Budget hypothétique à répartir (W)", "Hypothetical budget to allocate (W)"), "scenario-budget");
    const budget = this._node("input"); budget.type = "number"; budget.min = 0; budget.max = 1000000; budget.step = 1; budget.required = true;
    budget.placeholder = this._t("Exemple : 1500", "Example: 1500"); budget.setAttribute("aria-label", budgetLabel.textContent); budgetLabel.append(budget); root.append(budgetLabel);
    const resultBox = this._node("div"); resultBox.setAttribute("aria-live", "polite");
    const history = this._node("div", undefined, "scenario-history");
    const drawHistory = () => {
      history.replaceChildren(this._node("h3", this._t("Journal des scénarios manuels", "Manual scenario journal")),
        this._node("p", this._t("20 résultats maximum en mémoire, perdus au redémarrage de Home Assistant. Ce journal contient des simulations, pas des décisions exécutées.",
          "Up to 20 results in memory, lost when Home Assistant restarts. This journal contains simulations, not executed decisions."), "note"));
      for (const result of [...(this._snapshotData.simulation_history || [])].reverse()) {
        const item = this._node("details"); item.append(this._node("summary", new Date(result.created_at).toLocaleString(this._hass?.language || "fr", {timeZone:this._hass?.config?.time_zone}) + " · " + result.budget_w + " W"), this._simulationResult(result)); history.append(item);
      }
    };
    drawHistory();
    run = this._button(this._t("Simuler ce budget", "Simulate this budget"), async () => {
      if (dirty || !budget.reportValidity()) return;
      run.disabled = true;
      try {
        const result = await this._hass.callWS({type:"ehome_ems/simulate", entry_id:this._panel.config.entry_id, revision:this._snapshotData.revision, budget_w:Number(budget.value)});
        resultBox.replaceChildren(this._simulationResult(result));
        this._snapshotData.simulation_history = [...(this._snapshotData.simulation_history || []), result].slice(-20); drawHistory();
        status.textContent = this._t("Scénario calculé, aucune commande envoyée.", "Scenario calculated, no commands sent.");
      } catch (error) { status.textContent = error.code === "conflict" ? this._t("La configuration a changé. Actualisez avant de simuler.", "Configuration changed. Refresh before simulating.") : this._t("Simulation impossible. Vérifiez le budget et les paramètres enregistrés.", "Simulation failed. Check the budget and saved settings."); }
      finally { run.disabled = dirty; }
    });
    root.append(run, resultBox, history); return root;
  }
  _dailyRatios(snapshot) {
    const root=this._node("section",undefined,"daily-ratios"),grid=this._node("div",undefined,"ratios");
    const entries=[["autonomy",this._t("Autonomie apparente","Apparent self-sufficiency")],["selfConsumption",this._t("Autoconso apparente","Apparent self-consumption")]];
    const displays=entries.map(([key,label])=>{const card=this._node("div",undefined,"kpi");card.append(this._node("span",label,"kpi-label"));const value=this._node("div",undefined,"ratio-value");card.append(value);grid.append(card);return{key,value};});
    const exchange=this._node("div",undefined,"card exchanges");exchange.append(this._node("h3",this._t("Part Import / Export dans les échanges réseau","Import / Export share of grid exchanges")));
    const values=this._node("p"),importValue=this._node("span"),exportValue=this._node("span"),bar=this._node("div",undefined,"exchange-bar"),left=this._node("span"),right=this._node("span");bar.append(left,right);values.append(importValue," / ",exportValue);this._historyLink(importValue,snapshot.daily?.import);this._historyLink(exportValue,snapshot.daily?.export);exchange.append(values,bar);
    this._flowUpdates.push(()=>{
      const imported=this._energy(snapshot.daily?.import),exported=this._energy(snapshot.daily?.export);
      const ratios=dailyIndicators({home:this._energy(snapshot.daily?.home),solar:this._energy(snapshot.daily?.solar),imported,exported});
      for(const {key,value} of displays){value.textContent=ratios[key]===null?this._t("Indisponible","Unavailable"):percent(ratios[key],this._hass?.language)+" %";value.classList.toggle("bad",ratios[key]===null);}
      importValue.textContent=`Import : ${imported===null?this._t("Indisponible","Unavailable"):displayNumber(imported,this._hass?.language)+" kWh"}${ratios.importShare===null?"":` · ${percent(ratios.importShare,this._hass?.language)} %`}`;
      exportValue.textContent=`Export : ${exported===null?this._t("Indisponible","Unavailable"):displayNumber(exported,this._hass?.language)+" kWh"}${ratios.exportShare===null?"":` · ${percent(ratios.exportShare,this._hass?.language)} %`}`;
      left.style.width=(ratios.importShare||0)+"%";right.style.width=(ratios.exportShare||0)+"%";
      bar.hidden=ratios.importShare===null;
    });
    root.append(grid,exchange,this._node("p",this._t("Indicateurs apparents : autonomie = (maison − import) / maison ; autoconso = (solaire − export) / solaire. Le stockage, une charge réseau ou un export batterie peuvent les biaiser. Ils supposent des compteurs du même jour et un périmètre maison complet. Valeur incohérente ou dénominateur nul : indisponible.","Apparent indicators: self-sufficiency = (home − import) / home; self-consumption = (solar − export) / solar. Storage, grid charging and battery exports can bias them. Counters must cover the same day and the full home boundary. Inconsistent readings or zero denominator: unavailable."),"note"));return root;
  }
  _charger(config) {
    const root=this._node("section",undefined,"card charger-card");root.append(this._node("h2",config.name));
    const layout=this._node("div",undefined,"vessel-layout"),visual=this._node("div",undefined,"charger-icon");visual.append(this._icon("mdi:ev-station"));
    const details=this._node("div"),power=this._node("div",undefined,"vessel-main"),energy=this._node("div",undefined,"energy-value"),status=this._node("p",undefined,"note");
    this._bind(power,config.power);this._editable(power,config.power);
    status.append(this._manualControl(config));
    const mode=this._node("p",undefined,"note");this._flowUpdates.push(()=>{const watts=flowPower(this._hass?.states,config.power);mode.textContent=watts===null?this._t("Puissance indisponible","Power unavailable"):watts>=10?this._t("Puissance mesurée ≥ 10 W","Measured power ≥ 10 W"):((config.ev_session?.active?config.ev_session:config.ev_session?.last_session)?.peak_w!=null?this._t("Veille · ","Idle · ")+displayNumber((config.ev_session.active?config.ev_session:config.ev_session.last_session).peak_w,this._hass?.language)+" W max":this._t("Veille / faible puissance","Idle / low power"));});
    details.append(power,mode,this._usageEnergy(config),this._usageCost(config),status);
    layout.append(visual,details);root.append(layout);return root;
  }
  _equipmentActions(parent,equipment,section) {
    if(!this._hass?.user?.is_admin||!equipment.id)return;
    const name=parent.querySelector("h2,h3,.kpi-label,.flow-title");if(!name||name.dataset.equipmentName)return;
    name.dataset.equipmentName=equipment.id;name.classList.add("equipment-name");name.tabIndex=0;name.setAttribute("aria-haspopup","dialog");
    name.title=this._t("Appui prolongé, clic droit ou Entrée : modifier ou retirer","Hold, right-click or Enter: edit or remove");
    const open=()=>this._equipmentMenu(equipment,section);let timer,x,y;
    const cancel=()=>clearTimeout(timer);this._holdCancels.push(cancel);
    name.addEventListener("pointerdown",event=>{event.stopPropagation();if(event.button!==0)return;x=event.clientX;y=event.clientY;timer=setTimeout(open,600);});
    name.addEventListener("pointermove",event=>{if(Math.abs(event.clientX-x)+Math.abs(event.clientY-y)>10)cancel();});
    for(const type of ["pointerup","pointercancel","pointerleave"])name.addEventListener(type,cancel);
    name.addEventListener("contextmenu",event=>{event.preventDefault();event.stopPropagation();cancel();open();});
    name.addEventListener("keydown",event=>{if(["Enter"," "].includes(event.key)){event.preventDefault();event.stopPropagation();open();}});
  }
  _equipmentMenu(equipment,section) {
    if(!this._hass?.user?.is_admin||this._dialog?.open)return;
    const dialog=this._node("dialog");this._dialog=dialog;dialog.setAttribute("aria-label",this._t("Actions · ","Actions · ")+equipment.name);
    const close=()=>{dialog.close();dialog.remove();if(this._dialog===dialog)this._dialog=null;};
    const action=remove=>{close();this._settingsDialog(section,equipment.id,remove);};
    const edit=this._button(this._t("Modifier","Edit"),()=>action(false)),remove=this._button(this._t("Retirer du suivi","Remove monitoring"),()=>action(true));
    edit.setAttribute("aria-label",this._t("Modifier ","Edit ")+equipment.name);remove.setAttribute("aria-label",this._t("Retirer ","Remove ")+equipment.name);
    dialog.append(this._node("h2",equipment.name),edit,remove,this._button(this._t("Annuler","Cancel"),close));
    dialog.addEventListener("close",()=>{dialog.remove();if(this._dialog===dialog)this._dialog=null;});this.shadowRoot.append(dialog);dialog.showModal();edit.focus();
  }
  _settingsShortcuts(snapshot) {
    const root=this._node("div",undefined,"settings-shortcuts");
    const primary=this._node("div",undefined,"settings-primary");
    for(const [section,fr,en] of [["grid","Réseau","Grid"],["solar","Solaire","Solar"],["home","Conso Maison","Home consumption"],["daily","Compteurs du jour et tarif","Daily counters and tariff"]])primary.append(this._button(this._t(fr,en),()=>this._settingsDialog(section)));root.append(primary);
    for(const [section,fr,en] of [["photovoltaic","Ajouter un équipement photovoltaïque","Add PV equipment"],["batteries","Ajouter une batterie","Add battery"],["usages","Ajouter un usage","Add load"],["appliances","Ajouter un appareil","Add appliance"]])root.append(this._button(this._t(fr,en),()=>this._settingsDialog(section)));

    return root;
  }
  _settingsDialog(section,identifier=null,remove=false) {
    if(!this._hass?.user?.is_admin || this._dialog?.open)return;
    const settings=this._snapshotData?.settings || {},collection=section==="batteries"?"batteries":section==="photovoltaic"?"photovoltaic":"usages";
    const equipment=["batteries","usages","appliances","photovoltaic"].includes(section);
    const current=equipment?settings[collection]?.[identifier]||{}:section==="daily"?{...settings.daily,tariff_eur_kwh:settings.tariff_eur_kwh,weather_entity:settings.weather_entity}:settings;
    const dialog=this._node("dialog");this._dialog=dialog;
    const names={photovoltaic:this._t("Équipement photovoltaïque","PV equipment"),grid:this._t("Réseau","Grid"),solar:this._t("Solaire","Solar"),home:this._t("Conso Maison","Home consumption"),daily:this._t("Compteurs du jour et tarif","Daily counters and tariff"),batteries:this._t("Batterie","Battery"),usages:this._t("Usage","Load"),appliances:this._t("Appareil","Appliance")};
    const title=this._node("h2",remove?this._t("Retirer du suivi","Remove monitoring"):names[section]);title.id="settings-title";dialog.setAttribute("aria-labelledby",title.id);dialog.append(title);
    const form=this._node("form",undefined,"settings-form"),controls={};
    const add=(key,fr,en,type="text",options=null,units=null,initial=current[key])=>{
      const label=this._node("label",this._t(fr,en));let input;
      if(type==="select") {input=this._node("select");for(const [value,text] of options){const option=this._node("option",text);option.value=value;option.selected=value===(initial??"");input.append(option);}}
      else {input=this._node("input");input.type=type;if(type==="checkbox")input.checked=!!initial;else input.value=initial??"";}
      input.name=key;input.setAttribute("aria-label",this._t(fr,en));
      if(type==="number"){input.step=key==="home_max_age_seconds"?"1":"any";input.min="0";}
      if(key==="name"){input.required=true;input.maxLength=80;}
      if(units){const list=this._node("datalist");list.id="sources-"+key;input.autocomplete="off";
        for(const [id,state] of Object.entries(this._hass?.states||{}))if((key==="status"?["sensor","binary_sensor","switch","select"].includes(id.split(".")[0]):id.startsWith("sensor.")||(section==="usages"&&key==="temperature"&&id.startsWith("input_number."))) && (!units.length||units.includes(state.attributes?.unit_of_measurement)) && !this._snapshotData?.bindings?.[id]){
          const option=this._node("option");option.value=id;option.label=state.attributes?.friendly_name||id;list.append(option);
        }label.append(list);}
      label.append(input);if(units)this._entityPicker(label,input,[...label.querySelectorAll("datalist option")].map(o=>[o.value,o.label]));form.append(label);controls[key]=input;return input;
    };
    const source=(key,fr,en,units=["W","kW"])=>add(key,fr,en,"text",null,units);
    if(remove)dialog.append(this._node("p",this._t("Retirer uniquement l’association EMS de ","Remove only the EMS mapping of ")+(current.name||"")+this._t(" ? Aucun appareil ni capteur source ne sera supprimé.","? No device or source sensor will be deleted.")));
    else {
      if(equipment){add("name","Nom","Name");if(section==="photovoltaic"){
        add("kind","Type d’équipement","Equipment type","select",[["micro_inverter",this._t("Micro-onduleur","Microinverter")],["dc_inverter",this._t("Onduleur DC","DC inverter")],["hybrid_inverter",this._t("Onduleur hybride","Hybrid inverter")]],null,current.kind||"micro_inverter");
        add("manufacturer","Fabricant","Manufacturer");add("model","Modèle","Model");const rated=add("nominal_power_w","Puissance nominale (W, facultatif)","Nominal power (W, optional)","number");rated.min=1;rated.max=1000000;
        for(const [key,fr,en] of [["power","Puissance sortie AC","AC output power"],["dc_power","Puissance photovoltaïque DC","DC photovoltaic power"],["charge_power","Charge batterie (hybride)","Battery charge (hybrid)"],["discharge_power","Décharge batterie (hybride)","Battery discharge (hybrid)"]])source(key,fr,en);
        source("energy","Énergie produite","Produced energy",["Wh","kWh"]);add("energy_period","Période du compteur","Counter period","select",[["today",this._t("Aujourd’hui","Today")],["total",this._t("Cumul total","Lifetime total")],["session",this._t("Session","Session")]],null,current.energy_period||"total");source("temperature","Température","Temperature",["°C","°F"]);source("status","État","Status",[]);
        form.append(this._node("p",this._t("Suivi uniquement : ces mesures ne sont pas agrégées dans le total solaire et ne modifient pas le bilan Maison. Distinguez les sorties AC, entrées DC et flux batterie d’un hybride.","Monitoring only: readings are not aggregated into solar total or Home balance. Distinguish AC outputs, DC inputs and hybrid battery flows."),"note"));
      }else if(section==="batteries"){
        add("role","Rôle","Role","select",[["backup",this._t("Secours","Backup")],["active",this._t("Active","Active")]],null,current.role||"backup");
        add("coupling","Couplage","Coupling","select",[["ac","AC"],["dc","DC"]],null,current.coupling||"ac");add("capacity_kwh","Capacité utile (kWh, facultatif)","Usable capacity (kWh, optional)","number");
        add("remaining_energy_is_stock","Je confirme que le capteur d’énergie représente le stock restant, même si sa classe HA indique un cumul","I confirm the energy sensor is remaining stock even if HA class says total","checkbox");
        source("charge_power","Puissance de charge","Charge power");source("discharge_power","Puissance de décharge","Discharge power");source("soc","État de charge (%)","State of charge (%)",["%"]);source("remaining_energy","Énergie restante mesurée","Measured remaining energy",["Wh","kWh"]);
      }else{
        if(section==="usages")add("kind","Type d’usage","Load type","select",[["solar_router",this._t("Routeur solaire","Solar router")],["water_heater",this._t("Cumulus / chauffe-eau","Water heater")],["ev_charger",this._t("Borne de recharge","EV charger")],["other",this._t("Autre usage","Other load")]],null,current.kind||"solar_router");
        if(section==="usages"){
          add("router_type","Profil du routeur solaire","Solar router profile","select",[["generic",this._t("Générique / cumulus existant","Generic / existing water heater")],["f1atb","F1ATB"]],null,current.router_type||"generic");
          add("router_connection","Connexion F1ATB","F1ATB connection","select",[["http",this._t("HTTP local direct","Direct local HTTP")],["mqtt","MQTT"]],null,current.router_connection||(identifier?"mqtt":"http"));
          const actionSelect=add("router_action","Action du routeur","Router action","select",[[String(current.router_action??0),this._t("Action ","Action ")+(current.router_action??0)]],null,String(current.router_action??0));
          add("router_http_enabled","Activer les commandes HTTP manuelles F1ATB","Enable manual F1ATB HTTP commands","checkbox");
          const discoverFeedback=this._node("p",undefined,"note");discoverFeedback.setAttribute("role","status");
          const discover=this._button(this._t("Lire le routeur et ses actions","Read router and actions"),async()=>{discover.disabled=true;try{const data=await this._hass.callWS({type:"ehome_ems/router_discover",host:controls.router_url.value.trim()});const previous=actionSelect.value;actionSelect.replaceChildren();for(const a of data.actions){const o=this._node("option",a.index+" · "+a.name+(a.mode===0?this._t(" (inactive)"," (inactive)"):""));o.value=a.index;actionSelect.append(o);}if([...actionSelect.options].some(o=>o.value===previous))actionSelect.value=previous;discoverFeedback.textContent=this._t("Actions lues. Aucune commande envoyée.","Actions read. No command sent.");}catch(error){discoverFeedback.textContent=this._t("Lecture impossible : vérifiez l’adresse et l’accès depuis HA. ","Read failed: check address and access from HA. ")+(error.code||"");}finally{discover.disabled=false;}});
          form.append(discover,discoverFeedback);controls.router_discover_button=discover;
          add("router_output","Sortie F1ATB","F1ATB output","select",[["ssr","SSR"],["triac","Triac"],["pwm","PWM"]],null,current.router_output||"ssr");
          add("router_url","Adresse IP ou URL du routeur","Router IP address or URL","text");add("router_mqtt_topic","Topic MQTT exact : nom routeur/nom action","Exact MQTT topic: router name/action name");
          add("router_protocol_confirmed","Je confirme le protocole F1ATB V15+ et la souscription au forçage MQTT activée sur le routeur","I confirm F1ATB V15+ protocol and enabled MQTT forcing subscription","checkbox");
          add("router_mqtt_enabled","Activer les commandes MQTT manuelles F1ATB","Enable manual F1ATB MQTT commands","checkbox");
          form.append(this._node("p",this._t("HTTP : connexion directe, sans autre intégration F1ATB. Saisissez l’adresse puis lisez les actions. MQTT : utilise le broker HA existant. Enregistrer cette fiche n’envoie aucune commande au routeur.","HTTP connects directly without another F1ATB integration. Enter the address then read actions. MQTT uses the existing HA broker. Saving this card sends no router command."),"note"));
        }
        add("icon","Icône du produit","Product icon","select",PRODUCT_ICONS.map(icon=>[icon,icon==="auto"?this._t("Automatique selon le nom","Automatic by name"):icon]),null,current.icon||"auto");
        source("power","Puissance (W/kW)","Power (W/kW)");source("energy","Énergie (Wh/kWh)","Energy (Wh/kWh)",["Wh","kWh"]);
        add("energy_period","Période du compteur d’énergie","Energy counter period","select",[["today",this._t("Aujourd’hui (remis à zéro chaque jour)","Today (resets daily)")],["session",this._t("Session","Session")],["total",this._t("Compteur cumulé","Lifetime counter")]],null,current.energy_period||"total");
        if(section==="usages" && current.kind==="ev_charger"){
          add("ev_tariff_mode","Tarification borne VE","EV charging tariff","select",[["flat",this._t("Tarif unique","Flat rate")],["hp_hc",this._t("Heures pleines / creuses","Peak / off-peak")]],null,current.ev_tariff_mode||"flat");
          for(const [key,fr,en] of [["ev_tariff_flat","Tarif unique (€/kWh)","Flat rate (EUR/kWh)"],["ev_tariff_hp","Heures pleines (€/kWh)","Peak rate (EUR/kWh)"],["ev_tariff_hc","Heures creuses (€/kWh)","Off-peak rate (EUR/kWh)"]]){
            const field=add(key,fr,en,"number",null,null,current[key]??"");field.max="10";
          }
          add("ev_hc_start","Début heures creuses (HH:MM)","Off-peak start (HH:MM)","text",null,null,current.ev_hc_start||"22:00");
          add("ev_hc_end","Fin heures creuses (HH:MM)","Off-peak end (HH:MM)","text",null,null,current.ev_hc_end||"06:00");
        }
        const tolerance=add("negative_power_tolerance_w","Tolérance puissance négative (W)","Negative power tolerance (W)","number",null,null,current.negative_power_tolerance_w??5);tolerance.max="20";
        const goal=add("daily_energy_goal_kwh","Objectif énergie quotidien (kWh, facultatif)","Daily energy goal (kWh, optional)","number");goal.min="0.001";goal.max="1000";
        source("status","État (facultatif)","Status (optional)",[]);
        const controlOptions=[["",this._t("Non associé","Not mapped")],...Object.entries(this._hass?.states||{}).filter(([id])=>["switch","input_boolean","light","fan"].includes(id.split(".")[0])).map(([id,state])=>[id,(state.attributes?.friendly_name||id)+" · "+id])];
        add("control_entity","Entité de commande On/Off","On/Off control entity","select",controlOptions,null,current.control_entity||(["switch","input_boolean","light","fan"].includes(current.status?.split(".")[0])?current.status:""));
        add("control_enabled","Activer la commande manuelle On/Off pour cet appareil","Enable manual On/Off for this device","checkbox");
        form.append(this._node("p",this._t("Chaque clic On/Off envoie une commande réelle à l’entité choisie. Aucun scénario ni rafraîchissement ne commande automatiquement cet appareil. L’objectif quotidien mesure la progression d’énergie consommée, pas la chaleur restante.","Each On/Off click sends a real command to the chosen entity. Scenarios and refreshes never command this device automatically. Daily goal tracks consumed energy, not remaining heat."),"note"));
        if(section==="usages"){
          source("temperature","Température de l’eau (facultatif)","Water temperature (optional)",["°C","°F"]);
          form.append(this._node("p",this._t("Capteur ou aide numérique input_number, avec une unité °C ou °F. La valeur affichée correspond à la source choisie (température actuelle, maximum du jour, etc.).","Sensor or input_number helper with °C or °F units. The displayed value follows the chosen source (current temperature, daily maximum, etc.)."),"note"));
        }
        add("included_in_home","Sous-comptage inclus dans le périmètre maison","Submetering included in the home boundary","checkbox");
        form.append(this._node("p",this._t("Le compteur cumulé permet de calculer le jour par différence depuis minuit via History/Recorder. Sans référence à minuit, l’énergie et le coût du jour restent indisponibles. Un compteur de session ne devient pas un compteur journalier.","Lifetime counters can yield daily usage from the midnight difference using History/Recorder. Without a midnight baseline, daily energy and cost remain unavailable. Session energy is not daily energy."),"note"));
      }}else if(section==="daily"){
        for(const [key,fr,en] of [["solar","Solaire du jour","Daily solar"],["home","Maison du jour","Daily home"],["import","Import du jour","Daily import"],["export","Export du jour","Daily export"],["charge","Charge batteries du jour","Daily battery charge"],["discharge","Restitution batteries du jour","Daily battery discharge"]])source(key,fr,en,["Wh","kWh"]);
        const weatherOptions=[["",this._t("Non associée","Not mapped")],...Object.entries(this._hass?.states||{}).filter(([id])=>id.startsWith("weather.")).map(([id,state])=>[id,state.attributes?.friendly_name||id])];
        add("weather_entity","Météo du jour (entité météo HA)","Daily weather (HA weather entity)","select",weatherOptions);
        const price=add("tariff_eur_kwh","Tarif fixe estimatif (€/kWh)","Estimated flat price (EUR/kWh)","number");price.max="10";
        form.append(this._node("p",this._t("Uniquement des compteurs du jour remis à zéro à minuit. Tarif facultatif, hors abonnement et revente. Effacer un champ retire son association.","Daily counters resetting at midnight only. Optional tariff, excluding standing charges and export revenue. Clear a field to remove its mapping."),"note"));
      }else if(section==="home"){
        add("home_power_mode","Origine de Conso Maison","Home consumption source","select",[["existing",this._t("Capteur existant (mesuré ou calculé)","Existing sensor (measured or calculated)")],["calculated",this._t("Calcul automatique EMS","EMS automatic calculation")]],null,current.home_power_mode||"existing");
        source("home_power","Capteur Conso Maison","Home consumption sensor");
        add("home_grid_mode","Réseau utilisé dans le bilan","Grid used in the balance","select",[["auto",this._t("Auto : Import/Export complets, sinon réseau signé","Auto: complete Import/Export, otherwise signed grid")],["signed",this._t("Réseau signé (+ import / − export)","Signed grid (+ import / − export)")],["separate",this._t("Deux capteurs Import et Export","Separate Import and Export sensors")]],null,current.home_grid_mode||"auto");
        for(const [key,fr,en] of [["home_has_solar","Production solaire présente","Solar production present"],["home_has_storage","Batteries actives présentes","Active batteries present"],["home_boundary_confirmed","Périmètre AC confirmé pour le calcul automatique","AC boundary confirmed for automatic calculation"]])add(key,fr,en,"checkbox");
        add("home_freshness_policy","Quand une source est ancienne","When a source is old","select",[["warn",this._t("Signaler sans bloquer (observation)","Warn without blocking (observation)")],["strict",this._t("Bloquer le calcul (strict)","Block calculation (strict)")]],null,current.home_freshness_policy||"warn");
        const age=add("home_max_age_seconds","Ancienneté maximale (secondes, 0 = contrôle désactivé)","Maximum source age (seconds, 0 = check disabled)","number",null,null,current.home_max_age_seconds??300);age.min="0";age.max="3600";
        form.append(this._node("p",this._t("Conso Maison = Production solaire + Réseau − Charge batterie + Décharge batterie. Réseau signé : positif en import, négatif en export ; avec deux capteurs, Réseau = Import − Export. Cumulus, borne, chauffage et appareils restent inclus. Les sous-compteurs ne sont jamais soustraits. Les puissances doivent être mesurées côté AC, sur le même périmètre. Un capteur existant doit déjà représenter ce total.","Home consumption = Solar + Grid − Battery charge + Battery discharge. Signed grid: import positive, export negative; separate sensors: Grid = Import − Export. Water heater, EV, heating and appliances remain included. Submeters are never subtracted. AC measurements must cover the same boundary. An existing home sensor must already represent this total."),"note"));
        form.append(this._node("p",this._t("Une puissance stable à 0 W peut être valide sans rapport fréquent. Si votre intégration ne republie que les changements, adaptez ce délai ou choisissez 0 en connaissance de cause : l’ancienneté reste affichée, mais ne bloque plus le calcul. Les valeurs absentes, invalides ou indisponibles restent bloquantes.","A stable 0 W reading may be valid without frequent reports. For change-only sources, adapt the timeout or explicitly choose 0: ages remain visible but no longer block the calculation. Missing, invalid and unavailable inputs still block it."),"note"));
        form.append(this._node("p",this._t("En observation, une source ancienne est signalée sans effacer le bilan. Le mode strict bloque après le délai. Une source absente, invalide ou indisponible bloque toujours le calcul.","Observation warns about old reports without hiding the balance. Strict mode blocks after the timeout. Missing, invalid and unavailable readings always block calculation."),"note"));
        const mode=controls.home_power_mode,homeInput=controls.home_power;
        const sync=()=>{homeInput.disabled=mode.value==="calculated";};mode.addEventListener("change",sync);sync();
      }else if(section==="grid"){
        // Shelly channels are existing Home Assistant power entities; no Shelly API or extra integration.
        const shellyChannels=Object.entries(this._hass?.states||{}).filter(([id,state])=>
          id.startsWith("sensor.") && ["W","kW"].includes(state.attributes?.unit_of_measurement) &&
          /shelly/i.test(id+" "+(state.attributes?.friendly_name||"")) &&
          !/total|energy|voltage|current|frequency|factor/i.test(id+" "+(state.attributes?.friendly_name||""))
        ).sort(([a],[b])=>a.localeCompare(b,"fr",{numeric:true}));
        if(shellyChannels.length){
          const choices=[["",this._t("Choisir un canal Shelly…","Choose a Shelly channel…")],
            ...shellyChannels.map(([id,state])=>[id,(state.attributes?.friendly_name||id)+" · "+id])];
          const picker=add("shelly_grid_channel","Canal Shelly dédié au réseau","Shelly channel dedicated to grid","select",choices,null,"");
          form.append(this._node("p",this._t("Sélectionnez le canal mesurant l'échange net avec le réseau (+ import, − injection). Le choix remplit le capteur Réseau signé ci-dessous. Un canal de phase isolé ne représente pas le réseau complet d'une installation triphasée.","Select the channel measuring net grid power (+ import, − export). This fills the signed grid sensor below. A single phase channel does not represent the entire grid on three-phase installations."),"note"));
          picker.addEventListener("change",()=>{if(picker.value){controls.grid_power.value=picker.value;}});
        }else{
          form.append(this._node("p",this._t("Aucun canal Shelly de puissance détecté dans les entités Home Assistant. Vous pouvez toujours choisir manuellement un capteur réseau ci-dessous.","No Shelly power channel detected among Home Assistant entities. You can still select a grid sensor manually below."),"note"));
        }
        for(const [key,fr,en] of [["grid_power","Réseau signé (facultatif)","Signed grid (optional)"],["grid_import","Import réseau","Grid import"],["grid_export","Export réseau","Grid export"]])source(key,fr,en);
      }else source("solar_power","Production solaire","Solar production");
    }
    if(section==="usages"&&!remove){
      const syncRouter=()=>{const router=controls.kind.value==="solar_router",f1atb=router&&controls.router_type.value==="f1atb",http=f1atb&&controls.router_connection.value==="http";
        controls.router_type.closest("label").hidden=!router;
        for(const key of ["router_connection","router_url"])controls[key].closest("label").hidden=!f1atb;
        for(const key of ["router_action","router_http_enabled"])controls[key].closest("label").hidden=!http;
        controls.router_discover_button.hidden=!http;
        for(const key of ["router_output","router_mqtt_topic","router_mqtt_enabled","router_protocol_confirmed"])controls[key].closest("label").hidden=!f1atb||http;
        if(!f1atb){controls.router_mqtt_enabled.checked=false;controls.router_http_enabled.checked=false;}
      };controls.kind.addEventListener("change",syncRouter);controls.router_type.addEventListener("change",syncRouter);controls.router_connection.addEventListener("change",syncRouter);syncRouter();
    }
    const message=this._node("p","","note bad");message.setAttribute("role","status");
    const actions=this._node("div",undefined,"actions"),cancel=this._button(this._t("Annuler","Cancel"),()=>dialog.close());cancel.disabled=false;
    const revision=this._snapshotData.revision;
    const save=this._button(remove?this._t("Confirmer le retrait","Confirm removal"):this._t("Enregistrer","Save"),async()=>{
      if(!remove && !form.reportValidity())return;
      const values={};for(const [key,input] of Object.entries(controls)){if(key==="router_discover_button"||key==="shelly_grid_channel")continue;if(input.type==="checkbox")values[key]=input.checked;else if(input.value.trim()!=="")values[key]=input.type==="number"?Number(input.value):input.value.trim();}
      if(section==="usages"&&!remove){values.router_action=Number(values.router_action??0);if(values.kind!=="solar_router"||values.router_type!=="f1atb"){delete values.router_connection;delete values.router_action;delete values.router_http_enabled;}}
      save.disabled=true;form.inert=true;
      try{
        await this._hass.callWS({type:"ehome_ems/manage_settings",entry_id:this._panel.config.entry_id,revision,section,action:remove?"remove":"save",identifier,values});
        this._settingsRetries=5;dialog.close();await this._load();this._message.textContent=this._t("Configuration enregistrée. Aucune commande envoyée.","Settings saved. No device commands sent.");
      }catch(error){message.textContent=error.code==="conflict"?this._t("La configuration a changé. Annulez et actualisez avant de réessayer.","Configuration changed. Cancel and refresh before retrying."):
        this._t("Réglages refusés : vérifier sources, unités, doublons et périmètre maison. ","Settings rejected: check sources, units, duplicates and home boundary. ")+(error.message||error.code||"");
        if(String(error.message).includes("cumulative_energy"))message.textContent+=this._t(" Ce capteur est classé cumulé dans HA. S’il s’agit bien du stock restant, cochez la confirmation dédiée."," HA classifies this as a cumulative counter. If it is truly remaining stock, check the dedicated confirmation.");
        if(String(error.message).includes("exceeds_capacity"))message.textContent+=this._t(" Le stock dépasse la capacité déclarée : vérifiez la valeur, l’unité et la capacité."," Stock exceeds declared capacity: check value, unit and capacity.");}
      finally{save.disabled=false;form.inert=false;}
    });
    form.addEventListener("submit",event=>{event.preventDefault();save.click();});actions.append(cancel,save);dialog.append(form,message,actions);
    dialog.addEventListener("close",()=>{dialog.remove();if(this._dialog===dialog)this._dialog=null;});this.shadowRoot.append(dialog);dialog.showModal();(form.querySelector("input,select")||cancel).focus();
  }

  _configuration(snapshot) {
    const root = this._node("section", undefined, "card");
    root.append(this._node("h2", this._t("Configuration et associations", "Configuration and mappings")),
      this._node("p", this._t("Utilisez les raccourcis ci-dessous pour modifier uniquement la rubrique choisie. L’assistant complet reste accessible par la roue crantée de l’intégration.",
        "Use the shortcuts to edit only the selected section. The integration gear still opens the complete wizard."), "note"));
    const links = this._node("div", undefined, "config-links");
    const integration = this._node("a", this._t("Ouvrir l’intégration eHome EMS", "Open eHome EMS integration"));
    integration.href = "/config/integrations/integration/ehome_ems"; links.append(integration); root.append(links);
    if(this._hass?.user?.is_admin)root.append(this._settingsShortcuts(snapshot));

    root.append(this._node("p", this._t("Seuil d’animation : 10 W. Ce seuil visuel ne modifie ni les mesures ni les calculs. Une valeur sous ce seuil ne prouve pas qu’un équipement est arrêté.",
      "Animation threshold: 10 W. This visual threshold changes neither readings nor calculations. A reading below this threshold does not prove a device is off."), "note"));
    const list = this._node("div", undefined, "source-list");
    for (const [entity, binding] of Object.entries(snapshot.bindings || {})) {
      const item = this._node("div", undefined, "source-item"), text = this._node("div");
      text.append(this._node("strong", this._hass?.states[entity]?.attributes?.friendly_name || entity),
        this._node("code", binding.calculated_home ? this._t("Calcul automatique EMS", "EMS automatic calculation") : binding.source || this._t("Source absente", "Missing source")));
      const diagnostic = this._node("p", undefined, "note"); text.append(diagnostic);
      this._flowUpdates.push(() => {
        const state = this._hass?.states?.[entity];
        const quality = state?.attributes?.data_quality;
        const labels = {
          valid: this._t("Valeur et unité valides", "Valid value and unit"),
          unavailable: this._t("Indisponible", "Unavailable"),
          unsupported_unit: this._t("Unité incompatible", "Unsupported unit"),
          invalid_value: this._t("Valeur non numérique ou invalide", "Invalid or non-numeric value"),
          unexpected_direction: this._t("Signe inattendu", "Unexpected direction"),
          out_of_range: this._t("Valeur hors limites", "Out of range"),
          cumulative_energy: this._t("Compteur cumulé utilisé comme stock", "Cumulative counter used as stored energy"),
          exceeds_capacity: this._t("Stock supérieur à la capacité déclarée", "Stored energy exceeds declared capacity"),
          stale_source: this._t("Source périmée", "Stale source"),
          negative_balance: this._t("Bilan négatif incohérent", "Inconsistent negative balance"),
        };
        const available = state && !["unknown", "unavailable"].includes(state.state);
        const reason = labels[quality] || (!available ? this._t("Indisponible", "Unavailable") :
          this._t("Qualité non renseignée", "Quality not reported"));
        diagnostic.textContent = this._t("Mesure EMS : ", "EMS reading: ") + reading(this._hass?.states, entity, undefined, this._hass?.language).text + " · " + reason;
        if (binding.source) diagnostic.textContent += this._t(" · Source : ", " · Source: ") + reading(this._hass?.states, binding.source, undefined, this._hass?.language).text;
        diagnostic.title = quality || ""; diagnostic.classList.toggle("good",available && quality === "valid"); diagnostic.classList.toggle("bad",!available || (quality && quality !== "valid"));
      });
      item.append(text);
      if (this._hass?.user?.is_admin) item.append(this._button(this._t("Changer la source", "Change source"), () => this._edit(entity)));
      list.append(item);
    }
    root.append(list);
    const view = snapshot.dashboard.views.find(view => view.path === "quality");
    for (const card of view?.cards || []) root.append(this._card(card));
    return root;
  }
  _card(config) {
    const card = this._node("div", undefined, config.type === "vertical-stack" ? "stack" :
      config.type === "grid" ? "nested-grid" : "card");
    if (config.title) card.append(this._node("h2", config.title));
    if (config.type === "markdown") card.append(this._node("p", config.content, "note"));
    if (config.cards) config.cards.forEach(item => card.append(this._card(item)));
    if (config.type === "entities") for (const item of config.entities) {
      if (!item.attribute) {
        const color = this._tone(item.entity);
        card.append(this._metricTile(item.name, item.entity, this._entityIcon(item.entity), color));
      } else {
        const row = this._node("div", undefined, "row"), value = this._node("span", undefined, "value");
        this._bind(value, item.entity, item.attribute);
        row.append(this._node("span", item.name), value); card.append(row);
      }
    }
    if (config.type === "gauge") card.append(this._metricTile(config.name, config.entity, this._entityIcon(config.entity), this._tone(config.entity)));
    if (config.type === "history-graph") {
      card.classList.add("history");
      card.append(this._node("p", this._t("Ouvrir l’historique d’une mesure :", "Open a reading's history:"), "note"));
      for (const entityId of config.entities) {
        const name = this._hass?.states?.[entityId]?.attributes?.friendly_name || entityId;
        const row=this._node("div",undefined,"history-row");row.append(this._button(name, () => this.dispatchEvent(new CustomEvent("hass-more-info", {
          detail: { entityId }, bubbles: true, composed: true,
        }))),this._historyChart(entityId));card.append(row);
      }
    }
    return card;
  }
  _refresh() {
    this._loadHistory();this._loadHistory24();this._loadUsageHistory();this._subscribeWeather();
    for (const update of this._flowUpdates || []) update();
    for (const binding of this._bindings) {
      const value = reading(this._hass?.states, binding.entity, binding.attribute, this._hass?.language || "fr");
      if (binding.gauge) {
        binding.element.hidden = value.number === null;
        if (value.number !== null) binding.element.value = Math.max(0,
          Math.min(binding.gauge.max - binding.gauge.min, value.number - binding.gauge.min));
      } else { binding.element.classList.toggle("bad",value.number===null && ["Indisponible","Unavailable"].includes(value.text)); binding.element.classList.toggle("good",binding.attribute==="data_quality" && value.text==="valid"); binding.element.textContent = value.text; binding.element.classList.toggle("missing", value.number === null); binding.element.title = value.text; }
    }
  }
  _flow(config) {
    config = {...config, usages:(config.usages || []).filter(u => u.kind !== "appliance")};
    const root = this._node("section", undefined, "flow");
    root.setAttribute("aria-label", this._t("Flux d’énergie", "Energy flow"));
    root.append(this._node("h2", this._t("Flux en direct", "Live energy flow")));
    root.append(this._node("p", this._t("Observation · animation à partir de 10 W. Les faibles consommations restent affichées.",
      "Observation · animation from 10 W. Low readings remain visible."), "flow-note"));
    const stage = this._node("div", undefined, "flow-stage");
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 1000 830"); svg.classList.add("flow-links"); svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("preserveAspectRatio", "none");
    const defs=document.createElementNS(svg.namespaceURI,"defs");svg.append(defs);let arrowIndex=0;
    const link = (d, color, entity, reverse = false) => {
      const marker=document.createElementNS(svg.namespaceURI,"marker"),head=document.createElementNS(svg.namespaceURI,"path");
      marker.id=`flow-arrow-${arrowIndex++}`;marker.setAttribute("viewBox","0 0 8 8");marker.setAttribute("refX","7");marker.setAttribute("refY","4");marker.setAttribute("markerWidth","3");marker.setAttribute("markerHeight","3");marker.setAttribute("orient","auto");
      head.setAttribute("d","M0 0 L8 4 L0 8 Z");head.style.fill=color;head.style.stroke="none";head.style.opacity="1";marker.append(head);defs.append(marker);
      const path = document.createElementNS(svg.namespaceURI, "path");
      path.setAttribute("d", d); path.style.color = color; svg.append(path);
      this._flowUpdates.push(() => {
        const power = flowPower(this._hass?.states, entity);
        path.classList.toggle("active", flowActive(this._hass?.states, entity));
        path.setAttribute("marker-end",flowActive(this._hass?.states,entity)?`url(#${marker.id})`:"none");
        path.classList.toggle("unknown", power === null);
        path.classList.toggle("reverse", reverse);
      });
      return path;
    };
    const entities = config.entities || {};
    const solarPath=link("M230 140 V210 Q230 245 280 245 H480 Q520 245 520 290", "#ffce45", entities.solar_power);
    const exportPath=link("M730 360 Q800 350 800 290 V150", "#58aeff", entities.grid_export);
    const importPath=link("M850 150 V300 Q850 380 750 400", "#ff6565", entities.grid_import);
    const primary = config.batteries?.find(battery => battery.role === "active" && battery.coupling === "ac");
    const connectedBatteries = (config.batteries || []).filter(b => b.role === "active" && b.coupling === "ac");
    const batteryPaths = connectedBatteries.map(b => [
      link("M460 480 H180", "#50e49b", b.charge_power),
      link("M180 480 H460", "#58aeff", b.discharge_power),
    ]);
    stage.append(svg);
    const icon = (name) => { const el = this._node("ha-icon"); el.setAttribute("icon", name); return el; };
    const metric = (parent, entity) => {
      const el = this._node("span", undefined, "flow-number"); parent.append(el);
      this._bind(el, entity); if (entity) this._editable(parent, entity); return el;
    };
    const tile = (className, title, mdi, entity) => {
      const el = this._node("div", undefined, className); el.append(icon(mdi), this._node("span", title, "flow-title"));
      metric(el, entity); return el;
    };
    const day=(parent,source)=>{
      const el=this._node("span",undefined,"flow-day-energy"),entity=typeof source==="string"?source:source?.energy;
      this._historyLink(el,entity);this._flowUpdates.push(()=>{const energy=source&&typeof source==="object"?this._dayEnergy(source):this._energy(source);el.textContent=energy===null?this._t("Jour : indisponible","Today: unavailable"):displayNumber(energy,this._hass.language)+this._t(" kWh aujourd’hui"," kWh today");});parent.append(el);
    };
    const solarTile=tile("flow-tile flow-solar", this._t("Solaire", "Solar"), "mdi:white-balance-sunny", entities.solar_power);day(solarTile,this._snapshotData?.daily?.solar);stage.append(solarTile);
    const grid = this._node("div", undefined, "flow-tile flow-grid");
    grid.append(icon("mdi:transmission-tower"), this._node("span", this._t("Réseau", "Grid"), "flow-title"));
    for (const [key, label] of [["grid_import", this._t("Import", "Import")], ["grid_export", this._t("Export", "Export")]]) {
      grid.append(this._node("span", label, "flow-small"));
      const row = this._node("div"); row.style.color=key === "grid_import" ? "#ff6565" : "#58aeff"; metric(row, entities[key]);day(row,this._snapshotData?.daily?.[key==="grid_import"?"import":"export"]); grid.append(row);
    }
    this._flowUpdates.push(()=>{
      const incoming=flowPower(this._hass?.states,entities.grid_import),outgoing=flowPower(this._hass?.states,entities.grid_export);
      grid.style.color=incoming>=10?"#ff6565":outgoing>=10?"#58aeff":"#9eb2c8";
    });
    stage.append(grid);
    const house = this._node("div", undefined, "flow-house");
    const picture = this._node("img");
    this._flowUpdates.push(()=>{
      const mode=houseMode(new Date(),this._hass?.config?.time_zone || this._snapshotData?.time_zone || "UTC");
      const asset=mode==="day"?"house-day.webp":"house.webp";
      if(picture.dataset.mode!==mode){picture.dataset.mode=mode;picture.src="/ehome_ems_assets/"+asset;picture.alt=this._t(mode==="day"?"Maison en journée":"Maison de nuit",mode==="day"?"House by day":"House at night");}
    });
    picture.width = 600; picture.height = 300;
    house.append(picture, this._node("div", this._t("Conso Maison", "Home consumption"), "flow-title"));
    metric(house, entities.home_power);day(house,this._snapshotData?.daily?.home);stage.append(house);
    const batteryTile = (battery, className) => {
      const el = this._node("div", undefined, className);
      el.append(icon("mdi:battery-high"), this._node("span", battery.name, "flow-title"));this._equipmentActions(el,battery,"batteries");
      for (const [key, other, label] of [["charge_power", "discharge_power", this._t("Charge", "Charge")], ["discharge_power", "charge_power", this._t("Décharge", "Discharge")]]) {
        const group = this._node("div",undefined,"battery-direction");group.dataset.direction=key;group.style.color=key==="charge_power"?"#50e49b":"#58aeff"; group.append(this._node("span", label, "flow-small"));
        const row = this._node("div"); metric(row, battery[key]);day(row,connectedBatteries.length===1?this._snapshotData?.daily?.[key==="charge_power"?"charge":"discharge"]:null); group.append(row); el.append(group);
        this._flowUpdates.push(() => { group.hidden = false; });
      }
      const progress = this._node("progress"); progress.max = 100;
      progress.setAttribute("aria-label", this._t("État de charge", "State of charge")); el.append(progress);
      this._flowUpdates.push(() => { const soc = reading(this._hass?.states, battery.soc).number;
        progress.hidden = soc === null || soc < 0 || soc > 100;
        if (!progress.hidden) progress.value = soc;
      });
      const soc = this._node("div"); metric(soc, battery.soc); el.append(soc);
      el.append(this._node("span", `${battery.role === "active" ? this._t("Active", "Active") : this._t("Secours", "Backup")} · ${battery.coupling.toUpperCase()}`, "flow-small"));
      return el;
    };
    const batteryTiles = connectedBatteries.map((battery,index) => {
      const tile = batteryTile(battery,"flow-tile flow-battery");
      tile.dataset.batteryIndex = index;stage.append(tile);return tile;
    });
    const sceneWrap = this._node("div", undefined, "flow-scene-wrap"); sceneWrap.append(stage); root.append(sceneWrap);
    // The wrapper reserves the real card bounds while the scene geometry stays
    // fixed, avoiding feedback from percentage-positioned cards on resize.
    const reserveScene = () => {
      if (!stage.isConnected) return;
      const bounds = stage.getBoundingClientRect();
      if(bounds.width&&bounds.height)house.style.top=Math.max(bounds.height*.22,Math.max(solarTile.getBoundingClientRect().bottom,grid.getBoundingClientRect().bottom)-bounds.top+16)+"px";
      if (bounds.width && bounds.height && batteryTiles.length) {
        const houseBounds = house.getBoundingClientRect();
        let nextTop = Math.max(bounds.height * (bounds.width < 600 ? .59 : .47),houseBounds.top-bounds.top+houseBounds.height*.45);
        batteryTiles.forEach((tile,index) => {
          tile.style.top = nextTop + "px";
          const tileBounds = tile.getBoundingClientRect();
          const x1=(tileBounds.right-bounds.left)*1000/bounds.width,y1=(tileBounds.top+tileBounds.height/2-bounds.top)*830/bounds.height;
          const x2=(houseBounds.left+houseBounds.width*.12-bounds.left)*1000/bounds.width,y2=(houseBounds.top+houseBounds.height*.44-bounds.top)*830/bounds.height;
          batteryPaths[index][0].setAttribute("d",`M${x2} ${y2} H${x1+30} Q${x1+15} ${y2} ${x1+15} ${(y1+y2)/2} V${y1} H${x1}`);
          batteryPaths[index][1].setAttribute("d",`M${x1} ${y1} H${x1+15} V${(y1+y2)/2} Q${x1+15} ${y2} ${x1+30} ${y2} H${x2}`);
          nextTop += tileBounds.height + 12;
        });
      }
      if(bounds.width && bounds.height) {
        const h=house.getBoundingClientRect(),a=solarTile.getBoundingClientRect(),g=grid.getBoundingClientRect();
        const x=v=>(v-bounds.left)*1000/bounds.width,y=v=>(v-bounds.top)*830/bounds.height;
        const sx=x(a.right),sy=y(a.top+a.height*.55),hx=x(h.left+h.width*.48),hy=y(h.top+15);
        solarPath.setAttribute("d",`M${sx} ${sy} H${hx-40} Q${hx} ${sy} ${hx} ${sy+35} V${hy}`);
        const gx=x(g.left+g.width*.5),gy=y(g.bottom),rx=x(h.right-h.width*.12),ry=y(h.top+h.height*.40);
        exportPath.setAttribute("d",`M${rx} ${ry} H${gx-30} Q${gx} ${ry} ${gx} ${ry-30} V${gy}`);
        importPath.setAttribute("d",`M${gx} ${gy} V${ry-30} Q${gx} ${ry} ${gx-30} ${ry} H${rx}`);
      }
      let bottom = Math.max(bounds.bottom, ...Array.from(stage.children)
        .filter(child => child !== svg).map(child => child.getBoundingClientRect().bottom));
      sceneWrap.style.minHeight = Math.ceil(bottom - bounds.top + 16) + "px";
    };
    const observer = new ResizeObserver(reserveScene);
    observer.observe(stage);
    for (const child of stage.children) if (child !== svg) observer.observe(child);
    this._layoutObservers.push(observer); this._flowUpdates.push(reserveScene);
    const usageNote=this._node("p", config.home_calculated ?
      this._t("Usages suivis · inclus dans le total maison, sans ajout supplémentaire.", "Tracked loads · included in home total, not added again.") :
      this._t("Usages suivis · vérifiez le périmètre de votre capteur Maison (cumulus inclus ou exclu).", "Tracked loads · check your Home source boundary (water heater included or excluded)."), "flow-usage-title");
    const usages = this._node("div", undefined, "flow-usages");
    for (const usage of config.usages || []) {
      const mdi = productIcon(usage);
      const el = tile("flow-usage", usage.name, mdi, usage.power);this._equipmentActions(el,usage,"usages");
      day(el,usage);
      el.style.color = ["solar_router","water_heater"].includes(usage.kind) ? "#ffab4d" : usage.kind === "ev_charger" ? "#c18aff" : "#edf4ff";
      usages.append(el);
    }
    if (!config.usages?.length) usages.append(this._node("p", this._t("Aucun usage associé. Ajoutez le cumulus, le routeur ou le véhicule dans Configurer.", "No tracked loads. Add the water heater, router or vehicle in Configure."), "flow-note"));
    root.append(usages, usageNote);
    if (config.batteries?.some(battery => !connectedBatteries.includes(battery))) {
      const extra = this._node("div", undefined, "flow-extra");
      for (const battery of config.batteries.filter(battery => !connectedBatteries.includes(battery))) {
        const card=tile("flow-usage",battery.name,"mdi:battery-high",battery.soc);
        card.style.color="#8bb6ed";card.append(this._node("span",battery.role === "backup" ? this._t("Secours · hors bilan maison AC","Backup · outside AC home balance") : this._t("DC · suivi séparé","DC · separate monitoring"),"flow-small"));extra.append(card);
      }
      root.append(extra);
    }
    return root;
  }
  _entityPicker(parent,input,options,contextName=null) {
    if(!input.hasAttribute("aria-label"))input.setAttribute("aria-label",parent.firstChild?.textContent||this._t("Entité","Entity"));
    const picker=this._node("div",undefined,"entity-picker"),list=this._node("div",undefined,"entity-options");list.hidden=true;
    const button=this._button(this._t("Choisir une entité","Choose an entity"),()=>{list.hidden=!list.hidden;if(!list.hidden){draw("");input.focus();}button.setAttribute("aria-expanded",String(!list.hidden));});
    button.setAttribute("aria-label",this._t("Choisir une entité · ","Choose an entity · ")+input.getAttribute("aria-label"));button.setAttribute("aria-expanded","false");
    const draw=query=>{list.replaceChildren();const needle=query.toLocaleLowerCase(),matches=rankEntityOptions(options.filter(([id,name])=>(id+" "+name).toLocaleLowerCase().includes(needle)),contextName?.()||parent.closest("form")?.querySelector("[name=name]")?.value||"");
      for(const [id,name] of matches.slice(0,100)){const choice=this._button(name===id?id:name+" · "+id,()=>{input.value=id;list.hidden=true;button.setAttribute("aria-expanded","false");input.dispatchEvent(new Event("change",{bubbles:true}));input.focus();});choice.title=id;list.append(choice);}
      if(!matches.length)list.append(this._node("p",this._t("Aucune entité compatible","No compatible entity"),"note"));
      if(matches.length>100)list.append(this._node("p",this._t("Saisissez quelques lettres pour affiner les résultats.","Type a few letters to narrow the results."),"note"));
    };
    input.addEventListener("input",()=>{list.hidden=false;button.setAttribute("aria-expanded","true");draw(input.value);});
    input.addEventListener("keydown",e=>{if(e.key==="Escape"&&!list.hidden){e.preventDefault();e.stopPropagation();list.hidden=true;button.setAttribute("aria-expanded","false");}});
    picker.append(button,list);parent.append(picker);
  }
  _historyLink(element,entities) {
    const ids=[...new Set((Array.isArray(entities)?entities:[entities]).filter(Boolean))];if(!ids.length)return;
    element.classList.add("history-value");element.tabIndex=0;element.setAttribute("role","button");
    element.setAttribute("aria-label",this._t("Afficher l’historique","Show history"));
    element.addEventListener("click",event=>{event.stopPropagation();if(!this._dialog?.open)this._openHistory(ids);});
    element.addEventListener("keydown",event=>{if(!event.shiftKey&&(event.key==="Enter"||event.key===" ")){event.preventDefault();event.stopPropagation();this._openHistory(ids);}});
  }
  async _openHistory(entities) {
    if(this._dialog?.open)return;
    const ids=[...new Set(entities.map(id=>this._snapshotData?.bindings?.[id]?.source||id))];
    const dialog=this._node("dialog",undefined,"reading-history");this._dialog=dialog;
    const title=this._node("h2",this._t("Historique des mesures","Reading history"));dialog.setAttribute("aria-label",title.textContent);
    const controls=this._node("div",undefined,"actions"),body=this._node("div");let request=0;
    const draw=async hours=>{
      const token=++request;body.replaceChildren(this._node("p",this._t("Chargement…","Loading…")));
      try{
        const end=Date.now(),start=end-hours*3600000;
        const rows=await this._hass.callApi("GET",`history/period/${new Date(start).toISOString()}?filter_entity_id=${encodeURIComponent(ids.join(","))}&end_time=${new Date(end).toISOString()}&minimal_response&significant_changes_only=0`);
        if(token!==request||!dialog.open)return;body.replaceChildren();
        for(const id of ids){
          const state=this._hass.states[id],unit=state?.attributes?.unit_of_measurement||"",section=this._node("section",undefined,"history-series");
          section.append(this._node("h3",(state?.attributes?.friendly_name||id)+" · "+unit));
          const records=(rows||[]).find(r=>r[0]?.entity_id===id)||[],segments=historySegments(records),values=segments.flat().map(p=>p.value);
          if(!values.length)section.append(this._node("p",this._t("Aucun historique disponible. Vérifiez Recorder et sa rétention.","No history available. Check Recorder and retention."),"note"));
          else{
            const lo=values.reduce((a,b)=>Math.min(a,b),Infinity),hi=values.reduce((a,b)=>Math.max(a,b),-Infinity),span=hi-lo||1,svg=document.createElementNS("http://www.w3.org/2000/svg","svg");svg.setAttribute("viewBox","0 0 760 200");svg.setAttribute("role","img");svg.setAttribute("aria-label",(state?.attributes?.friendly_name||id)+" · "+lo+"–"+hi+" "+unit);
            for(const segment of segments){const step=Math.max(1,Math.ceil(segment.length/3000)),points=segment.filter((p,i)=>i%step===0||i===segment.length-1).map(p=>[Math.max(0,Math.min(760,(p.time-start)/(end-start)*760)),180-(p.value-lo)/span*160]);const path=document.createElementNS(svg.namespaceURI,"path");path.setAttribute("d",points.map(([x,y],i)=>(i?"L":"M")+x+","+y).join(" "));path.setAttribute("fill","none");path.setAttribute("stroke","#5bb8ff");path.setAttribute("stroke-width","2");svg.append(path);}
            section.append(this._node("p",new Date(start).toLocaleString(this._hass.language)+" → "+new Date(end).toLocaleString(this._hass.language),"note"),svg,this._node("p",this._t("Minimum : ","Minimum: ")+displayNumber(lo,this._hass.language)+" · Max : "+displayNumber(hi,this._hass.language)+" "+unit,"note"));
          }
          section.append(this._button(this._t("Ouvrir la fiche Home Assistant","Open Home Assistant details"),()=>{dialog.close();this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:id},bubbles:true,composed:true}));}));body.append(section);
        }
        body.append(this._node("p",this._t("Historique des sources d’origine. Un compteur cumulé affiche son cumul ; le total du jour est calculé séparément. Pour un total, les sources sont affichées individuellement, sans addition de périmètres.","Original source history. A cumulative counter shows its total; today’s energy is calculated separately. For an aggregate, sources are shown individually."),"note"));
      }catch{if(token===request)body.replaceChildren(this._node("p",this._t("Historique indisponible : connexion ou Recorder à vérifier.","History unavailable: check connection or Recorder."),"note warn"));}
    };
    controls.append(this._button("24 h",()=>draw(24)),this._button("7 j",()=>draw(168)),this._button(this._t("Fermer","Close"),()=>dialog.close()));dialog.append(title,controls,body);
    dialog.addEventListener("close",()=>{request++;dialog.remove();if(this._dialog===dialog)this._dialog=null;});this.shadowRoot.append(dialog);dialog.showModal();await draw(24);
  }
  _alerts() {
    const root=this._node("section",undefined,"card alerts-panel");root.append(this._node("h2",this._t("Alertes et Notifications","Alerts and Notifications")),this._node("p",this._t("Configurez les seuils et le destinataire HA. Aucune alerte n’est activée par défaut. Import quotidien : une notification par jour ; puissance et indisponibilité : une par épisode.","Configure thresholds and HA notification service. Alerts are disabled by default. Daily import: once per day; power and unavailability: once per episode."),"note"));
    const content=this._node("div");root.append(content);const load=async()=>{
      try{const data=await this._hass.callWS({type:"ehome_ems/alerts",entry_id:this._panel.config.entry_id});if(!root.isConnected)return;content.replaceChildren();
        let rules=structuredClone(data.rules||[]);const savedIds=new Set(rules.map(r=>r.id));
        if(this._hass.user?.is_admin){
          const form=this._node("form",undefined,"alert-form"),list=this._node("div"),message=this._node("p",undefined,"note");message.setAttribute("role","status");
          const draw=()=>{list.replaceChildren();for(const rule of rules){
            const detail=this._node("details",undefined,"alert-rule"),summary=this._node("summary"),row=this._node("fieldset");detail.open=!savedIds.has(rule.id);detail.append(summary,row);
            const summaryText=()=>{summary.textContent=(rule.label||this._t("Alerte sans nom","Unnamed alert"))+" · "+(rule.enabled?this._t("Activée","Enabled"):this._t("Désactivée","Disabled"))+" · "+({daily_import:rule.threshold+" kWh",import_power:rule.threshold+" W",entity_unavailable:rule.duration_minutes+" min"}[rule.kind]||rule.kind);};summaryText();
            const field=(label,key,control)=>{const l=this._node("label",label);l.append(control);row.append(l);control.addEventListener("change",()=>{rule[key]=control.type==="checkbox"?control.checked:control.type==="number"?Number(control.value):control.value;summaryText();});};
            const select=(values,current)=>{const el=this._node("select");for(const [value,name]of values){const option=this._node("option",name);option.value=value;el.append(option);}el.value=current;return el;};
            const name=this._node("input");name.value=rule.label||"";name.maxLength=80;name.placeholder=this._t("Ex. Import supérieur à 12 kWh","E.g. Import above 12 kWh");field(this._t("Nom de l’alerte","Alert name"),"label",name);
            field(this._t("Type","Type"),"kind",select([["daily_import",this._t("Import réseau quotidien (kWh)","Daily grid import (kWh)")],["import_power",this._t("Puissance d’import (W)","Grid import power (W)")],["entity_unavailable",this._t("Entité indisponible","Unavailable entity")]],rule.kind));
            const entity=this._node("input");entity.value=rule.entity;entity.setAttribute("list","alert-entities");entity.required=true;field(this._t("Entité source","Source entity"),"entity",entity);entity.removeAttribute("list");this._entityPicker(entity.parentElement,entity,Object.entries(this._hass.states).map(([id,state])=>[id,state.attributes?.friendly_name||id]));
            for(const [key,label]of [["threshold",this._t("Seuil (kWh ou W selon type)","Threshold (kWh or W by type)")],["duration_minutes",this._t("Durée avant alerte (minutes)","Delay before alert (minutes)")]]){const input=this._node("input");input.type="number";input.min=key==="threshold"?"0.01":"0";input.max=key==="threshold"?"1000000":"1440";input.step="any";input.value=rule[key];input.required=true;field(label,key,input);}
            field(this._t("Notifier via","Notify via"),"notify_service",select((data.notify_services||["persistent_notification.create"]).map(n=>[n,n]),rule.notify_service));
            for(const [key,label]of [["daily_confirmed",this._t("Pour l’import quotidien : je confirme que cette entité mesure le jour civil et se remet à zéro chaque jour.","For daily import: I confirm this entity measures the current calendar day and resets daily.")],["enabled",this._t("Activer cette alerte","Enable this alert")]]){const input=this._node("input");input.type="checkbox";input.checked=rule[key];field(label,key,input);}
            row.append(this._button(this._t("Supprimer cette alerte","Remove this alert"),()=>{rules=rules.filter(r=>r!==rule);draw();}));list.append(detail);
          }};
          const choices=this._node("datalist");choices.id="alert-entities";for(const [id,state]of Object.entries(this._hass.states)){const o=this._node("option");o.value=id;o.label=state.attributes?.friendly_name||id;choices.append(o);}
          const add=this._button(this._t("Ajouter une alerte","Add an alert"),()=>{rules.push({id:newCopyToken().replaceAll("-","").slice(0,32),kind:"daily_import",label:"",entity:this._snapshotData?.daily?.import||"",threshold:12,duration_minutes:0,enabled:false,notify_service:"persistent_notification.create",daily_confirmed:false});draw();});
          const save=this._node("button",this._t("Enregistrer les alertes","Save alerts"));save.type="submit";form.addEventListener("submit",async event=>{event.preventDefault();save.disabled=true;try{await this._hass.callWS({type:"ehome_ems/save_alerts",entry_id:this._panel.config.entry_id,revision:this._snapshotData.revision,rules});await this._load();}catch(error){message.textContent=this._t("Enregistrement refusé : vérifier entités, unités, confirmation du compteur du jour et actualiser. ","Save rejected: check entities, units, daily counter confirmation and refresh. ")+(error.code||"");}finally{save.disabled=false;}});
          form.append(choices,list,add,save,message);draw();content.append(form);
        }
        content.append(this._node("h3",this._t("Journal des notifications","Notification journal")),this._button(this._t("Actualiser le journal","Refresh journal"),load));
        for(const item of [...(data.journal||[])].reverse()){content.append(this._node("p",new Date(item.time).toLocaleString(this._hass.language,{timeZone:this._snapshotData.time_zone})+" · "+(item.label||item.rule_id)+" · "+item.message+" · "+({sent:this._t("Envoyée","Sent"),failed:this._t("Échec d’envoi : vérifier le service","Send failed: check service"),pending:this._t("Envoi non confirmé","Send unconfirmed")}[item.status]||item.status),"note"));}
        if(!data.journal?.length)content.append(this._node("p",this._t("Aucune notification émise.","No notifications sent."),"note"));
      }catch{content.textContent=this._t("Alertes indisponibles : actualisez après le rechargement de l’intégration.","Alerts unavailable: refresh after integration reload.");}
    };queueMicrotask(load);return root;
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
      if (event.shiftKey && event.key === "Enter") { event.preventDefault(); this._edit(entity); }
      else if ((event.key === "Enter" || event.key === " ") && event.target===element) {event.preventDefault();this._openHistory([entity]);}
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

}
if (globalThis.customElements && !customElements.get(PANEL_TAG)) {
  customElements.define(PANEL_TAG, EhomeEmsPanel);
}
