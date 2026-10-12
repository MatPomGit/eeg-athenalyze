"""Non-destructive, provenance-rich BIDS derivatives for synthetic EO/EC."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

from eeg_athenalyze.archive import load_recording
from eeg_athenalyze.analysis.spectral import compare_resting_alpha


def export_alpha_derivatives(source: Path, bids_root: Path) -> Path:
    """Write a versioned custom derivative, never replacing earlier results."""
    if not (bids_root / "dataset_description.json").is_file():
        raise ValueError("Export and validate a BIDS dataset first")
    recording = load_recording(source)
    if recording.metadata.get("data_status") != "simulated":
        raise ValueError("Only synthetic EO/EC derivatives are currently supported")
    participant = str(recording.metadata.get("participant_id", "sub001")).removeprefix("sub-")
    session = str(recording.metadata.get("session_id", "01")).removeprefix("ses-")
    if not all(re.fullmatch(r"[A-Za-z0-9]+", x) for x in (participant, session)):
        raise ValueError("Invalid BIDS identifiers")
    result = compare_resting_alpha(recording)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    pipeline = bids_root / "derivatives" / "eeg-neurolyze"
    destination = pipeline / f"sub-{participant}" / f"ses-{session}" / "eeg"
    stem = f"sub-{participant}_ses-{session}_task-rest_desc-alphapower"
    output = destination / f"{stem}.tsv"
    if output.exists():
        raise FileExistsError(f"Derivative already exists: {output}")
    with tempfile.TemporaryDirectory(prefix="neurolyze-deriv-") as scratch:
        staged = Path(scratch)
        source_description = json.loads((bids_root / "dataset_description.json").read_text(encoding="utf-8"))
        if not source_description.get("BIDSVersion"):
            raise ValueError("Raw dataset has no BIDSVersion")
        (staged / "dataset_description.json").write_text(
            json.dumps({
                "Name": "EEG Neurolyze alpha power derivatives",
                "BIDSVersion": source_description["BIDSVersion"],
                "DatasetType": "derivative",
                "GeneratedBy": [{"Name": "EEG Neurolyze", "Version": "0.1.0"}],
            }, indent=2), encoding="utf-8"
        )
        with (staged / "alpha.tsv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(["channel", "eyes_open_uv2", "eyes_closed_uv2"])
            for channel in recording.channel_names:
                writer.writerow([
                    channel, result.eyes_open_uv2[channel],
                    result.eyes_closed_uv2[channel],
                ])
        (staged / "alpha.json").write_text(json.dumps({
            "Description": "Custom derivative: resting alpha power by channel and condition",
            "Units": "uV^2",
            "FrequencyBandHz": [8, 13],
            "DataStatus": "simulated",
            "SourceArchiveSHA256": digest,
            "SourceArchiveName": source.name,
            "SoftwarePackage": "eeg_athenalyze",
            "Note": "Custom table, not a standardized EEG-BIDS feature schema",
        }, indent=2), encoding="utf-8")
        destination.mkdir(parents=True, exist_ok=True)
        for filename, target in [
            ("alpha.tsv", output),
            ("alpha.json", output.with_suffix(".json")),
        ]:
            if target.exists():
                raise FileExistsError(f"Derivative exists: {target}")
        description_target = pipeline / "dataset_description.json"
        if description_target.exists():
            existing = json.loads(description_target.read_text(encoding="utf-8"))
            expected = json.loads((staged / "dataset_description.json").read_text(encoding="utf-8"))
            if existing.get("Name") != expected["Name"]:
                raise ValueError("Existing derivatives pipeline has incompatible metadata")
        else:
            shutil.copyfile(staged / "dataset_description.json", description_target)
        shutil.copyfile(staged / "alpha.json", output.with_suffix(".json"))
        shutil.copyfile(staged / "alpha.tsv", output)
    return output
