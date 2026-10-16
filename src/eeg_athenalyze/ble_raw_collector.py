"""Opt-in raw BLE notification capture for Muse S Athena.

Never automatically run this in CI. Not an EEG decoder or timing validator.
No commands are sent unless explicitly requested via --start-stream.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
from pathlib import Path
import time

from eeg_athenalyze.ble_notification_qc import SENSOR_SUFFIXES

CONTROL_UUID = "273e0001-4c4d-454d-96be-f03bac821358"
ALLOWED_PRESETS = ("p21", "p1035", "p1041")


def frame_control_command(command: str) -> bytes:
    """BrainFlow/BlueMuse length-prefixed ASCII command with terminal LF."""
    if command not in {"v6", "s", "h", "dc001", "L1", *ALLOWED_PRESETS}:
        raise ValueError("Unapproved device command")
    encoded = command.encode("ascii") + b"\n"
    return bytes((len(encoded),)) + encoded


async def collect(
    output: Path, *, name: str, duration: float = 60.0,
    discovery_timeout: float = 20.0, start_stream: bool = False,
    preset: str = "p21", low_latency: bool = False,
    bleak_client=None, bleak_scanner=None,
) -> dict[str, object]:
    """Capture application-visible notifications to a new local-only JSONL file.

    Dependency injection supports isolated mock tests without OS BLE or hardware.
    Do not run while BrainFlow, Muse apps or OpenMuse own the headset.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Explicit device name required")
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Duration must be positive and finite")
    if not math.isfinite(discovery_timeout) or not 1 <= discovery_timeout <= 60:
        raise ValueError("Discovery timeout must be 1..60 seconds")
    if preset not in ALLOWED_PRESETS:
        raise ValueError("Unsupported preset")
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    if bleak_client is None or bleak_scanner is None:
        try:
            from bleak import BleakClient, BleakScanner
        except ImportError as exc:
            raise RuntimeError("Install bleak separately: python -m pip install bleak") from exc
        bleak_client, bleak_scanner = BleakClient, BleakScanner
    matches = [d for d in await bleak_scanner.discover(timeout=discovery_timeout)
               if d.name == name]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one device named {name!r}, found {len(matches)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation is deliberately after discovery. Failed stream retains
    # its partial capture; never resume/overwrite under the same filename.
    captured = 0
    characteristics = []
    async with bleak_client(matches[0], timeout=discovery_timeout) as client:
        available = {str(c.uuid).lower(): c
                     for service in client.services
                     for c in service.characteristics}
        for uuid in SENSOR_SUFFIXES:
            ch = available.get(uuid)
            if ch is not None and "notify" in {p.lower() for p in ch.properties}:
                characteristics.append(uuid)
        if not characteristics:
            raise RuntimeError("No notifiable Athena data characteristic found")
        if start_stream and CONTROL_UUID not in available:
            raise RuntimeError("Control GATT characteristic missing; no commands sent")
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            def on_data(sender, data):
                nonlocal captured
                uuid = str(sender.uuid).lower()
                if uuid not in characteristics:
                    return
                row = {
                    "receive_monotonic_seconds": time.monotonic(),
                    "characteristic": uuid,
                    "payload_hex": bytes(data).hex(),
                }
                stream.write(json.dumps(row, separators=(",", ":")) + "\n")
                stream.flush()
                captured += 1

            subscribed = []
            started = False
            stream_command_attempted = False
            try:
                for uuid in characteristics:
                    await client.start_notify(uuid, on_data)
                    subscribed.append(uuid)
                if start_stream:
                    stream_command_attempted = True
                    for cmd in ("v6", "s", "h", preset, "s", "dc001", "dc001"):
                        await client.write_gatt_char(CONTROL_UUID, frame_control_command(cmd), response=True)
                    if low_latency:
                        await client.write_gatt_char(CONTROL_UUID, frame_control_command("L1"), response=True)
                    started = True
                await asyncio.sleep(duration)
                if not client.is_connected:
                    raise RuntimeError("BLE disconnected during capture; partial JSONL retained")
            finally:
                if stream_command_attempted and client.is_connected:
                    try:
                        await client.write_gatt_char(CONTROL_UUID, frame_control_command("h"), response=True)
                    except Exception:
                        pass  # preserve raw capture and avoid masking prior failure
                for uuid in reversed(subscribed):
                    if client.is_connected:
                        try:
                            await client.stop_notify(uuid)
                        except Exception:
                            pass
    if captured == 0:
        raise RuntimeError("No BLE notifications received; empty raw journal retained")
    return {"path": str(output), "notification_count": captured,
            "notifiable_characteristics": characteristics,
            "source_clock": "host_monotonic_callback_not_device",
            "hardware_validated": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--discovery-timeout", type=float, default=20.0)
    parser.add_argument("--start-stream", action="store_true",
                        help="Explicitly send allowlisted Athena init/start commands")
    parser.add_argument("--preset", choices=ALLOWED_PRESETS, default="p21")
    parser.add_argument("--low-latency", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = asyncio.run(collect(args.output, name=args.name,
                                     duration=args.duration,
                                     discovery_timeout=args.discovery_timeout,
                                     start_stream=args.start_stream,
                                     preset=args.preset, low_latency=args.low_latency))
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"BLE capture failed: {exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
