"""Read-only GATT service/characteristic diagnostic for Muse S Athena on Windows.

Usage: python tools/diagnose_muse_gatt.py --name MuseS-C87B
Install the optional dependency first: python -m pip install bleak
"""
from __future__ import annotations

import argparse
import asyncio
import sys

EXPECTED_SERVICE = "0000fe8d-0000-1000-8000-00805f9b34fb"
EXPECTED_CONTROL = "273e0001-4c4d-454d-96be-f03bac821358"


async def inspect(name: str, timeout: float) -> int:
    try:
        from bleak import BleakClient, BleakScanner
    except ImportError:
        print("Install 'bleak' in the project .venv to run read-only GATT diagnostics.", file=sys.stderr)
        return 2

    print(f"Scanning for BLE name {name!r} for {timeout:g} seconds...")
    discovered = await BleakScanner.discover(timeout=timeout)
    matches = [device for device in discovered if device.name == name]
    if len(matches) != 1:
        print(f"Expected one device named {name!r}; detected {len(matches)}. Check power, competing apps and Bluetooth pairing.")
        return 2
    device = matches[0]
    # Intentionally avoid printing device MAC/address in logs.
    print(f"Found named device {name!r}. Connecting to inspect GATT only...")
    async with BleakClient(device, timeout=timeout) as client:
        services = client.services
        service_uuids = {str(s.uuid).lower() for s in services}
        control_uuids = {str(c.uuid).lower() for service in services for c in service.characteristics}
        print("GATT service UUIDs:")
        for uuid in sorted(service_uuids):
            print(" ", uuid)
        print("Expected Athena FE8D service:", EXPECTED_SERVICE in service_uuids)
        print("Expected Athena control characteristic:", EXPECTED_CONTROL in control_uuids)
        print("No commands or notifications were sent.")
        return 0 if EXPECTED_SERVICE in service_uuids and EXPECTED_CONTROL in control_uuids else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Muse S Athena GATT inspection")
    parser.add_argument("--name", default="MuseS-C87B", help="Exact advertised BLE name")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()
    try:
        return asyncio.run(inspect(args.name, args.timeout))
    except Exception as exc:
        print(f"BLE GATT enumeration failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
