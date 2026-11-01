"""Install the frontend matching the already installed HA test engine."""
import json
from pathlib import Path
import subprocess
import sys
import homeassistant

components = Path(homeassistant.__file__).parent / "components"
requirements = []
# Frontend device metadata also imports these standard entity domains.
for domain in ("frontend", "ffmpeg", "infrared", "radio_frequency", "conversation", "camera", "stream", "tts", "hassio"):
    manifest = components / domain / "manifest.json"
    if manifest.exists():
        requirements.extend(json.loads(manifest.read_text()).get("requirements", []))
command = (["uv", "pip", "install", "--python", sys.executable] if "--uv" in sys.argv else
           [sys.executable, "-m", "pip", "install"])
subprocess.run([*command, *dict.fromkeys(requirements)], check=True)
