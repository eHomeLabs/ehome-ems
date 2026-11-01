# eHome EMS b12 — design QA

Final result: passed after the corrections below.

## Scope and evidence

Compared the supplied b11 screenshots and target cards against the running b12 fixture at 1440×1600 and 390×844 CSS pixels. Evidence in artifacts/panel includes desktop/mobile, flow-day, flow-night, Today, loads, storage, two batteries and add-appliance modal captures. The cloud preview was also checked interactively. HA theme and source values intentionally differ from the references.

## Corrections checked

- Values use at most two decimals without rounding the underlying calculations. Today no longer overflows with long fractional energy values.
- Power history uses an unfilled smooth line through five-minute averages, with explicit averaging labels and preserved unavailable gaps.
- Navigation places Mes Appareils second, Historique fifth and Configuration last. The editable-copy button is removed.
- Appliance creation/edit/removal and scoped configuration shortcuts open accessible in-panel forms. Mobile forms have sticky save/cancel actions. Server validation preserves unrelated mappings and stable equipment identifiers; readers cannot change settings.
- EV charging has a large purple charging-station visual matching the cumulus card hierarchy. Unavailable vessel values use a readable smaller red label.
- Valid diagnostics are green and unavailable readings red. Grid import is red, export blue, with separately measured directions retained and animation starting at 10 W.
- Day and night houses preserve the same transparent 2:1 canvas, architecture and layout bounds. Clock checks cover exactly 07:00 and 19:00 in the HA timezone, including DST. A timer updates the scene even without new sensor readings.
- Today includes apparent autonomy/self-consumption with visible formulas and assumptions, plus import/export energies and shares. Missing or inconsistent inputs never become invented percentages.
- A background settings refresh does not close an open form. Bounded retries allow mirror creation to settle after an integration reload.

## Validation

132 Python unit tests and 13 frontend unit tests pass. The Chromium desktop/mobile suite covers navigation, direct CRUD, source remapping, diagnostics colors, two batteries, animation thresholds, reduced motion, day/night assets and unchanged house bounds. Real Home Assistant checks pass on 2026.9.1 and 2026.11.0b0, including administrator permissions, optimistic revision checks, stable IDs and no device service calls during settings changes.

## Intentional limits

Daily energy periods remain explicitly selected by the user; a cumulative counter cannot truthfully produce a daily cost. Ratios are apparent energy-balance indicators: grid charging, stock variation and battery export can bias them. No physical charger, battery or router commands are sent. Physical Android/RPi performance remains a hardware check for the user.
