// Browser checks use only simulated data, not an authenticated user HA.
const { chromium } = require("playwright");
const http = require("node:http");
const fs = require("node:fs/promises");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "..");
const output = path.resolve(process.argv[2] || path.join(root, "artifacts/panel"));

(async () => {
  await fs.mkdir(output, { recursive: true });
  const server = http.createServer(async (request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
      const filename = path.resolve(root, "." + pathname.replace("/ehome_ems_assets/", "/custom_components/ehome_ems/frontend/assets/"));
      if (!filename.startsWith(root + path.sep)) throw new Error("outside root");
      const content = await fs.readFile(filename);
      response.setHeader("Content-Type", filename.endsWith(".webp") ? "image/webp" : filename.endsWith(".html") ? "text/html" : "text/javascript");
      response.end(content);
    } catch {
      response.statusCode = 404; response.end("Not found");
    }
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
    for (const viewport of [{ width: 1440, height: 1600 }, { width: 390, height: 844 }]) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on("pageerror", error => errors.push(error.message));
      await page.goto("http://127.0.0.1:" + server.address().port + "/tests/fixtures/panel.html");
      await page.getByRole("heading", { name: "eHome EMS", exact: true }).waitFor();
      await page.getByRole("button", { name: "Vue d’ensemble", exact: true }).waitFor();
      assert.equal(await page.evaluate(() => customElements.get("ehome-ems-panel") !== fixturePanel.constructor), true);
      const navBox = await page.getByRole("navigation", { name: "Vues énergie" }).boundingBox();
      const flowBox = await page.locator(".flow").boundingBox();
      assert.ok(navBox.y < flowBox.y);
      await page.locator(".flow-house img").evaluate(img => img.decode());
      assert.equal(await page.locator(".flow-links path.active").count(), 4);
      assert.equal(await page.evaluate(() => document.querySelector("ehome-ems-panel-0-2-0b11").shadowRoot.querySelector(".flow").scrollWidth <= innerWidth), true);
      assert.ok(await page.getByText("1500 W", { exact: true }).count());
      assert.equal(await page.evaluate(() =>
        fixturePanel.shadowRoot.querySelector("main").scrollWidth <= innerWidth), true);
      await page.screenshot({ path: path.join(output, viewport.width < 600 ? "mobile.png" : "desktop.png"), fullPage: true });
      await page.locator(".flow").screenshot({ path: path.join(output, viewport.width < 600 ? "flow-mobile.png" : "flow-desktop.png") });
      // Reproduce the hardware report: idle storage has two visible zero rows,
      // an existing home source and an EV consuming 1 W without charging.
      await page.evaluate(() => {
        window.beforeNight={states:structuredClone(fixtureHass.states),flow:structuredClone(fixtureFlow)};
        fixtureFlow.home_calculated=false;
        fixtureFlow.batteries[0].name="Zendure SolarFlow 2400 AC+";
        for(const [id,value] of Object.entries({pv:0,import:731,export:0,home:731,charge:0,discharge:0,soc:10,cumulus:0,ev:1}))
          fixtureHass.states["sensor."+id]={...fixtureHass.states["sensor."+id],state:String(value)};
        fixturePanel.hass={...fixtureHass};
      });
      await page.getByRole("button",{name:"Actualiser",exact:true}).click();
      await page.getByText("Maison · source existante",{exact:true}).first().waitFor();
      await page.waitForFunction(() => {
        const shadow=fixturePanel.shadowRoot;
        return shadow.querySelector(".flow-usage-title").getBoundingClientRect().top >=
          shadow.querySelector(".flow-battery").getBoundingClientRect().bottom + 8;
      });
      await page.waitForFunction(() => {const r=fixturePanel.shadowRoot;return r.querySelector(".home-outgoing").getBoundingClientRect().top >= r.querySelector(".flow-house").getBoundingClientRect().bottom + 8;});
      assert.equal(await page.locator(".flow-links path.active").count(),2);
      assert.equal(await page.locator(".flow-branches path.active").count(),0);
      assert.ok(await page.locator(".flow-usages").getByText("1 W",{exact:true}).count());
      await page.locator(".flow").screenshot({path:path.join(output,viewport.width<600?"idle-mobile.png":"idle-desktop.png")});
      for(const value of [9.99,10,1]) {
        await page.evaluate(value => {fixtureHass.states["sensor.ev"].state=String(value);fixturePanel.hass={...fixtureHass};},value);
        assert.equal(await page.locator(".flow-branches path.active").count(),value>=10?1:0);
      }
      await page.evaluate(() => {fixtureHass.states=beforeNight.states;Object.assign(fixtureFlow,beforeNight.flow);fixturePanel.hass={...fixtureHass};});
      await page.getByRole("button",{name:"Actualiser",exact:true}).click();
      await page.waitForFunction(() => fixturePanel.shadowRoot.querySelectorAll(".flow-links path.active").length===4);
      const editable = page.getByRole("button", { name: "Modifier la source de Production solaire", exact: true }).first();
      await editable.dispatchEvent("pointerdown", { button: 0, clientX: 20, clientY: 20, pointerType: "touch" });
      await page.getByRole("dialog", { name: "Changer la source", exact: true }).waitFor();
      await page.screenshot({ path: path.join(output, viewport.width < 600 ? "editor-mobile.png" : "editor-desktop.png"), fullPage: true });
      await editable.dispatchEvent("pointerup", { button: 0 });
      await page.getByRole("searchbox", { name: "Rechercher un capteur", exact: true }).fill("alternative");
      await page.getByRole("listbox", { name: "Nouvelle source", exact: true }).selectOption("sensor.pv_alternative");
      await page.getByRole("button", { name: "Enregistrer la source", exact: true }).click();
      await page.getByRole("dialog").waitFor({ state: "detached" });
      assert.ok(await page.getByText("2000 W", { exact: true }).count());
      const remap = await page.evaluate(() => calls.find(call => call.type==="ehome_ems/remap_source"));
      assert.equal(remap.expected_source, "sensor.pv_source");
      assert.equal(remap.source_id, "sensor.pv_alternative");
      await page.evaluate(() => {
        fixtureHass.states["sensor.pv"] = { state: "unavailable",
          attributes: { unit_of_measurement: "W", friendly_name: "Production solaire" } };
        fixturePanel.hass = { ...fixtureHass };
      });
      assert.ok(await page.getByText("Indisponible", { exact: true }).count());
      assert.equal(await page.locator(".flow-solar").getByText("Indisponible", { exact: true }).count(), 1);
      assert.equal(await page.locator(".flow-links path.active").count(), 3);
      await page.emulateMedia({ reducedMotion: "reduce" });
      assert.equal(await page.locator(".flow-links path.active").first().evaluate(el => getComputedStyle(el).animationName), "none");
      await page.getByRole("button", { name: "Stockage", exact: true }).click();
      assert.equal(await page.getByText("18 %", { exact: true }).count(), 1);
      await page.getByRole("button", { name: "Historique", exact: true }).click();
      await page.evaluate(() => fixturePanel.addEventListener("hass-more-info",
        event => window.moreInfoEntity = event.detail.entityId));
      await page.getByRole("button", { name: "Production solaire", exact: true }).click();
      assert.equal(await page.evaluate(() => window.moreInfoEntity), "sensor.pv");
      await page.getByRole("button", { name: "Créer une copie modifiable", exact: true }).evaluate(button => {
        button.click(); button.click();
      });
      await page.getByRole("link", { name: "Ouvrir la copie", exact: true }).waitFor();
      const calls = await page.evaluate(() => window.calls);
      assert.equal(calls.filter(call => call.type === "lovelace/dashboards/create").length, 1);
      assert.equal(calls.filter(call => call.type === "lovelace/config/save").length, 1);
      assert.equal(calls.filter(call => call.type === "call_service").length, 0);
      await page.getByRole("button", { name: "Stratégie", exact: true }).click();
      assert.equal(await page.getByText("Aucune commande envoyée", { exact: true }).count(), 1);
      await page.getByRole("checkbox",{name:"Inclure Zendure",exact:true}).check();
      await page.getByRole("spinbutton",{name:"Plafond (W) · Zendure",exact:true}).fill("1000");
      assert.equal(await page.getByRole("button",{name:"Simuler ce budget",exact:true}).isDisabled(),true);
      await page.getByRole("button",{name:"Monter · Cumulus",exact:true}).click();
      await page.getByRole("button",{name:"Enregistrer les priorités de simulation",exact:true}).click();
      await page.getByText("Priorités de simulation enregistrées. Aucun équipement modifié.",{exact:true}).waitFor();
      const priorities=await page.evaluate(()=>calls.find(call=>call.type==="ehome_ems/save_simulation").targets);
      assert.deepEqual(priorities.map(t=>t.id),["usage:b","battery:a","usage:c"]);
      assert.equal(priorities[1].max_w,1000);
      await page.getByRole("spinbutton",{name:"Budget hypothétique à répartir (W)",exact:true}).fill("1500");
      await page.getByRole("button",{name:"Simuler ce budget",exact:true}).click();
      await page.locator(".scenario-result").first().getByText("Budget : 1500 W · Alloué : 1000 W · Non alloué : 500 W",{exact:true}).waitFor();
      await page.locator(".simulation-editor").screenshot({path:path.join(output,viewport.width<600?"simulation-editor-mobile.png":"simulation-editor-desktop.png")});
      await page.locator(".scenario-result").first().screenshot({path:path.join(output,viewport.width<600?"simulation-result-mobile.png":"simulation-result-desktop.png")});
      assert.equal(await page.evaluate(()=>calls.some(call=>call.type==="call_service")),false);
      await page.getByRole("button", { name: "Configuration", exact: true }).click();
      assert.ok(await page.getByText("Interface 0.2.0b11 · Intégration 0.2.0b11", { exact: true }).count());
      await page.getByRole("button", { name: "Changer la source", exact: true }).first().click();
      await page.getByRole("dialog").waitFor();
      await page.getByRole("button", { name: "Annuler", exact: true }).click();
      await page.getByRole("button",{name:"Mes Appareils",exact:true}).click();
      await page.getByText("Frigo",{exact:true}).waitFor();
      assert.ok(await page.getByText(/0,17.*aujourd’hui.*estimation/).count());
      assert.equal(await page.getByRole("heading",{name:"Cumulus",exact:true}).count(),0);
      await page.screenshot({path:path.join(output,viewport.width<600?"appliances-mobile.png":"appliances-desktop.png"),fullPage:true});
      await page.getByRole("button",{name:"Aujourd’hui",exact:true}).click();
      await page.getByText("J’ai produit",{exact:true}).waitFor();
      assert.ok(await page.getByText("2.1 kWh",{exact:true}).count());
      await page.screenshot({path:path.join(output,viewport.width<600?"today-mobile.png":"today-desktop.png"),fullPage:true});
      await page.getByRole("button",{name:"Stockage",exact:true}).click();
      await page.getByRole("heading",{name:"Aferiy",exact:true}).waitFor();
      assert.ok(await page.getByText("51 °C",{exact:true}).count());
      await page.locator(".stack").first().screenshot({path:path.join(output,viewport.width<600?"storage-mobile.png":"storage-desktop.png")});
      await page.evaluate(() => {fixtureFlow.batteries[1].role="active";});
      await page.getByRole("button",{name:"Actualiser",exact:true}).click();
      await page.getByRole("button",{name:"Vue d’ensemble",exact:true}).click();
      assert.equal(await page.locator(".flow-battery").count(),2);
      await page.waitForFunction(()=>{const r=fixturePanel.shadowRoot;return r.querySelectorAll(".flow-battery")[1].getBoundingClientRect().top>=r.querySelectorAll(".flow-battery")[0].getBoundingClientRect().bottom+8;});
      assert.equal(await page.evaluate(()=>fixturePanel.shadowRoot.querySelector("main").scrollWidth<=innerWidth),true);
      await page.screenshot({path:path.join(output,viewport.width<600?"two-batteries-mobile.png":"two-batteries-desktop.png"),fullPage:true});
      await page.evaluate(()=>{fixtureFlow.batteries[1].role="backup";});
      await page.evaluate(() => { window.omitFlow = true; });
      await page.getByRole("button", { name: "Actualiser", exact: true }).click();
      await page.getByRole("button", { name: "Vue d’ensemble", exact: true }).click();
      await page.getByRole("alert").getByText("Flux indisponible dans cette version chargée").waitFor();
      await page.evaluate(() => { fixtureHass.user = { is_admin: false }; fixturePanel.hass = { ...fixtureHass }; });
      assert.equal(await page.getByRole("button", { name: "Créer une copie modifiable", exact: true }).count(), 0);
      await page.getByRole("button", { name: "Stratégie", exact: true }).click();
      assert.equal(await page.getByRole("button",{name:"Enregistrer les priorités de simulation",exact:true}).count(),0);
      assert.equal(await page.getByRole("checkbox",{name:"Inclure Zendure",exact:true}).isDisabled(),true);
      assert.deepEqual(errors, []);
      await page.close();
    }
    console.log("PASS: desktop/mobile rendering, unavailable values, tabs, history event and guarded native copy");
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
