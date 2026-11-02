"""Build and verify a deterministic integration ZIP; no secrets or local caches."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components/ehome_ems"


def main():
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())
    assert manifest["domain"] == "ehome_ems"
    version = manifest["version"]
    assert f'VERSION = "{version}"' in (INTEGRATION / "const.py").read_text()
    assert f'UI_VERSION = "{version}"' in (INTEGRATION / "frontend/ehome-panel.mjs").read_text()
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    archive = output / f"ehome-ems-{version}.zip"
    sources = sorted(path for path in INTEGRATION.rglob("*")
                     if path.is_file() and not path.is_symlink()
                     and "__pycache__" not in path.parts
                     and path.suffix in {".py", ".json", ".yaml", ".png", ".svg", ".mjs", ".webp"})
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sources:
            name = path.relative_to(ROOT).as_posix()
            entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            zipped.writestr(entry, path.read_bytes())
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert len(zipped.namelist()) == len(sources)
        assert all(name.startswith("custom_components/ehome_ems/") and ".." not in name.split("/")
                   for name in zipped.namelist())
        packaged = json.loads(zipped.read("custom_components/ehome_ems/manifest.json"))
        assert packaged == manifest
        for required in ("__init__.py", "config_flow.py", "sensor.py", "dashboard.py", "home_balance.py", "usage.py",
                         "panel.py", "manual_control.py", "photovoltaic.py", "f1atb.py", "f1atb_http.py", "f1atb_runtime.py", "f1atb_sensor.py", "source_editor.py", "settings.py", "simulation.py", "frontend/ehome-panel.mjs",
                         "brand/icon.png", "brand/icon@2x.png",
                         "frontend/assets/house.webp", "frontend/assets/house-day.webp",
                         "dashboard_service.py", "services.yaml", "strings.json",
                         "translations/fr.json", "translations/en.json"):
            assert f"custom_components/ehome_ems/{required}" in zipped.namelist(), required
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / f"{archive.name}.sha256").write_text(f"{digest}  {archive.name}\n")
    print(f"Verified {archive.name}: {len(sources)} files; sha256={digest}")


if __name__ == "__main__":
    main()
