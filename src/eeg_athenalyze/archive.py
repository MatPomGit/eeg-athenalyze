"""Atomic, checksummed storage for unprocessed EEG recordings."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

from eeg_athenalyze.recording import Recording

_ARCHIVE_VERSION = 1
_RECORDING_MEMBER = "recording.json"
_MANIFEST_MEMBER = "manifest.json"


def _recording_bytes(recording: Recording) -> bytes:
    payload = {
        "recording_id": recording.recording_id,
        "sample_rate_hz": recording.sample_rate_hz,
        "channel_names": recording.channel_names,
        "samples_uv": recording.samples_uv,
        "timestamps_seconds": recording.timestamps_seconds,
        "metadata": recording.metadata,
    }
    return json.dumps(
        payload, allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def save_recording(recording: Recording, destination: str | Path) -> Path:
    """Atomically save and read-back-verify an archive without overwriting."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    recording_data = _recording_bytes(recording)
    manifest = {
        "archive_version": _ARCHIVE_VERSION,
        "recording_sha256": hashlib.sha256(recording_data).hexdigest(),
        "recording_member": _RECORDING_MEMBER,
    }
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            with zipfile.ZipFile(
                temporary, mode="w", compression=zipfile.ZIP_DEFLATED
            ) as archive:
                archive.writestr(_MANIFEST_MEMBER, json.dumps(manifest).encode("utf-8"))
                archive.writestr(_RECORDING_MEMBER, recording_data)
            temporary.flush()
            os.fsync(temporary.fileno())

        verified_recording = load_recording(temporary_path)
        if verified_recording != recording:
            raise OSError(
                "archive read-back verification did not match source recording"
            )
        os.link(temporary_path, path)
        return path
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def load_recording(source: str | Path) -> Recording:
    """Load an archive, rejecting unsupported formats and checksum mismatches."""
    path = Path(source)
    try:
        with zipfile.ZipFile(path, mode="r") as archive:
            manifest = json.loads(archive.read(_MANIFEST_MEMBER))
            recording_data = archive.read(_RECORDING_MEMBER)
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid EEG recording archive: {path}") from error

    if manifest.get("archive_version") != _ARCHIVE_VERSION:
        raise ValueError("unsupported EEG recording archive version")
    if manifest.get("recording_member") != _RECORDING_MEMBER:
        raise ValueError("invalid EEG recording archive manifest")
    actual_digest = hashlib.sha256(recording_data).hexdigest()
    if actual_digest != manifest.get("recording_sha256"):
        raise ValueError("EEG recording archive checksum mismatch")

    try:
        payload = json.loads(recording_data)
        return Recording(
            recording_id=payload["recording_id"],
            sample_rate_hz=payload["sample_rate_hz"],
            channel_names=tuple(payload["channel_names"]),
            samples_uv=tuple(tuple(row) for row in payload["samples_uv"]),
            timestamps_seconds=tuple(payload["timestamps_seconds"]),
            metadata=payload["metadata"],
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("invalid EEG recording archive content") from error
