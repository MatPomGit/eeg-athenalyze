# Agent development instructions

This is **EEG Neurolyze** (`MatPomGit/eeg-neurolyze`). The existing Python distribution, module and executable are temporarily called `eeg-athenalyze` / `eeg_athenalyze`; see [ADR-0006](docs/architecture/adr/0006-project-naming.md). Do not break those interfaces without a reviewed migration.

## Required reading before implementation
1. [Project concept](docs/architecture/PROJECT-CONCEPT.md)
2. [Architecture decisions](docs/architecture/adr/README.md)
3. [Milestones and verification gates](docs/architecture/ROADMAP.md)
4. [Existing implementation specification](Complete-Implementation-Specification.md) (historical name; use repository's actual identity)

## Engineering rules
- Work in small tested vertical slices. Inspect code and tests before edits; do not generate empty placeholders.
- Windows 11 is the primary user platform. Invoke local isolated `.venv` interpreters and do not install packages globally.
- Preserve original EEG samples and available timestamps; never modify source archives or overwrite completed sessions.
- Never claim real device success based on simulated data. A simulator must be labeled in CLI, filenames/metadatas and reports.
- Keep BrainFlow device adapters separate from PsychoPy tasks and MNE analyses. LSL timing needs explicit clock-domain metadata and actual validation before latency-sensitive claims.
- BIDS compliance requires supported file formats, real sidecars, official validator with no blocking errors and MNE round-trip checks; BIDS-like directory names alone are insufficient.
- For physical Muse S Athena, verify channel mappings, units, reference, timestamps, BLE behavior and firmware/API against trustworthy sources and on-device measurements.
- PsychoPy Builder and Python API should share event semantics. Preserve observed vs intended event timing.
- Protect human-subject data; pseudonymize and exclude recordings and credentials from commits, logs and cloud uploads.
- Write code/comments/CLI in English. Update student documentation in **both English and Polish** whenever instructional steps change.
- PEP 8, typing, focused tests and failure diagnostics are mandatory. Do not add global dependencies or autonomous PR sprawl.
- Never conflate **accepted architecture**, **implemented code**, **tested software** and **hardware-validated** functionality.

## Pull request checklist
- State decision/ADR and milestone impacted.
- Describe implementation, migration, risks, changed commands and privacy implications.
- Include actual test commands and results, never projected outcomes.
- Update README and PL/EN docs for user-facing behavior.
- Add or supersede an ADR for a significant architectural change; never silently rewrite accepted decisions.

## Near-term priority
Finish M02: MNE-BIDS BrainVision export of synthetic EO/EC archives, compliant event/channel metadata, official validator and read-back checks. Keep the hardware acquisition and PsychoPy integration in bounded separate PRs.

## GitHub Actions: reguły dla agentów AI

- Stosuj domyślnie `workflow_dispatch` **wyłącznie na gałęzi `main`**. Nie uruchamiaj testów Actions dla PR lub gałęzi roboczych; sprawdzaj je lokalnie.
- Automatyczne wywołanie dopuszczalne jest tylko dla niezbędnego procesu po `push` na `main`, z wąskim `paths` i warunkiem jobu `github.ref == 'refs/heads/main'`; nie przywracaj automatycznych CI bez zgody.
- Unikaj kosztownych testów sprzętowych EEG/Muse na zewnętrznym runnerze i nie deklaruj testu rzeczywistego urządzenia, jeśli wykonano wyłącznie mock.
- Żaden agent nie może omijać polityki przez tagi, PR, `workflow_run`, `repository_dispatch` czy `always()`. Ręczny wybór innej gałęzi może utworzyć pominięte wykonanie; używaj tylko `main`.
