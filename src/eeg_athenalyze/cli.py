"""Command-line entry point for EEG Athenalyze."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.recording import SyntheticConfig, generate_synthetic_recording


def _record_synthetic(arguments: argparse.Namespace) -> int:
    try:
        config = SyntheticConfig(
            sample_rate_hz=arguments.sample_rate,
            seed=arguments.seed,
        )
        recording = generate_synthetic_recording(
            arguments.duration,
            config=config,
            condition=arguments.condition,
        )
        path = save_recording(recording, arguments.output)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(
        f"Saved simulated recording {recording.recording_id}: "
        f"{len(recording.samples_uv)} samples, {len(recording.channel_names)} channels "
        f"at {recording.sample_rate_hz:g} Hz -> {path}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eeg-athenalyze")
    subcommands = parser.add_subparsers(dest="command", required=True)
    synthetic = subcommands.add_parser(
        "synthetic-record", help="generate and archive simulated EEG"
    )
    synthetic.add_argument("--output", type=Path, required=True)
    synthetic.add_argument("--duration", type=float, default=10.0)
    synthetic.add_argument("--sample-rate", type=float, default=256.0)
    synthetic.add_argument("--seed", type=int, default=0)
    synthetic.add_argument("--condition", default="synthetic")
    synthetic.set_defaults(handler=_record_synthetic)
    arguments = parser.parse_args(argv)
    return arguments.handler(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
