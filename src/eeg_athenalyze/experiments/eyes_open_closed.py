"""Configurable synthetic eyes-open/eyes-closed resting-state session."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from pathlib import Path
import re
import uuid

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.recording import (
    Recording,
    SyntheticConfig,
    generate_synthetic_recording,
)

_IDENTIFIER = re.compile(r"^(?:sub-)?[A-Za-z0-9]+$")


@dataclass(frozen=True)
class EyesOpenClosedConfig:
    stabilization_seconds: float = 30.0
    eyes_open_seconds: float = 120.0
    break_seconds: float = 30.0
    eyes_closed_seconds: float = 120.0
    participant_id: str = "sub-001"
    session_id: str | None = None
    synthetic: SyntheticConfig = SyntheticConfig()

    def __post_init__(self) -> None:
        durations = (
            self.stabilization_seconds,
            self.eyes_open_seconds,
            self.break_seconds,
            self.eyes_closed_seconds,
        )
        if any(not math.isfinite(value) or value <= 0 for value in durations):
            raise ValueError("all block durations must be positive and finite")
        if not _IDENTIFIER.fullmatch(self.participant_id):
            raise ValueError("participant_id must contain only letters and digits")
        if self.session_id is not None and not _IDENTIFIER.fullmatch(self.session_id):
            raise ValueError("session_id must contain only letters and digits")


@dataclass(frozen=True)
class ExperimentResult:
    recording: Recording
    archive_path: Path
    report_path: Path


def run_eyes_open_closed(
    output_directory: str | Path,
    *,
    config: EyesOpenClosedConfig | None = None,
) -> ExperimentResult:
    """Run the synthetic protocol, archive original samples, then report results."""
    settings = config or EyesOpenClosedConfig()
    session_id = settings.session_id or uuid.uuid4().hex[:8]
    stem = f"{settings.participant_id}_ses-{session_id}_task-rest"
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / f"{stem}.eegz"
    report_path = output / f"{stem}.html"
    blocks = (
        ("stabilization", settings.stabilization_seconds),
        ("eyes_open", settings.eyes_open_seconds),
        ("break", settings.break_seconds),
        ("eyes_closed", settings.eyes_closed_seconds),
    )

    samples: list[tuple[float, ...]] = []
    timestamps: list[float] = []
    events: list[dict[str, object]] = []
    onset = 0.0
    for block_index, (condition, duration) in enumerate(blocks):
        block_config = replace(
            settings.synthetic, seed=settings.synthetic.seed + block_index
        )
        block = generate_synthetic_recording(
            duration,
            config=block_config,
            condition=condition,
        )
        actual_duration = len(block.samples_uv) / block.sample_rate_hz
        events.append(
            {
                "event_type": f"{condition}_start",
                "condition": condition,
                "onset_seconds": onset,
                "duration_seconds": actual_duration,
                "timestamp_semantics": "synthetic_elapsed_seconds",
            }
        )
        samples.extend(block.samples_uv)
        timestamps.extend(onset + timestamp for timestamp in block.timestamps_seconds)
        onset += actual_duration

    recording = Recording(
        recording_id=str(uuid.uuid4()),
        sample_rate_hz=settings.synthetic.sample_rate_hz,
        channel_names=settings.synthetic.channel_names,
        samples_uv=tuple(samples),
        timestamps_seconds=tuple(timestamps),
        metadata={
            "data_status": "simulated",
            "device_model": "synthetic",
            "channel_units": "microvolts",
            "timestamp_semantics": "synthetic_elapsed_seconds",
            "experiment_id": "eyes-open-closed",
            "participant_id": settings.participant_id,
            "session_id": session_id,
            "events": events,
            "configuration": {
                "stabilization_seconds": settings.stabilization_seconds,
                "eyes_open_seconds": settings.eyes_open_seconds,
                "break_seconds": settings.break_seconds,
                "eyes_closed_seconds": settings.eyes_closed_seconds,
                "sample_rate_hz": settings.synthetic.sample_rate_hz,
                "random_seed": settings.synthetic.seed,
            },
        },
    )
    save_recording(recording, archive_path)

    from eeg_athenalyze.analysis.spectral import compare_resting_alpha
    from eeg_athenalyze.reporting.html_report import write_resting_report

    comparison = compare_resting_alpha(recording)
    write_resting_report(recording, comparison, report_path)
    return ExperimentResult(recording, archive_path, report_path)
