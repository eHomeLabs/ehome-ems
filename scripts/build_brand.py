"""Render the existing eHome EMS vector symbol for HA's local brand endpoint."""
from pathlib import Path
import cairosvg

folder = Path(__file__).resolve().parents[1] / "custom_components/ehome_ems/brand"
for filename, size in (("icon.png", 256), ("icon@2x.png", 512)):
    cairosvg.svg2png(url=str(folder / "icon.svg"), write_to=str(folder / filename),
                    output_width=size, output_height=size)
    print(f"{filename}: {size}x{size}")
