"""Welch power spectral density and resting-state alpha comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_left
import math
from typing import Sequence

from eeg_athenalyze.recording import Recording


@dataclass(frozen=True)
class Spectrum:
    frequencies_hz: tuple[float, ...]
    power_uv2_per_hz: tuple[float, ...]


@dataclass(frozen=True)
class AlphaComparison:
    eyes_open_uv2: dict[str, float]
    eyes_closed_uv2: dict[str, float]

    @property
    def relative_change(self) -> dict[str, float]:
        return {
            channel: (
                self.eyes_closed_uv2[channel] - open_power
            ) / open_power
            if open_power > 0
            else math.inf
            for channel, open_power in self.eyes_open_uv2.items()
        }


def welch_psd(
    samples: Sequence[float],
    sample_rate_hz: float,
    *,
    segment_seconds: float = 2.0,
) -> Spectrum:
    """Estimate one-sided PSD in microvolt-squared per hertz."""
    if not math.isfinite(sample_rate_hz) or sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be a positive finite number")
    if not math.isfinite(segment_seconds) or segment_seconds <= 0:
        raise ValueError("segment_seconds must be a positive finite number")
    if len(samples) < 8 or any(not math.isfinite(value) for value in samples):
        raise ValueError("at least eight finite samples are required")

    requested_length = max(8, round(segment_seconds * sample_rate_hz))
    segment_length = min(len(samples), requested_length)
    fft_length = 1 << (segment_length - 1).bit_length()
    window = tuple(
        0.5 - 0.5 * math.cos(2.0 * math.pi * index / (segment_length - 1))
        for index in range(segment_length)
    )
    window_power = sum(value * value for value in window)
    step = max(1, segment_length // 2)
    starts = range(0, len(samples) - segment_length + 1, step)
    accumulated = [0.0] * (fft_length // 2 + 1)
    segment_count = 0

    for start in starts:
        segment = samples[start : start + segment_length]
        mean = sum(segment) / segment_length
        transformed = _fft(
            [
                complex((value - mean) * window[index], 0.0)
                for index, value in enumerate(segment)
            ]
            + [0j] * (fft_length - segment_length)
        )
        for index in range(len(accumulated)):
            power = abs(transformed[index]) ** 2 / (
                sample_rate_hz * window_power
            )
            if index != 0 and index != fft_length // 2:
                power *= 2.0
            accumulated[index] += power
        segment_count += 1

    if segment_count == 0:
        raise ValueError("not enough samples to calculate a spectrum")
    scale = 1.0 / segment_count
    return Spectrum(
        frequencies_hz=tuple(
            index * sample_rate_hz / fft_length
            for index in range(len(accumulated))
        ),
        power_uv2_per_hz=tuple(value * scale for value in accumulated),
    )


def band_power(spectrum: Spectrum, low_hz: float, high_hz: float) -> float:
    """Integrate PSD over a frequency band using the spectrum's bin width."""
    if not math.isfinite(low_hz) or not math.isfinite(high_hz):
        raise ValueError("band limits must be finite")
    if low_hz < 0 or high_hz <= low_hz:
        raise ValueError("band must have a non-negative lower and higher upper limit")
    if len(spectrum.frequencies_hz) < 2:
        raise ValueError("spectrum must have at least two frequency bins")
    bin_width = spectrum.frequencies_hz[1] - spectrum.frequencies_hz[0]
    return sum(
        power
        for frequency, power in zip(
            spectrum.frequencies_hz, spectrum.power_uv2_per_hz
        )
        if low_hz <= frequency <= high_hz
    ) * bin_width


def compare_resting_alpha(
    recording: Recording,
    *,
    low_hz: float = 8.0,
    high_hz: float = 13.0,
    segment_seconds: float = 2.0,
    max_gap_factor: float = 1.5,
) -> AlphaComparison:
    """Compare per-channel alpha power in EO/EC event segments.

    Measured timestamp coverage is half-open: the first timestamp through one
    nominal sample period after the last timestamp.
    """
    if not math.isfinite(max_gap_factor) or max_gap_factor <= 1:
        raise ValueError("max_gap_factor must be finite and greater than 1")
    if (
        not math.isfinite(low_hz)
        or not math.isfinite(high_hz)
        or low_hz < 0
        or high_hz <= low_hz
        or high_hz > recording.sample_rate_hz / 2
    ):
        raise ValueError("alpha band must be finite and within the Nyquist range")
    # Require at least 1 Hz true frequency resolution, or finer for
    # narrower-than-1-Hz bands. Zero-padding alone does not add resolution.
    minimum_run_samples = max(
        8,
        math.ceil(recording.sample_rate_hz * max(1.0, 1.0 / (high_hz - low_hz))),
    )
    events = recording.metadata.get("events")
    if not isinstance(events, list):
        raise ValueError("recording does not contain experiment event metadata")
    powers: dict[str, dict[str, float]] = {}
    for condition in ("eyes_open", "eyes_closed"):
        event = next(
            (
                item
                for item in events
                if isinstance(item, dict) and item.get("condition") == condition
            ),
            None,
        )
        if event is None:
            raise ValueError(f"recording has no {condition} event")
        onset = event.get("onset_seconds")
        duration = event.get("duration_seconds")
        if (
            not isinstance(onset, (int, float))
            or not isinstance(duration, (int, float))
            or not math.isfinite(onset)
            or not math.isfinite(duration)
            or duration <= 0
        ):
            raise ValueError(f"recording has invalid {condition} event timing")
        measured = recording.metadata.get("data_status") == "measured"
        event_end = onset + duration
        if measured:
            timestamps = recording.timestamps_seconds
            if (
                not timestamps
                or onset < timestamps[0]
                or event_end > timestamps[-1] + 1 / recording.sample_rate_hz
            ):
                raise ValueError(
                    f"{condition} event falls outside measured recording coverage"
                )
        start = (bisect_left(recording.timestamps_seconds, onset) if measured
                 else round(onset * recording.sample_rate_hz))
        stop = (bisect_left(recording.timestamps_seconds, event_end)
                if measured else min(len(recording.samples_uv),
                                     start + round(duration * recording.sample_rate_hz)))
        condition_samples = recording.samples_uv[start:stop]
        if len(condition_samples) < 8:
            raise ValueError(f"recording has too few samples for {condition}")
        powers[condition] = {}
        runs = [(start, stop)]
        if measured:
            runs = []
            run_start = start
            maximum_gap = max_gap_factor / recording.sample_rate_hz
            for index in range(start + 1, stop):
                gap = recording.timestamps_seconds[index] - recording.timestamps_seconds[index - 1]
                if gap <= 0 or gap > maximum_gap:
                    if index - run_start >= minimum_run_samples:
                        runs.append((run_start, index))
                    run_start = index
            if stop - run_start >= minimum_run_samples:
                runs.append((run_start, stop))
        if not runs:
            raise ValueError(
                f"recording has insufficient contiguous samples for {condition}; "
                f"requires at least {minimum_run_samples} samples per Welch run "
                "for the selected frequency band"
            )
        for channel_index, channel_name in enumerate(recording.channel_names):
            estimates = []
            for run_start, run_stop in runs:
                spectrum = welch_psd(
                    [row[channel_index] for row in recording.samples_uv[run_start:run_stop]],
                    recording.sample_rate_hz,
                    segment_seconds=segment_seconds,
                )
                run_length = run_stop - run_start
                segment_length = min(
                    run_length,
                    max(8, round(segment_seconds * recording.sample_rate_hz)),
                )
                segment_count = 1 + (
                    run_length - segment_length
                ) // max(1, segment_length // 2)
                estimates.append(
                    (band_power(spectrum, low_hz, high_hz), segment_count)
                )
            if not estimates:
                raise ValueError(f"recording has insufficient contiguous samples for {condition}")
            powers[condition][channel_name] = sum(value * count for value, count in estimates) / sum(count for _, count in estimates)
    return AlphaComparison(
        eyes_open_uv2=powers["eyes_open"],
        eyes_closed_uv2=powers["eyes_closed"],
    )


def _fft(values: list[complex]) -> list[complex]:
    """In-place radix-2 Cooley-Tukey transform."""
    length = len(values)
    if length == 0 or length & (length - 1):
        raise ValueError("FFT length must be a power of two")
    reversed_index = 0
    for index in range(1, length):
        bit = length >> 1
        while reversed_index & bit:
            reversed_index ^= bit
            bit >>= 1
        reversed_index ^= bit
        if index < reversed_index:
            values[index], values[reversed_index] = (
                values[reversed_index],
                values[index],
            )

    block_length = 2
    while block_length <= length:
        angle = -2.0 * math.pi / block_length
        root = complex(math.cos(angle), math.sin(angle))
        for start in range(0, length, block_length):
            factor = 1.0 + 0j
            half = block_length // 2
            for offset in range(half):
                even = values[start + offset]
                odd = factor * values[start + offset + half]
                values[start + offset] = even + odd
                values[start + offset + half] = even - odd
                factor *= root
        block_length *= 2
    return values
