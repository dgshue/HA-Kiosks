#!/usr/bin/env python3
"""
Copy local ESPHome config to Home Assistant dashboard config folder.
Run this before pushing to deploy our changes to the dashboard.

The ESPHome dashboard uses /config/esphome/ (inside Home Assistant).
Adjust DEST_PATH for your setup.
"""

import shutil
import sys
from pathlib import Path

# Source: our repo config
SOURCE = Path(__file__).parent / "LivingRoom" / "kiosk-living-room-combined.yaml"

# Destination: Home Assistant config folder
# Common paths - edit for your setup:
# - Docker: /config/esphome/living-room-kiosk.yaml (copy into container)
# - HA OS: /config in the config folder
# - Windows: C:\\Users\\...\\home-assistant\\config\\esphome\\
DEST_PATH = Path.home() / "home-assistant" / "config" / "esphome" / "living-room-kiosk.yaml"
# Alternative: use env var
# DEST_PATH = Path(os.environ.get("HA_CONFIG", "~/home-assistant/config")) / "esphome" / "living-room-kiosk.yaml"


def main():
    if not SOURCE.exists():
        print(f"Source not found: {SOURCE}")
        sys.exit(1)

    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else DEST_PATH
    dest = dest.expanduser().resolve()

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, dest)
    print(f"Copied config to {dest}")
    print("Now run: python push-to-dashboard.py")


if __name__ == "__main__":
    main()
