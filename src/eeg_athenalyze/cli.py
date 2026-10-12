"""Command-line entry point for EEG Athenalyze."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.analysis.spectral import compare_resting_alpha
from eeg_athenalyze.experiments.eyes_open_closed import (
    EyesOpenClosedConfig,
    run_eyes_open_closed,
)
from eeg_athenalyze.recording import SyntheticConfig, generate_synthetic_recording
from eeg_athenalyze.reporting.html_report import write_resting_report


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


def _run_experiment(arguments: argparse.Namespace) -> int:
    try:
        defaults = EyesOpenClosedConfig()
        config = EyesOpenClosedConfig(
            stabilization_seconds=defaults.stabilization_seconds
            * arguments.duration_scale,
            eyes_open_seconds=defaults.eyes_open_seconds * arguments.duration_scale,
            break_seconds=defaults.break_seconds * arguments.duration_scale,
            eyes_closed_seconds=defaults.eyes_closed_seconds
            * arguments.duration_scale,
            participant_id=arguments.participant,
            session_id=arguments.session,
            synthetic=SyntheticConfig(
                sample_rate_hz=arguments.sample_rate,
                seed=arguments.seed,
            ),
        )
        result = run_eyes_open_closed(arguments.output, config=config)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Saved raw simulated EEG: {result.archive_path}")
    print(f"Saved EO/EC report: {result.report_path}")
    return 0


def _analyze_session(arguments: argparse.Namespace) -> int:
    from eeg_athenalyze.archive import load_recording

    try:
        recording = load_recording(arguments.session)
        comparison = compare_resting_alpha(recording)
        report_path = write_resting_report(
            recording,
            comparison,
            arguments.output or arguments.session.with_suffix(".html"),
        )
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Saved resting-state report: {report_path}")
    return 0



def _bids_export(arguments: argparse.Namespace) -> int:
    from eeg_athenalyze.bids import export_bids

    try:
        dataset = export_bids(arguments.session, arguments.dataset)
    except (OSError, ValueError, ImportError, RuntimeError) as error:
        print(f"BIDS export failed: {error}", file=sys.stderr)
        return 1
    print(f"Exported EEG-BIDS candidate: {dataset}")
    print("Run BIDS validation before claiming compliance.")
    return 0


def _bids_validate(arguments: argparse.Namespace) -> int:
    from eeg_athenalyze.bids import validate_bids

    try:
        status = validate_bids(arguments.dataset)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"BIDS validation failed: {error}", file=sys.stderr)
        return 1
    print(f"BIDS validator exit status: {status}")
    return status


def _bids_derivatives(arguments: argparse.Namespace) -> int:
    from eeg_athenalyze.derivatives import export_alpha_derivatives

    try:
        path = export_alpha_derivatives(arguments.session, arguments.dataset)
    except (OSError, ValueError) as error:
        print(f"BIDS derivatives failed: {error}", file=sys.stderr)
        return 1
    print(f"Saved custom alpha-power derivative: {path}")
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

    experiment = subcommands.add_parser("experiment", help="run an experiment")
    experiment_commands = experiment.add_subparsers(
        dest="experiment_command", required=True
    )
    run = experiment_commands.add_parser("run")
    run.add_argument("name", choices=("eyes-open-closed",))
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--participant", default="sub-001")
    run.add_argument("--session")
    run.add_argument("--sample-rate", type=float, default=256.0)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument(
        "--duration-scale",
        type=float,
        default=1.0,
        help="scale all protocol blocks (use 1 for the specified 30/120/30/120 s)",
    )
    run.set_defaults(handler=_run_experiment)

    analyze = subcommands.add_parser(
        "analyze", help="analyze an archived EO/EC recording without reacquiring data"
    )
    analyze.add_argument("--session", type=Path, required=True)
    analyze.add_argument("--output", type=Path)
    analyze.set_defaults(handler=_analyze_session)

    bids = subcommands.add_parser("bids", help="EEG-BIDS export and validation")
    bids_commands = bids.add_subparsers(dest="bids_command", required=True)
    bids_export = bids_commands.add_parser("export")
    bids_export.add_argument("--session", type=Path, required=True)
    bids_export.add_argument("--dataset", type=Path, required=True)
    bids_export.set_defaults(handler=_bids_export)
    bids_validate = bids_commands.add_parser("validate")
    bids_validate.add_argument("--dataset", type=Path, required=True)
    bids_validate.set_defaults(handler=_bids_validate)

    derivatives = bids_commands.add_parser("derivatives", help="write custom EO/EC derivatives")
    derivatives.add_argument("--session", type=Path, required=True)
    derivatives.add_argument("--dataset", type=Path, required=True)
    derivatives.set_defaults(handler=_bids_derivatives)

    arguments = parser.parse_args(argv)
    return arguments.handler(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
