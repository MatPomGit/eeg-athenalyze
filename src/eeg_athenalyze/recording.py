"""Recording model and deterministic synthetic EEG generation."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import uuid


@dataclass(frozen=True)
class Recording:
    """An immutable, sample-major EEG recording with elapsed source timestamps."""

    recording_id: str
    sample_rate_hz: float
    channel_names: tuple[str, ...]
    samples_uv: tuple[tuple[float, ...], ...]
    timestamps_seconds: tuple[float, ...]
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        if not self.recording_id:
            raise ValueError("recording_id must not be empty")
        if not math.isfinite(self.sample_rate_hz) or self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be a positive finite number")
        if not self.channel_names or len(set(self.channel_names)) != len(
            self.channel_names
        ):
            raise ValueError("channel_names must be non-empty and unique")
        if len(self.samples_uv) != len(self.timestamps_seconds):
            raise ValueError("sample and timestamp counts must match")
        previous_timestamp = -math.inf
        for timestamp, row in zip(self.timestamps_seconds, self.samples_uv):
            if not math.isfinite(timestamp) or timestamp <= previous_timestamp:
                raise ValueError("timestamps must be finite and strictly increasing")
            if len(row) != len(self.channel_names):
                raise ValueError("each sample must have one value per channel")
            if any(not math.isfinite(value) for value in row):
                raise ValueError("sample values must be finite")
            previous_timestamp = timestamp


@dataclass(frozen=True)
class SyntheticConfig:
    """Settings for reproducible simulated EEG, expressed in microvolts."""

    sample_rate_hz: float = 256.0
    channel_names: tuple[str, ...] = ("TP9", "AF7", "AF8", "TP10")
    seed: int = 0
    oscillations_uv: tuple[tuple[float, float], ...] = ((6.0, 3.0), (20.0, 2.0))
    alpha_frequency_hz: float = 10.0
    alpha_amplitude_uv: float = 8.0
    alpha_reactivity_multiplier: float = 2.0
    line_noise_frequency_hz: float = 50.0
    line_noise_amplitude_uv: float = 0.5
    noise_amplitude_uv: float = 1.0
    blink_rate_hz: float = 0.15
    blink_amplitude_uv: float = 40.0
    muscle_burst_rate_hz: float = 0.2
    muscle_amplitude_uv: float = 3.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.sample_rate_hz) or self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be a positive finite number")
        if not self.channel_names or len(set(self.channel_names)) != len(
            self.channel_names
        ):
            raise ValueError("channel_names must be non-empty and unique")
        if not isinstance(self.seed, int):
            raise ValueError("seed must be an integer")
        if (
            not math.isfinite(self.alpha_reactivity_multiplier)
            or self.alpha_reactivity_multiplier < 0
        ):
            raise ValueError(
                "alpha_reactivity_multiplier must be finite and non-negative"
            )
        frequencies = [self.alpha_frequency_hz, self.line_noise_frequency_hz]
        frequencies.extend(frequency for frequency, _ in self.oscillations_uv)
        if any(
            not math.isfinite(frequency)
            or frequency < 0
            or frequency >= self.sample_rate_hz / 2
            for frequency in frequencies
        ):
            raise ValueError("all frequencies must be below the Nyquist frequency")
        numeric_values = (
            self.alpha_amplitude_uv,
            self.line_noise_amplitude_uv,
            self.noise_amplitude_uv,
            self.blink_rate_hz,
            self.blink_amplitude_uv,
            self.muscle_burst_rate_hz,
            self.muscle_amplitude_uv,
            *(amplitude for _, amplitude in self.oscillations_uv),
        )
        if any(not math.isfinite(value) or value < 0 for value in numeric_values):
            raise ValueError(
                "amplitudes and artifact rates must be finite and non-negative"
            )


def generate_synthetic_recording(
    duration_seconds: float,
    *,
    config: SyntheticConfig | None = None,
    condition: str = "synthetic",
    alpha_multiplier: float | None = None,
) -> Recording:
    """Generate deterministic EEG-like data without requiring physical hardware."""
    settings = config or SyntheticConfig()
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        raise ValueError("duration_seconds must be a positive finite number")
    if not condition:
        raise ValueError("condition must not be empty")
    if alpha_multiplier is None:
        alpha_multiplier = (
            settings.alpha_reactivity_multiplier
            if condition.lower() in {"eyes_closed", "ec"}
            else 1.0
        )
    if not math.isfinite(alpha_multiplier) or alpha_multiplier < 0:
        raise ValueError("alpha_multiplier must be finite and non-negative")

    sample_count = round(duration_seconds * settings.sample_rate_hz)
    if sample_count < 1:
        raise ValueError("duration_seconds is shorter than one sample")

    rng = random.Random(settings.seed)
    component_frequencies = [
        frequency for frequency, _ in settings.oscillations_uv
    ] + [settings.alpha_frequency_hz, settings.line_noise_frequency_hz]
    phases = [
        [
            rng.uniform(0.0, 2.0 * math.pi)
            for _ in component_frequencies
        ]
        for _ in settings.channel_names
    ]
    blink_envelope = [0.0] * sample_count
    muscle_mask = [False] * sample_count
    blink_length = max(1, round(0.2 * settings.sample_rate_hz))
    muscle_length = max(1, round(0.1 * settings.sample_rate_hz))
    for sample_index in range(sample_count):
        if rng.random() < settings.blink_rate_hz / settings.sample_rate_hz:
            end = min(sample_count, sample_index + blink_length)
            for index in range(sample_index, end):
                progress = (index - sample_index) / blink_length
                blink_envelope[index] += math.sin(math.pi * progress)
        if rng.random() < settings.muscle_burst_rate_hz / settings.sample_rate_hz:
            end = min(sample_count, sample_index + muscle_length)
            muscle_mask[sample_index:end] = [True] * (end - sample_index)

    rows: list[tuple[float, ...]] = []
    for sample_index in range(sample_count):
        elapsed = sample_index / settings.sample_rate_hz
        row = []
        for channel_index in range(len(settings.channel_names)):
            value = rng.gauss(0.0, settings.noise_amplitude_uv)
            phase_index = 0
            for frequency, amplitude in settings.oscillations_uv:
                value += amplitude * math.sin(
                    2.0 * math.pi * frequency * elapsed
                    + phases[channel_index][phase_index]
                )
                phase_index += 1
            value += (
                settings.alpha_amplitude_uv
                * alpha_multiplier
                * math.sin(
                    2.0 * math.pi * settings.alpha_frequency_hz * elapsed
                    + phases[channel_index][phase_index]
                )
            )
            phase_index += 1
            value += settings.line_noise_amplitude_uv * math.sin(
                2.0 * math.pi * settings.line_noise_frequency_hz * elapsed
                + phases[channel_index][phase_index]
            )
            value += settings.blink_amplitude_uv * blink_envelope[sample_index]
            if muscle_mask[sample_index]:
                value += rng.gauss(0.0, settings.muscle_amplitude_uv)
            row.append(value)
        rows.append(tuple(row))

    return Recording(
        recording_id=str(uuid.uuid4()),
        sample_rate_hz=settings.sample_rate_hz,
        channel_names=settings.channel_names,
        samples_uv=tuple(rows),
        timestamps_seconds=tuple(
            sample_index / settings.sample_rate_hz
            for sample_index in range(sample_count)
        ),
        metadata={
            "data_status": "simulated",
            "device_model": "synthetic",
            "channel_units": "microvolts",
            "timestamp_semantics": "synthetic_elapsed_seconds",
            "condition": condition,
            "alpha_multiplier": alpha_multiplier,
            "random_seed": settings.seed,
            "configuration": {
                "oscillations_uv": [
                    [frequency, amplitude]
                    for frequency, amplitude in settings.oscillations_uv
                ],
                "alpha_frequency_hz": settings.alpha_frequency_hz,
                "alpha_amplitude_uv": settings.alpha_amplitude_uv,
                "alpha_reactivity_multiplier": settings.alpha_reactivity_multiplier,
                "line_noise_frequency_hz": settings.line_noise_frequency_hz,
                "line_noise_amplitude_uv": settings.line_noise_amplitude_uv,
                "noise_amplitude_uv": settings.noise_amplitude_uv,
                "blink_rate_hz": settings.blink_rate_hz,
                "blink_amplitude_uv": settings.blink_amplitude_uv,
                "muscle_burst_rate_hz": settings.muscle_burst_rate_hz,
                "muscle_amplitude_uv": settings.muscle_amplitude_uv,
            },
        },
    )
