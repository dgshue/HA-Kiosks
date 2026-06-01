#!/usr/bin/env python3
"""
Push config to ESPHome dashboard - first tries to upload our config via HTTP,
then compiles and uploads to device.
"""

import asyncio
import sys
from pathlib import Path

import aiohttp
from esphome_dashboard_api import ESPHomeDashboardAPI


async def try_save_config(session: aiohttp.ClientSession, dashboard_url: str, config_path: Path) -> bool:
    """Try to save config to dashboard via HTTP if endpoint exists."""
    config_content = config_path.read_text(encoding="utf-8")
    config_name = "living-room-kiosk.yaml"
    
    # Try common dashboard save endpoints
    endpoints_to_try = [
        ("PUT", f"json-config?configuration={config_name}", {"data": config_content}),
        ("POST", "save-config", {"configuration": config_name, "content": config_content}),
        ("POST", "config", {"configuration": config_name, "content": config_content}),
    ]
    
    for method, path, payload in endpoints_to_try:
        try:
            if method == "PUT":
                resp = await session.put(
                    f"{dashboard_url}/{path}",
                    data=config_content if "data" in payload else None,
                    headers={"Content-Type": "text/yaml"} if "data" in payload else {},
                )
            else:
                resp = await session.post(f"{dashboard_url}/{path}", json=payload)
            if resp.status in (200, 201, 204):
                print(f"Config saved via {method} {path}")
                return True
        except Exception as e:
            continue
    return False


async def main():
    dashboard_url = "http://192.168.1.15:6052"
    config_path = Path(__file__).parent / "LivingRoom" / "kiosk-living-room-combined.yaml"
    config_name = "living-room-kiosk.yaml"

    async with aiohttp.ClientSession() as session:
        api = ESPHomeDashboardAPI(dashboard_url, session)

        def log_line(line: str) -> None:
            print(line, end="")

        try:
            # Try to upload our config first
            if config_path.exists():
                print("Attempting to sync config to dashboard...")
                saved = await try_save_config(session, dashboard_url, config_path)
                if not saved:
                    print("Could not sync config via API - dashboard may use different config.")
                    print("Ensure config is synced (e.g. via HA File Editor or sync-config-to-dashboard.py)")
                    print()

            # Get devices
            devices = await api.get_devices()
            configured = devices.get("configured", [])
            config_names = [d["configuration"] for d in configured]
            print(f"Configured devices: {config_names}")

            if config_name not in config_names:
                for alt in ("living-room-kiosk", "kiosk-living-room-combined.yaml"):
                    if alt in config_names:
                        config_name = alt
                        print(f"Using config: {config_name}")
                        break
                else:
                    print(f"Config '{config_name}' not in dashboard.")
                    sys.exit(1)

            print(f"\nCompiling {config_name}...")
            ok = await api.compile(config_name, line_received_cb=log_line)
            if not ok:
                print("\nCompile failed!")
                sys.exit(1)

            print("\nCompile OK. Uploading...")
            device = next(
                (d for d in configured if d["configuration"] == config_name), None
            )
            port = device["address"] if device else "living-room-kiosk.local"
            ok = await api.upload(config_name, port, line_received_cb=log_line)
            if not ok:
                print("\nUpload failed!")
                sys.exit(1)

            print("\nUpload complete!")
        except aiohttp.ClientError as e:
            print(f"Connection error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
