"""Physical Muse S Athena acquisition using BrainFlow. No synthetic fallback."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from pathlib import Path
import time
import uuid

from eeg_athenalyze.archive import save_recording
from eeg_athenalyze.acquisition_journal import AcquisitionJournal, recover_journal
from eeg_athenalyze.recording import Recording

CHANNEL_NAMES = ("TP9", "AF7", "AF8", "TP10")


@dataclass(frozen=True)
class AthenaSettings:
    duration_seconds: float = 30.0
    serial_number: str = ""
    mac_address: str = ""
    preset_command: str = "preset=p1041;low_latency=true"
    poll_seconds: float = 0.25
    discovery_timeout_seconds: int = 15

    def __post_init__(self) -> None:
        if not math.isfinite(self.duration_seconds) or self.duration_seconds <= 0:
            raise ValueError("Duration must be positive and finite")
        if not 1 <= self.discovery_timeout_seconds <= 60:
            raise ValueError("Discovery timeout must be 1 to 60 seconds")
        if not 0.05 <= self.poll_seconds <= 5:
            raise ValueError("Poll period must be 0.05 to 5 seconds")


def _api():
    """Import hardware dependency only on explicit physical-device operations."""
    try:
        from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
    except ImportError as exc:
        raise RuntimeError("Install BrainFlow in .venv: python -m pip install '.[muse]'") from exc
    identifier = getattr(BoardIds, "MUSE_S_ATHENA_BOARD", None)
    # 5.22.0 release materials used the misspelling ANTHENA; support either
    # only if actually exposed by the locally installed BrainFlow runtime.
    if identifier is None:
        identifier = getattr(BoardIds, "MUSE_S_ANTHENA_BOARD", None)
    if identifier is None:
        raise RuntimeError("Installed BrainFlow does not expose the Muse S Athena board")
    return BoardShim, BrainFlowInputParams, int(identifier.value)


def device_info() -> dict[str, object]:
    """Report BrainFlow-provided layout; does not connect to hardware."""
    shim, _, board_id = _api()
    channels = list(shim.get_eeg_channels(board_id))
    if len(channels) != len(CHANNEL_NAMES):
        raise RuntimeError(f"Expected four principal EEG channels, found {len(channels)}")
    return {
        "board_id": board_id,
        "eeg_indices": channels,
        "channel_names": list(CHANNEL_NAMES),
        "sampling_rate_hz": shim.get_sampling_rate(board_id),
        "timestamp_channel": shim.get_timestamp_channel(board_id),
        "hardware_validated": False,
    }


def record_athena(output: Path, settings: AthenaSettings | None = None) -> Path:
    """Acquire physical EEG and persist source timestamps without interpolation.

    On discontinuous/non-monotonic timing, abort instead of silently replacing
    measured timestamps with a synthetic sample clock.
    """
    settings = settings or AthenaSettings()
    shim, params_class, board_id = _api()
    info = device_info()
    params = params_class()
    params.serial_number = settings.serial_number
    params.mac_address = settings.mac_address
    params.other_info = settings.preset_command
    params.timeout = settings.discovery_timeout_seconds
    board = shim(board_id, params)
    prepared = False
    started = False
    journal_path = Path(str(output) + '.partial.jsonl')
    if output.exists() or journal_path.exists():
        raise FileExistsError('Archive or recovery journal already exists')
    chunks_written = 0
    start_utc = datetime.now(timezone.utc).isoformat()
    try:
        try:
            board.prepare_session()
        except Exception as exc:
            if getattr(exc, "exit_code", None) == 7 or "BOARD_NOT_READY_ERROR" in str(exc):
                raise RuntimeError(
                    "Muse S Athena BLE connection opened but the streaming GATT "
                    "control characteristic may be unavailable. Verify that the "
                    "device is actually Athena-compatible, close competing Muse "
                    "apps, reconnect Bluetooth and inspect the FE8D service and "
                    "273e0001-4c4d-454d-96be-f03bac821358 characteristic. "
                    "Changing EEG presets cannot create a missing GATT characteristic. "
                    f"BrainFlow reported: {exc}"
                ) from exc
            raise
        prepared = True
        board.start_stream()
        started = True
        with AcquisitionJournal(output, channel_count=len(CHANNEL_NAMES)) as journal:
            until = time.monotonic() + settings.duration_seconds
            while time.monotonic() < until:
                time.sleep(min(settings.poll_seconds, max(0.0, until - time.monotonic())))
                batch = board.get_board_data()
                if batch.shape[1]:
                    journal.append(
                        batch[info["eeg_indices"], :].T,
                        batch[int(info["timestamp_channel"]), :],
                    )
            tail = board.get_board_data()
            if tail.shape[1]:
                journal.append(
                    tail[info["eeg_indices"], :].T,
                    tail[int(info["timestamp_channel"]), :],
                )
            chunks_written = journal.sample_count
    finally:
        if started:
            try:
                board.stop_stream()
            finally:
                if prepared:
                    board.release_session()
        elif prepared:
            board.release_session()

    if not chunks_written:
        raise RuntimeError("Muse S Athena returned no EEG samples; journal retained")
    import numpy as np

    rows, times = recover_journal(journal_path, channel_count=len(CHANNEL_NAMES))
    if len(rows) != chunks_written:
        raise RuntimeError("Recovery journal sample count mismatch")
    indices = info["eeg_indices"]
    timestamp_index = int(info["timestamp_channel"])
    timestamps = np.asarray(times, dtype=float)
    if not np.all(np.isfinite(timestamps)) or np.any(np.diff(timestamps) < 0):
        raise RuntimeError("Missing or non-monotonic source timestamps; no file written")
    source_t = tuple(float(t - timestamps[0]) for t in timestamps)
    eeg = np.asarray(rows, dtype=float)
    if not np.all(np.isfinite(eeg)):
        raise RuntimeError("Non-finite EEG values; no file written")
    deltas = np.diff(timestamps)
    nominal_period = 1.0 / float(info["sampling_rate_hz"])
    suspected_gaps = int(np.count_nonzero(deltas > nominal_period * 1.5))
    duplicate_timestamps = int(np.count_nonzero(deltas == 0))
    largest_interval = float(deltas.max()) if len(deltas) else 0.0
    # Read-back archive keeps BrainFlow's microvolt values and elapsed
    # source timestamps. Absolute epoch timestamps are preserved in metadata.
    recording = Recording(
        recording_id=str(uuid.uuid4()),
        sample_rate_hz=float(info["sampling_rate_hz"]),
        channel_names=CHANNEL_NAMES,
        samples_uv=tuple(tuple(float(v) for v in row) for row in eeg),
        timestamps_seconds=source_t,
        metadata={
            "data_status": "measured",
            "device_model": "Muse S Athena",
            "channel_units": "microvolts",
            "timestamp_semantics": "brainflow_source_epoch_seconds",
            "first_source_timestamp_seconds": float(timestamps[0]),
            "recording_start_utc": start_utc,
            "board_id": board_id,
            "source_eeg_indices": indices,
            "source_timestamp_index": timestamp_index,
            "source_sample_count": len(source_t),
            "suspected_timestamp_gaps": suspected_gaps,
            "duplicate_source_timestamps": duplicate_timestamps,
            "largest_source_interval_seconds": largest_interval,
            "recording_end_utc": datetime.now(timezone.utc).isoformat(),
            "source_clock_kind": "BrainFlow timestamp; physical timing unverified",
            "connection_configuration": {
                "preset_command": settings.preset_command,
                "serial_number_specified": bool(settings.serial_number),
                "mac_address_specified": bool(settings.mac_address),
            },
            "timing_verified": False,
            "electrode_reference_verified": False,
        },
    )
    result = save_recording(recording, output)
    journal_path.unlink()
    return result
