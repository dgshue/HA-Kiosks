#!/usr/bin/env python3
"""Push ESPHome config to Living Room Kiosk via Dashboard API."""

import asyncio
import sys
from pathlib import Path

import aiohttp
from esphome_dashboard_api import ESPHomeDashboardAPI


async def save_config_to_dashboard(session: aiohttp.ClientSession, dashboard_url: str) -> bool:
    """Upload our local config to the dashboard before compiling."""
    config_path = Path(__file__).parent / "LivingRoom" / "kiosk-living-room-combined.yaml"
    if not config_path.exists():
        return False
    config_content = config_path.read_text(encoding="utf-8")
    try:
        r = await session.post(
            f"{dashboard_url}/edit",
            params={"configuration": "living-room-kiosk.yaml"},
            data=config_content,
            headers={"Content-Type": "application/yaml"},
        )
        return r.status == 200
    except Exception:
        return False


async def main():
    dashboard_url = "http://192.168.1.15:6052"
    config_name = "living-room-kiosk.yaml"

    async with aiohttp.ClientSession() as session:
        api = ESPHomeDashboardAPI(dashboard_url, session)

        def log_line(line: str) -> None:
            try:
                print(line, end="", flush=True)
            except UnicodeEncodeError:
                print(line.encode("ascii", "replace").decode(), end="", flush=True)

        try:
            # Sync our config to dashboard first
            if await save_config_to_dashboard(session, dashboard_url):
                print("Config synced to dashboard.")

            # Get devices to find current config names
            devices = await api.get_devices()
            configured = devices.get("configured", [])
            config_names = [d["configuration"] for d in configured]
            print(f"Configured devices: {config_names}")

            # Use living-room-kiosk.yaml or kiosk-living-room-combined.yaml
            if config_name not in config_names:
                for alt in ("living-room-kiosk", "kiosk-living-room-combined.yaml"):
                    if alt in config_names:
                        config_name = alt
                        print(f"Using config: {config_name}")
                        break
                else:
                    print(
                        f"Config '{config_name}' not in dashboard. "
                        f"Add LivingRoom/kiosk-living-room-combined.yaml in dashboard first."
                    )
                    sys.exit(1)

            print(f"\nCompiling {config_name}...")
            ok = await api.compile(config_name, line_received_cb=log_line)
            if not ok:
                print("\nCompile failed!")
                sys.exit(1)

            print("\nCompile OK. Uploading...")
            # For OTA, port is typically the device hostname or IP
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
