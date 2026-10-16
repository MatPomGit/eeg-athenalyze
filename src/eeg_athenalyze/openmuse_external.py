"""Optional external OpenMuse raw packet capture; no EEG decoding or timing claims."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def _executable(command: str) -> str:
    executable = shutil.which(command)
    if executable is None:
        raise RuntimeError(
            f"OpenMuse executable {command!r} not found. Install OpenMuse in a "
            "separate environment and pass --openmuse-executable with its full path."
        )
    return executable


def find_openmuse(*, executable: str = "OpenMuse") -> int:
    """Print upstream-discovered device identifiers for explicit user selection."""
    return subprocess.run([_executable(executable), "find"], check=False).returncode


def capture_openmuse(
    address: str, output: Path, *, duration: float = 60.0,
    executable: str = "OpenMuse",
) -> Path:
    """Invoke upstream raw recording in a separate process, preserving its native file.

    No reconnection, forced LSL conversion, EEGZ synthesis, or overwrite.
    """
    import math
    if not address.strip():
        raise ValueError("OpenMuse address from 'OpenMuse find' is required")
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Duration must be a positive finite number")
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"OpenMuse output already exists: {output}")
    # Do not reuse an existing unfinished output or silently create it.
    output.parent.mkdir(parents=True, exist_ok=True)
    args = [_executable(executable), "record", "--address", address,
            "--duration", str(duration), "--outfile", str(output)]
    result = subprocess.run(args, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"OpenMuse record failed (exit {result.returncode}); inspect the raw "
            f"output if created, do not classify it as a complete session: {output}"
        )
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("OpenMuse reported success but did not create nonempty raw output")
    return output
