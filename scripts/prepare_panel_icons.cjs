// Test-only adapter: production uses Home Assistant's ha-icon and bundled MDI.
const fs = require("node:fs");
const mdi = require("@mdi/js");
fs.writeFileSync("tests/fixtures/mdi.json", JSON.stringify({
  "mdi:white-balance-sunny": mdi.mdiWhiteBalanceSunny,
  "mdi:transmission-tower": mdi.mdiTransmissionTower,
  "mdi:battery-high": mdi.mdiBatteryHigh,
  "mdi:battery-outline": mdi.mdiBatteryOutline,
  "mdi:battery": mdi.mdiBattery,
  "mdi:water-boiler": mdi.mdiWaterBoiler,
  "mdi:car-electric": mdi.mdiCarElectric,
  "mdi:power-plug": mdi.mdiPowerPlug,
  "mdi:home": mdi.mdiHome,
  "mdi:battery-charging": mdi.mdiBatteryCharging,
}));
