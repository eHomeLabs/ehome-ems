// Test-only adapter: production uses Home Assistant's ha-icon and bundled MDI.
const fs = require("node:fs");
const mdi = require("@mdi/js");
fs.writeFileSync("tests/fixtures/mdi.json", JSON.stringify({
  "mdi:washing-machine": mdi.mdiWashingMachine,
  "mdi:dishwasher": mdi.mdiDishwasher,
  "mdi:tumble-dryer": mdi.mdiTumbleDryer,
  "mdi:fridge": mdi.mdiFridge,
  "mdi:radiator": mdi.mdiRadiator,
  "mdi:air-conditioner": mdi.mdiAirConditioner,
  "mdi:pool": mdi.mdiPool,
  "mdi:coffee-maker": mdi.mdiCoffeeMaker,
  "mdi:printer-3d-nozzle": mdi.mdiPrinter3dNozzle,
  "mdi:lightbulb": mdi.mdiLightbulb,
  "mdi:television": mdi.mdiTelevision,
  "mdi:desktop-classic": mdi.mdiDesktopClassic,
  "mdi:white-balance-sunny": mdi.mdiWhiteBalanceSunny,
  "mdi:transmission-tower": mdi.mdiTransmissionTower,
  "mdi:battery-high": mdi.mdiBatteryHigh,
  "mdi:battery-outline": mdi.mdiBatteryOutline,
  "mdi:battery": mdi.mdiBattery,
  "mdi:water-boiler": mdi.mdiWaterBoiler,
  "mdi:car-electric": mdi.mdiCarElectric,
  "mdi:ev-station": mdi.mdiEvStation,
  "mdi:power-plug": mdi.mdiPowerPlug,
  "mdi:home": mdi.mdiHome,
  "mdi:battery-charging": mdi.mdiBatteryCharging,
}));
