# eHome EMS — Codex instructions

Develop a local-first, vendor-neutral residential energy management system.

- Home Assistant is an optional source adapter, not the core.
- V1 is read-only: no commands to real devices.
- Never commit credentials, access tokens, private URLs or actual entity inventories.
- Develop with simulated data and automated tests.
- Normalize power (W), energy (Wh), SOC (%), timestamps, source and data quality.
- Explicitly distinguish grid import/export and battery charge/discharge.
- Prevent double-counting overlapping measurements.
- Indicate stale and unavailable measurements in the UI.
- Keep the interface responsive, accessible, and in French.
- Proposed stack: Python/FastAPI backend, React/TypeScript frontend, SQLite initially.
- Prefer small changes, tests, documentation, and pull requests.
- Never alter a real Home Assistant instance without explicit authorization.
