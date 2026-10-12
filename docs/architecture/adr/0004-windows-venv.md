# ADR-0004: Isolated Python runtimes and Windows launchers

- Date: 2026-10-12
- Status: Accepted
- Scope: reproducible installation and usability

## Context
PsychoPy and EEG numerical stacks may impose incompatible package/interpreter constraints, while students require repeatable launchers without shell expertise.

## Decision
Use `.venv` (Python 3.12 target) for core acquisition and analysis; use separately validated `.venv-psychopy` (initial Python 3.11 target) for PsychoPy. Lock tested dependencies before research releases. Use minimal `.bat` wrappers invoking explicit environment interpreters, with no silent upgrades, administrative privileges, or fallback to simulated data during real acquisition. `.venv` launchers exist for synthetic workflows; PsychoPy runtime is planned.

## Consequences
Two environments require local setup and stable IPC. Users can re-run independent stages without altering prior acquisitions.

## Alternatives
Global Python packages are not reproducible. One combined environment risks dependency conflicts. Full containers complicate BLE/graphics access on Windows.

## Verification
Windows smoke test, spaces in paths, proper exit codes and exact interpreter/package version reporting.
