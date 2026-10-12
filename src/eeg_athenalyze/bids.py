"""Lossless native-archive to BrainVision EEG-BIDS conversion and validation."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess

from eeg_athenalyze.archive import load_recording

_LABEL = re.compile(r"^[a-zA-Z0-9]+$")


def export_bids(source: Path, root: Path, *, power_line_frequency: float = 50.0) -> Path:
    """Convert a checksummed unprocessed archive to BIDS without changing it.

    The caller must run the official BIDS validator before claiming compliance.
    """
    import numpy as np
    import mne
    from mne_bids import BIDSPath, write_raw_bids, make_dataset_description, read_raw_bids

    recording = load_recording(source)
    metadata = recording.metadata
    if metadata.get("channel_units") != "microvolts":
        raise ValueError("Only microvolt source samples can currently be exported")
    if metadata.get("timestamp_semantics") not in {
        "synthetic_elapsed_seconds",
    }:
        raise ValueError("Unsupported or unverified timestamp semantics")
    if not recording.samples_uv:
        raise ValueError("Cannot export an empty recording")
    # BIDS EEG represents uniformly sampled streams; never conceal acquisition gaps.
    timestamps = np.asarray(recording.timestamps_seconds, dtype=float)
    expected = np.arange(len(timestamps)) / recording.sample_rate_hz
    if not np.allclose(timestamps - timestamps[0], expected, rtol=0, atol=1e-6):
        raise ValueError("Nonuniform timestamps require gap-aware export")
    participant = str(metadata.get("participant_id", "sub001"))
    session = str(metadata.get("session_id", "01"))
    participant = participant.removeprefix("sub-")
    session = session.removeprefix("ses-")
    if not _LABEL.fullmatch(participant) or not _LABEL.fullmatch(session):
        raise ValueError("Invalid BIDS participant/session identifier")
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Output dataset must be a new empty directory: {root}")
    info = mne.create_info(
        list(recording.channel_names),
        sfreq=recording.sample_rate_hz,
        ch_types=["eeg"] * len(recording.channel_names),
    )
    raw = mne.io.RawArray(
        np.asarray(recording.samples_uv, dtype=float).T * 1e-6,
        info,
        verbose="ERROR",
    )
    raw.info["line_freq"] = power_line_frequency
    event_items = metadata.get("events", [])
    if not isinstance(event_items, list):
        raise ValueError("Invalid source events")
    annotations = []
    for event in event_items:
        if not isinstance(event, dict):
            raise ValueError("Invalid event")
        onset = float(event["onset_seconds"])
        duration = float(event["duration_seconds"])
        if onset < 0 or duration < 0 or onset + duration > len(timestamps) / recording.sample_rate_hz + 1e-6:
            raise ValueError("Event outside recording")
        annotations.append((onset, duration, str(event["condition"])))
    if annotations:
        raw.set_annotations(mne.Annotations(
            onset=[e[0] for e in annotations],
            duration=[e[1] for e in annotations],
            description=[e[2] for e in annotations],
        ))
    path = BIDSPath(subject=participant, session=session, task="rest", datatype="eeg", root=root)
    # For NPZ/JSON-derived preloaded arrays an explicit output format is required.
    try:
        written = write_raw_bids(
            raw, path, format="BrainVision", allow_preload=True,
            overwrite=False, verbose=False,
        )
        make_dataset_description(
            name="EEG Neurolyze synthetic resting-state demonstration",
            dataset_type="raw",
            path=root,
        )
        # The BrainVision export is a converted representation, not the native archive.
        restored = read_raw_bids(written, verbose=False)
        exported = restored.get_data()
        original = raw.get_data()
        if exported.shape != original.shape or not np.allclose(
            exported, original, atol=1e-8, rtol=1e-4
        ):
            raise ValueError("BIDS read-back sample verification failed")
        return root
    except Exception:
        # Do not leave a partially valid-looking dataset after a failed conversion.
        if root.exists():
            shutil.rmtree(root)
        raise


def validate_bids(root: Path, *, executable: str = "bids-validator-deno") -> int:
    """Run the real installed BIDS validator; missing binaries fail closed."""
    if not root.is_dir():
        raise ValueError(f"Dataset directory does not exist: {root}")
    if shutil.which(executable) is None:
        raise RuntimeError(
            "Official BIDS validator unavailable. Install the bids-validator-deno "
            "optional dependency in the project environment."
        )
    result = subprocess.run(
        [executable, str(root.resolve()), "--json"],
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )
    report = {
        "validator": executable,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    report_path = root.parent / (root.name + ".bids-validation.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return result.returncode
