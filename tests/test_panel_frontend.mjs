import test from "node:test";
import assert from "node:assert/strict";
import { createIndependentCopy, reading, newCopyToken, flowPower, flowActive } from "../custom_components/ehome_ems/frontend/ehome-panel.mjs";

test("10 W animation threshold preserves low readings and handles kW", () => {
  for (const [value, unit, active] of [[0,"W",false],[1,"W",false],[9.99,"W",false],[10,"W",true],[11,"W",true],[0.009,"kW",false],[0.01,"kW",true],["unavailable","W",false]]) {
    const states={a:{state:String(value),attributes:{unit_of_measurement:unit}}};
    assert.equal(flowActive(states,"a"),active);
    assert.equal(reading(states,"a").text,value==="unavailable"?"Indisponible":`${new Intl.NumberFormat("fr",{maximumFractionDigits:2,useGrouping:false}).format(value)} ${unit}`);
  }
});

test("flow rejects unknown units, missing and negative power without inventing zero", () => {
  assert.equal(flowPower({a:{state:"1.5",attributes:{unit_of_measurement:"kW"}}},"a"),1500);
  for (const state of ["unknown","unavailable","-20","NaN"]) assert.equal(flowPower({a:{state,attributes:{unit_of_measurement:"W"}}},"a"),null);
  assert.equal(flowPower({a:{state:"20",attributes:{unit_of_measurement:"kWh"}}},"a"),null);
  assert.equal(flowPower({},"a"),null);
});

test("copy creates a new native dashboard then saves only that path", async () => {
  const calls = [];
  const dashboard = { title: "EMS", views: [{ cards: [] }] };
  const hass = { callWS: async command => { calls.push(command); return { id: "new" }; } };
  const path = await createIndependentCopy(hass, dashboard, "unique-123");
  assert.equal(path, "ehome-ems-copy-unique-123");
  assert.equal(calls[0].type, "lovelace/dashboards/create");
  assert.equal(calls[0].require_admin, true);
  assert.equal(calls[1].type, "lovelace/config/save");
  assert.equal(calls[1].url_path, path);
  calls[1].config.views.length = 0;
  assert.equal(dashboard.views.length, 1);
});

test("collision never saves to an existing dashboard", async () => {
  const calls = [];
  const hass = { callWS: async command => { calls.push(command); throw new Error("already exists"); } };
  await assert.rejects(createIndependentCopy(hass, {}, "collision"));
  assert.equal(calls.length, 1);
  assert.equal(calls[0].type, "lovelace/dashboards/create");
});

test("save failure reports the new empty copy and never deletes anything", async () => {
  const calls = [];
  const hass = { callWS: async command => {
    calls.push(command);
    if (calls.length === 2) throw new Error("disconnected");
    return { id: "new" };
  } };
  await assert.rejects(createIndependentCopy(hass, {}, "new"), error =>
    error.createdPath === "ehome-ems-copy-new");
  assert.equal(calls.length, 2);
  assert.ok(calls.every(call => !call.type.includes("delete")));
});

test("unavailable and unknown values are not zero or a numeric gauge", () => {
  for (const state of ["unavailable", "unknown"]) {
    assert.deepEqual(reading({ "sensor.a": { state } }, "sensor.a"), { text: "Indisponible", number: null });
  }
  assert.equal(reading({}, "sensor.a").number, null);
  assert.equal(reading({ "sensor.a": { state: "0", attributes: { unit_of_measurement: "W" } } }, "sensor.a").text, "0 W");
});

test("signed readings and raw statuses keep their meaning", () => {
  assert.equal(reading({ a: { state: "-250", attributes: { unit_of_measurement: "W" } } }, "a").number, -250);
  assert.equal(reading({ a: { state: "charging", attributes: {} } }, "a").number, null);
  assert.equal(reading({ a: { state: "charging", attributes: {} } }, "a").text, "charging");
});

test("copy identifiers cannot inject paths or overwrite the default dashboard", async () => {
  const hass = { callWS: () => assert.fail("must not call WS") };
  await assert.rejects(createIndependentCopy(hass, {}, "../lovelace"));
});

test("LAN HTTP can create unique copy tokens without secure-context randomUUID", () => {
  assert.match(newCopyToken({ getRandomValues: values => values.fill(42) }), /^[a-f0-9]{32}$/);
});

test("history preserves unknown gaps and rejects empty or reversed samples", async () => {
  const {historySegments}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");
  const at=(minute,state)=>({last_changed:new Date(Date.UTC(2026,0,1,0,minute)).toISOString(),state});
  assert.deepEqual(historySegments([at(0,"1"),at(1,""),at(2,"3")]).map(s=>s.length),[1,1]);
  assert.deepEqual(historySegments([at(0,"1"),at(1,"2"),at(2,"unavailable"),at(3,"4"),at(4,"5")]).map(s=>s.length),[2,2]);
  assert.equal(historySegments([at(0,"NaN"),at(1,"unknown")]).length,0);
});

test("two-decimal formatting changes labels only, not numeric calculation",async()=>{
  const {displayNumber}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");
  const source={a:{state:"0.08158396670277",attributes:{unit_of_measurement:"kWh"}}};
  assert.equal(reading(source,"a").text,"0,08 kWh");
  assert.equal(reading(source,"a").number,0.08158396670277);
  assert.equal(displayNumber(8.176,"en"),"8.18");
});
test("house changes exactly at 07 and 19 in the HA timezone including DST",async()=>{
  const {houseMode}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");
  for(const [time,mode] of [["2026-11-01T05:59:59Z","night"],["2026-11-01T06:00:00Z","day"],["2026-11-01T17:59:59Z","day"],["2026-11-01T18:00:00Z","night"],["2026-07-01T05:00:00Z","day"],["2026-07-01T17:00:00Z","night"]])assert.equal(houseMode(new Date(time),"Europe/Paris"),mode);
});
test("daily ratios handle missing, zero and physically inconsistent inputs",async()=>{
  const {dailyIndicators,curveSegments}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");
  const r=dailyIndicators({home:8.5,solar:4.1,imported:6.2,exported:.3});
  assert.ok(Math.abs(r.autonomy-27.058823529)<1e-6);assert.ok(Math.abs(r.selfConsumption-92.682926829)<1e-6);
  assert.ok(Math.abs(r.importShare+r.exportShare-100)<1e-8);
  const unavailable=dailyIndicators({home:0,solar:0,imported:0,exported:0});assert.ok(Object.values(unavailable).every(v=>v===null));
  assert.equal(dailyIndicators({home:1,solar:1,imported:2,exported:2}).selfConsumption,null);
  const t=Date.UTC(2026,0,1);const values=curveSegments([0,100,20].map((state,i)=>({state:String(state),last_changed:new Date(t+i*60000).toISOString()})));
  assert.equal(values[0].length,1);assert.equal(values[0][0].value,40);
});

test("percent readings have no decimals while keeping full calculation precision",async()=>{
 const {reading,percent}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");
 const r=reading({s:{state:"35.69",attributes:{unit_of_measurement:"%"}}},"s");assert.equal(r.text,"36 %");assert.equal(r.number,35.69);assert.equal(percent(93.47),"93");
});
test("15 minute trend arrows cover 24 completed quarters and keep missing bins neutral",async()=>{
 const {quarterTrends}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");
 const end=Date.UTC(2026,10,1,12),step=900000;
 assert.equal(quarterTrends([],end).length,24);assert.ok(quarterTrends([],end).every(b=>b.direction===null));
 const data=[100,200,50,50].map((state,i)=>({state:String(state),last_changed:new Date(end-4*step+i*step).toISOString()}));
 assert.deepEqual(quarterTrends(data,end).slice(-4).map(b=>b.direction),[null,1,-1,0]);
 assert.ok(quarterTrends([{state:"123",last_changed:new Date(end-7*3600000).toISOString()}],end).every(b=>b.value===null));
});
test("daily energy from lifetime counter uses midnight baseline, units and resets",async()=>{
 const {dailyFromCounter}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");const t=Date.UTC(2026,10,1),row=(offset,state)=>({state:String(state),last_changed:new Date(t+offset).toISOString()});
 assert.equal(dailyFromCounter([row(0,1524),row(3600000,1524.5)],1524.81,"kWh",t,t+7200000),.81);
 assert.equal(dailyFromCounter([row(0,1524000)],1524810,"Wh",t,t+7200000),.81);
 assert.equal(dailyFromCounter([row(0,100),row(3600000,101),row(4000000,0),row(5000000,.3)],.5,"kWh",t,t+7200000),1.5);
 assert.equal(dailyFromCounter([row(1000,100)],101,"kWh",t,t+7200000),null);
 assert.equal(dailyFromCounter([],1524.81,"kWh",t,t+7200000),null);
 assert.equal(dailyFromCounter([row(0,100)],NaN,"kWh",t,t+7200000),null);
});
test("HA midnight follows Paris timezone including 23 and 25 hour days",async()=>{
 const {localDayStart}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");
 assert.equal(new Date(localDayStart(new Date("2026-11-01T16:00:00Z"),"Europe/Paris")).toISOString(),"2026-10-31T23:00:00.000Z");
 const day=d=>localDayStart(new Date(d),"Europe/Paris");
 assert.equal((day("2026-03-30T12:00:00Z")-day("2026-03-29T12:00:00Z"))/3600000,23);
 assert.equal((day("2026-10-26T12:00:00Z")-day("2026-10-25T12:00:00Z"))/3600000,25);
});

test("native product icons infer French names and permit explicit overrides",async()=>{const {productIcon}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");for(const [name,icon] of [["Lave Linge","washing-machine"],["Sèche Serviette","radiator"],["Filtration Piscine","pool"],["Clim Labo","air-conditioner"],["Frigo/Congélateur","fridge"],["Expresso","coffee-maker"]])assert.equal(productIcon({name}),"mdi:"+icon);assert.equal(productIcon({name:"Frigo",icon:"mdi:pool"}),"mdi:pool");assert.equal(productIcon({name:"unknown",icon:"javascript:bad"}),"mdi:power-plug");});

test("daily goal is consumed energy progress, distinct from SOC and can exceed target",async()=>{const {dailyGoalPercent}=await import("../custom_components/ehome_ems/frontend/ehome-panel.mjs");assert.ok(Math.abs(dailyGoalPercent(2.16,3)-72)<1e-9);assert.ok(Math.abs(dailyGoalPercent(4,3)-400/3)<1e-9);for(const [energy,goal] of [[null,3],[2,0],[2,-1],[2,NaN],[-1,3]])assert.equal(dailyGoalPercent(energy,goal),null);});

import {pvProductionSources, strictSum, situationFacts} from "../custom_components/ehome_ems/frontend/ehome-panel.mjs";
test("PV totals choose one production per equipment and deduplicate original sources",()=>{
 const selected=pvProductionSources([{power:"a",dc_power:"dc"},{power:"alias"},{power:"a"},{kind:"hybrid_inverter",power:"hybridAC"},{kind:"hybrid_inverter",dc_power:"hybridDC"}],id=>id==="alias"?"a":id);
 assert.deepEqual(selected.map(p=>p.production),["dc","alias","hybridDC"]);
 assert.equal(strictSum([100,0,200]),300);assert.equal(strictSum([100,null]),null);assert.equal(strictSum([]),null);assert.equal(strictSum([1,NaN]),null);
});
test("situation interprets observed flows without inferring energy origin or missing zeros",()=>{
 assert.deepEqual(situationFacts({solar:2500,home:1000,imported:0,exported:200,charge:1200,discharge:0,water:600}),["surplus","water","charge","export"]);
 assert.equal(situationFacts({solar:null,home:1000,imported:0,exported:0})[0],"incomplete");
 assert.equal(situationFacts({solar:100,home:1500,imported:1400,exported:0})[0],"import");
});

import {rankEntityOptions} from "../custom_components/ehome_ems/frontend/ehome-panel.mjs";
test("entity ordering prioritizes device names with accents without hiding other sources",()=>{
 const options=[["sensor.frigo","Frigo"],["sensor.lave_linge","Lave linge énergie"],["sensor.seche_linge_power","Sèche-linge puissance"]];
 const ranked=rankEntityOptions(options,"Seche Linge");
 assert.equal(ranked[0][0],"sensor.seche_linge_power");assert.equal(ranked.length,options.length);assert.equal(options[0][0],"sensor.frigo");
 assert.equal(rankEntityOptions(options,"").length,3);
});
