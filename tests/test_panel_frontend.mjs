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
