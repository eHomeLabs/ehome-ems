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
    browser = await chromium.launch({ executablePath: chromium.executablePath(), headless: true, args: ["--no-sandbox"] });
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on("pageerror", error => errors.push(error.message));
      await page.goto("http://127.0.0.1:" + server.address().port + "/tests/fixtures/panel.html");
      await page.getByRole("heading", { name: "eHome EMS", exact: true }).waitFor();
      await page.getByRole("button", { name: "Synthèse", exact: true }).waitFor();
      await page.locator(".flow-house img").evaluate(img => img.decode());
      assert.equal(await page.locator(".flow-links path.active").count(), 4);
      assert.equal(await page.evaluate(() => document.querySelector("ehome-ems-panel").shadowRoot.querySelector(".flow").scrollWidth <= innerWidth), true);
      assert.ok(await page.getByText("1500 W", { exact: true }).count());
      assert.equal(await page.evaluate(() =>
        fixturePanel.shadowRoot.querySelector("main").scrollWidth <= innerWidth), true);
      await page.screenshot({ path: path.join(output, viewport.width < 600 ? "mobile.png" : "desktop.png"), fullPage: true });
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
      assert.equal(await page.locator("progress").first().isHidden(), true);
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
      await page.evaluate(() => { fixtureHass.user = { is_admin: false }; fixturePanel.hass = { ...fixtureHass }; });
      assert.equal(await page.getByRole("button", { name: "Créer une copie modifiable", exact: true }).count(), 0);
      assert.deepEqual(errors, []);
      await page.close();
    }
    console.log("PASS: desktop/mobile rendering, unavailable values, tabs, history event and guarded native copy");
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
