"""Pure offline bitstream tests for Athena candidate 14-bit EEG packing.

No BLE access. This is a reference *hypothesis* until matched to source-pinned
native decoder bytes and physical packet captures.
"""
from __future__ import annotations

from collections.abc import Iterable

EEG_BITS = 14
EEG_MASK = (1 << EEG_BITS) - 1
EEG_MIDPOINT = 1 << (EEG_BITS - 1)
EEG_FULL_SCALE_UV = 1450.0
SUPPORTED_EEG_TAGS = {0x11: (4, 4), 0x12: (8, 2)}


def decode_lsb_14bit(payload: bytes, *, sample_count: int) -> tuple[int, ...]:
    """Decode contiguous least-significant-bit-first 14-bit unsigned values.

    The byte/bit model is explicitly a test candidate, not a verified Athena
    subpacket framing contract; callers must strip upstream headers themselves.
    """
    if sample_count < 0:
        raise ValueError("sample_count must be nonnegative")
    expected_bits = sample_count * EEG_BITS
    expected_bytes = (expected_bits + 7) // 8
    if len(payload) != expected_bytes:
        raise ValueError(f"Expected {expected_bytes} payload bytes, got {len(payload)}")
    stream = int.from_bytes(payload, "little")
    if expected_bits % 8 and stream >> expected_bits:
        raise ValueError("Nonzero padding bits in EEG payload")
    return tuple((stream >> (i * EEG_BITS)) & EEG_MASK for i in range(sample_count))


def encode_lsb_14bit(values: Iterable[int]) -> bytes:
    """Synthetic fixture encoder, intentionally independent of device I/O."""
    raw = tuple(values)
    if any(not isinstance(v, int) or not 0 <= v <= EEG_MASK for v in raw):
        raise ValueError("Expected unsigned 14-bit integer values")
    stream = sum(v << (i * EEG_BITS) for i, v in enumerate(raw))
    return stream.to_bytes((len(raw) * EEG_BITS + 7) // 8, "little")


def codes_to_uv(codes: Iterable[int], *, denominator: int = 16383) -> tuple[float, ...]:
    """Convert candidate offset-binary values without claiming ADC validation."""
    if denominator not in (16383, 16384):
        raise ValueError("Denominator must be 16383 or 16384")
    raw = tuple(codes)
    if any(not isinstance(v, int) or not 0 <= v <= EEG_MASK for v in raw):
        raise ValueError("EEG sample code outside 14-bit range")
    return tuple((v - EEG_MIDPOINT) * EEG_FULL_SCALE_UV / denominator for v in raw)


def decode_eeg_tag_payload(tag: int, payload: bytes) -> tuple[tuple[int, ...], ...]:
    """Return sample-major code matrix, with unknown physical channel mapping.

    EEG8 mode's eight logical channels are not assumed to be eight electrodes.
    """
    if tag not in SUPPORTED_EEG_TAGS:
        raise ValueError(f"Unknown EEG tag: 0x{tag:02x}")
    channels, per_channel = SUPPORTED_EEG_TAGS[tag]
    values = decode_lsb_14bit(payload, sample_count=channels * per_channel)
    return tuple(tuple(values[t * channels + c] for c in range(channels))
                 for t in range(per_channel))


def summarize_packet_indices(indices: Iterable[int], *, modulus: int | None = None) -> dict[str, object]:
    """Conservative index-order report; never infer BLE loss from unknown modulus.

    A positive modulo delta >1 is only an *index jump*, NOT certified packet loss.
    """
    values = tuple(indices)
    if any(not isinstance(v, int) or v < 0 for v in values):
        raise ValueError("Packet indices must be nonnegative integers")
    if modulus is not None and (modulus < 2 or any(v >= modulus for v in values)):
        raise ValueError("Invalid packet-index modulus or index")
    repeated = sum(a == b for a, b in zip(values, values[1:]))
    if modulus is None:
        return {"count": len(values), "repeated_adjacent_indices": repeated,
                "index_jump_candidates": None, "packet_loss_estimate": None,
                "clock_validated": False}
    deltas = [(b - a) % modulus for a, b in zip(values, values[1:])]
    return {"count": len(values), "repeated_adjacent_indices": repeated,
            "index_jump_candidates": sum(d > 1 for d in deltas),
            "packet_loss_estimate": None, "clock_validated": False}


def brainflow_candidate_sample_timestamp(
    last_timestamp: float, current_timestamp: float,
    sample_index: int, n_samples: int, sampling_rate: float,
) -> float:
    """Exact branch model of upstream MuseAthena::get_sample_timestamp.

    This models software host timing, NOT the Muse hardware clock. It exists
    solely to make duplicate timestamps reproducible in deterministic tests.
    """
    if n_samples <= 0 or sampling_rate <= 0:
        return current_timestamp
    if last_timestamp <= 0.0:
        return current_timestamp - (n_samples - sample_index - 1) / sampling_rate
    if current_timestamp <= last_timestamp:
        return current_timestamp
    proposal = last_timestamp + (sample_index + 1) / sampling_rate
    if proposal <= current_timestamp:
        return proposal
    step = (current_timestamp - last_timestamp) / n_samples
    return last_timestamp + step * (sample_index + 1)
