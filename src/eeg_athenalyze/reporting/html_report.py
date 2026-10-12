"""Self-contained HTML report generation for resting-state recordings."""

from __future__ import annotations

import html
import math
import os
from pathlib import Path
import tempfile

from eeg_athenalyze.analysis.spectral import AlphaComparison
from eeg_athenalyze.recording import Recording


def write_resting_report(
    recording: Recording,
    comparison: AlphaComparison,
    destination: str | Path,
) -> Path:
    """Write a compact, self-contained report without replacing existing files."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    bars = []
    maximum = max(
        (*comparison.eyes_open_uv2.values(), *comparison.eyes_closed_uv2.values()),
        default=0.0,
    )
    for index, channel in enumerate(recording.channel_names):
        open_power = comparison.eyes_open_uv2[channel]
        closed_power = comparison.eyes_closed_uv2[channel]
        change = comparison.relative_change[channel]
        change_text = f"{change:.1%}" if math.isfinite(change) else "N/A"
        rows.append(
            "<tr>"
            f"<th>{html.escape(channel)}</th>"
            f"<td>{open_power:.3f}</td>"
            f"<td>{closed_power:.3f}</td>"
            f"<td>{change_text}</td>"
            "</tr>"
        )
        open_width = 0.0 if maximum == 0 else 280 * open_power / maximum
        closed_width = 0.0 if maximum == 0 else 280 * closed_power / maximum
        bars.append(
            f'<text x="0" y="{index * 58 + 18}">{html.escape(channel)}</text>'
            f'<rect x="55" y="{index * 58}" width="{open_width:.2f}" height="20" '
            'fill="#4472c4"/>'
            f'<rect x="55" y="{index * 58 + 23}" width="{closed_width:.2f}" '
            'height="20" fill="#ed7d31"/>'
        )

    metadata = recording.metadata
    events = metadata.get("events", [])
    event_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(event.get('condition', '')))}</td>"
        f"<td>{event.get('onset_seconds', 0):.3f}</td>"
        f"<td>{event.get('duration_seconds', 0):.3f}</td>"
        "</tr>"
        for event in events
        if isinstance(event, dict)
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EEG Athenalyze resting-state report</title>
<style>
body {{ font: 16px system-ui, sans-serif; margin: 2rem auto;
max-width: 900px; padding: 0 1rem; }}
table {{ border-collapse: collapse; margin: 1rem 0; }}
th, td {{ border: 1px solid #bbb; padding: .4rem .7rem; text-align: left; }}
.warning {{ border-left: 4px solid #ed7d31; padding: .6rem 1rem; background: #fff5eb; }}
svg {{ max-width: 100%; }} svg text {{ font: 13px sans-serif; }}
</style>
</head>
<body>
<h1>EEG Athenalyze: EO/EC resting-state report</h1>
<p class="warning">Simulated EEG; not a clinical result or a hardware-validated
recording.
Timing and signal quality have not been validated with physical equipment.</p>
<h2>Session</h2>
<dl>
<dt>Participant pseudonym</dt>
<dd>{html.escape(str(metadata.get("participant_id", "unknown")))}</dd>
<dt>Session</dt><dd>{html.escape(str(metadata.get("session_id", "unknown")))}</dd>
<dt>Recording ID</dt><dd>{html.escape(recording.recording_id)}</dd>
<dt>Sample rate</dt><dd>{recording.sample_rate_hz:g} Hz</dd>
<dt>Channels</dt><dd>{html.escape(", ".join(recording.channel_names))}</dd>
<dt>Samples</dt><dd>{len(recording.samples_uv)}</dd>
<dt>Duration</dt>
<dd>{recording.timestamps_seconds[-1]:.3f} s (last sample timestamp)</dd>
</dl>
<h2>Block/event timing</h2>
<table><thead><tr><th>Condition</th><th>Onset (s)</th><th>Duration (s)</th></tr></thead>
<tbody>{event_rows}</tbody></table>
<h2>Alpha-band power (8–13 Hz)</h2>
<p>Values are integrated Welch PSD in &micro;V<sup>2</sup>; the EO/EC change is
descriptive and does not identify a cognitive or clinical state.</p>
<table><thead><tr><th>Channel</th><th>Eyes open (&micro;V<sup>2</sup>)</th>
<th>Eyes closed (&micro;V<sup>2</sup>)</th><th>Relative change</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
<svg viewBox="0 0 360 {max(1, len(recording.channel_names)) * 58}" role="img"
aria-label="Alpha power by channel; blue is eyes open and orange is eyes closed">
{"".join(bars)}
<text x="55" y="{len(recording.channel_names) * 58 - 3}" fill="#4472c4">Eyes open</text>
<text x="155" y="{len(recording.channel_names) * 58 - 3}" fill="#ed7d31">
Eyes closed</text>
</svg>
<h2>Limitations</h2>
<p>This simulated signal is intended for software demonstrations only.
Four-channel recordings provide limited spatial coverage and do not include
occipital electrodes. The report is not a diagnosis, and alpha power alone cannot
uniquely identify cognitive state.</p>
</body></html>
"""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(page)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.link(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return path
