# EEG Athenalyze: Complete Implementation Specification

## 1. Mission

Act as a senior Python engineer, EEG/neuroinformatics specialist, experimental neuropsychologist, PsychoPy developer, and scientific software architect.

Implement **EEG Athenalyze** in `MatPomGit/eeg-athenalyze`: a modular, open-source platform for EEG acquisition, experimental psychology, neuropsychology, signal processing, visualization, reproducible research, and future BCI development.

**Target OS:** Windows 11  
**Hardware:** Muse S Athena  
**Core:** Python 3.12, BrainFlow, MNE-Python, MNE-BIDS  
**Experiments:** PsychoPy Builder and PsychoPy Python API  
**Synchronization:** Lab Streaming Layer (LSL)  
**Data standard:** EEG-BIDS and BIDS Derivatives  
**Interface/code:** English  
**Educational documentation:** English and Polish

The goal is a **working end-to-end system**, not merely scaffolding, mockups, or documentation.

Inspect the existing repository first. Preserve working implementations. Implement missing functionality incrementally, run tests, fix errors, and update documentation.

## 2. Architecture

Separate the system into independent layers:

1. `core`: configuration, models, provenance, events.
2. `devices`: Muse S Athena, synthetic EEG, future devices.
3. `acquisition`: streaming, buffering, timestamps, recording integrity.
4. `experiments`: protocols, conditions, blocks, trials, registry.
5. `integrations`: PsychoPy API, Builder, LSL, XDF.
6. `synchronization`: clock alignment, markers, timing validation.
7. `datasets`: native archives, BIDS export, validation, derivatives.
8. `preprocessing`: MNE filters, artifacts, epochs, referencing.
9. `analysis`: PSD, band power, features, experimental comparisons.
10. `visualization`: EEG traces, spectra, spectrograms, dashboards.
11. `reporting`: results, quality metrics, HTML reports.
12. `education`: bilingual documentation and laboratory tutorials.

Requirements:

- Use a Python `src/` layout.
- Implement reusable interfaces and a device registry.
- Use typed, validated YAML experiment configurations.
- Keep device acquisition independent from experimental presentation.
- Keep analysis independent from hardware.
- Preserve backward compatibility where practical.
- Do not duplicate analytical logic in scripts, notebooks, or PsychoPy experiments.
- Support future EEG devices, experimental protocols, algorithms, and visualizations through documented extension interfaces.

Suggested repository structure:

```text
eeg-athenalyze/
├── README.md
├── README.pl.md
├── AGENTS.md
├── LICENSE
├── CITATION.cff
├── CONTRIBUTING.md
├── CHANGELOG.md
├── SECURITY.md
├── pyproject.toml
├── .gitignore
├── .github/workflows/
├── src/eeg_athenalyze/
│   ├── cli.py
│   ├── core/
│   ├── devices/
│   ├── acquisition/
│   ├── experiments/
│   ├── integrations/
│   ├── synchronization/
│   ├── datasets/
│   ├── preprocessing/
│   ├── analysis/
│   ├── visualization/
│   └── reporting/
├── psychopy/
│   ├── builder_templates/
│   ├── scripted_experiments/
│   ├── stimuli/
│   └── conditions/
├── experiments/
│   ├── eyes_open_closed/
│   ├── resting_state/
│   ├── stroop/
│   ├── nback/
│   └── templates/
├── config/
│   ├── devices/
│   ├── experiments/
│   ├── preprocessing/
│   └── analysis/
├── windows/
├── examples/
├── notebooks/
├── education/
│   ├── en/
│   └── pl/
├── docs/
│   ├── en/
│   └── pl/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── hardware/
│   ├── synchronization/
│   └── bids/
├── data/
└── reports/
```

Do not create empty placeholder files for unimplemented features. Keep experimental data, virtual environments, private information, and generated results outside Git.

## 3. Muse S Athena and BrainFlow

Implement a real BrainFlow hardware adapter using the Athena-specific board identifier, `BoardIds.MUSE_S_ATHENA_BOARD`, after verifying the installed BrainFlow API.

Verify current official documentation for:

- BLE connection requirements on Windows 11.
- Four principal EEG electrodes: TP9, AF7, AF8, TP10.
- Nominal 256 Hz EEG sampling.
- Channel ordering and data units.
- Supported acquisition presets.
- Additional auxiliary sensors and streams.
- BrainFlow timestamps and clock semantics.
- Firmware-dependent capabilities.

Do not confuse additional Athena EEG-like values with independent scalp electrodes.

Implement:

- Connection diagnostics and channel verification.
- Safe session initialization and cleanup.
- Start/stop recording.
- Continuous buffering.
- Timestamp preservation.
- Detection of suspicious gaps or sample-count mismatches.
- Signal-quality indicators.
- Interrupted-recording recovery.
- Clear device and connection errors.

Create a reproducible **synthetic EEG adapter** with configurable sample rate, channel count, random seed, oscillations, alpha reactivity, line noise, and blink/muscle-like artifacts.

Synthetic acquisition must support all standard processing workflows without physical hardware. Clearly label simulated data.

Never claim hardware validation without testing the physical device.

## 4. Isolated Python environments

All execution must use local virtual environments. Never install application packages globally.

Use two independent runtimes:

| Environment | Python | Responsibility |
|---|---|---|
| `.venv` | 3.12 | BrainFlow, MNE, acquisition, processing, BIDS, reports |
| `.venv-psychopy` | 3.11 initially | PsychoPy, stimuli, behavioral responses, LSL markers |

Verify PsychoPy/Python compatibility before pinning dependencies. Support PsychoPy Standalone as an optional alternative.

Manage dependencies through `pyproject.toml` and reproducible lock or constraint files.

Windows launchers must use explicit Python paths:

```bat
.venv\Scripts\python.exe
.venv-psychopy\Scripts\python.exe
```

Implement environment setup scripts:

- `setup_environment.bat`
- `setup_psychopy.bat`
- `check_environment.bat`

The installers must detect Python, initialize environments, install pinned dependencies, verify imports, and return meaningful errors.

Environment setup must be idempotent. Experiments must never silently install or upgrade packages.

Do not share `site-packages` between environments.

## 5. PsychoPy integration: Builder and Python API

**Use PsychoPy as the primary stimulus and behavioral experiment engine.**

Support both:

1. **PsychoPy Builder:** editable `.psyexp` experiment templates for students.
2. **PsychoPy Python API:** programmatic experiment creation, execution, and advanced control.

Official API reference:  
https://psychopy.org/api/index.html

Use relevant official modules:

- `psychopy.visual`: visual stimuli, windows, text, shapes, images.
- `psychopy.core` and `psychopy.clock`: clocks, timing, execution control.
- `psychopy.data`: experiment handlers, trial handling, behavioral results.
- `psychopy.hardware.keyboard`: keyboard responses where supported.
- `psychopy.event`: appropriate input handling.
- `psychopy.sound`: auditory stimuli.
- `psychopy.session`: session orchestration where useful.
- `psychopy.iohub`: synchronized event monitoring where appropriate.
- `psychopy.gui`: participant/session dialogs.
- `psychopy.logging`: experiment diagnostics.

Consult the current PsychoPy API before implementing.

Use Builder for introductory experiments and the Python API for advanced dynamic paradigms. Both approaches must use the same experiment metadata and event conventions.

Implement:

- Stimulus presentation.
- Trial randomization and counterbalancing.
- Accurate behavioral reaction-time recording.
- Response accuracy.
- Experiment instructions.
- Trial/block/event state tracking.
- Frame timing diagnostics.
- Export of behavioral data.
- Event-marker publication to LSL.

Use `Window.callOnFlip()` or another validated frame-synchronized method for stimulus onset markers when appropriate.

Distinguish intended, software-measured, and physically verified stimulus onset times.

Do not assume millisecond-level synchronization accuracy without experimental validation.

PsychoPy must remain optional for resting-state acquisition and offline analysis.

## 6. LSL synchronization

Implement bidirectional experiment coordination and LSL-based stream integration.

Architecture:

```text
Muse S Athena → BrainFlow → EEG stream ──┐
                                         ├→ Synchronized session
PsychoPy → Stimulus/response markers ────┘
                    ↓
          Native archive / XDF
                    ↓
             EEG-BIDS export
                    ↓
          MNE processing / analysis
```

Support:

- EEG and marker streams.
- Unique event IDs.
- Trial and condition identifiers.
- Host/source timestamps and clock-domain metadata.
- Clock correction and drift diagnostics.
- Optional XDF recording.
- Offline event alignment.
- Latency and discontinuity reporting.

Preserve BrainFlow source timing information. Do not treat LSL timestamp corrections as proof that BLE transmission delays have been eliminated.

Provide tests using known synthetic marker sequences.

Document a real-hardware timing validation protocol, including optional photodiode-based stimulus verification.

Event-related analyses requiring precise onset timing must remain marked unvalidated until synchronization performance is measured.

## 7. Extensible experiment engine

Create:

- `ExperimentDefinition`
- `ExperimentCondition`
- `ExperimentBlock`
- `ExperimentTrial`
- `ExperimentEvent`
- `ExperimentRunner`
- `ExperimentRegistry`
- `ExperimentResult`

Each experiment must define:

- Research objective and hypothesis.
- Participant instructions.
- Conditions and trial structure.
- Timing and repetitions.
- Randomization/counterbalancing.
- Stimuli and responses.
- Device requirements.
- Event markers.
- Processing and analysis settings.
- Output specification.

Use versioned YAML configurations with schema validation.

**Implement the following initial experiments:**

### EO/EC resting-state EEG

First mandatory complete end-to-end implementation:

- 30 s stabilization.
- 120 s eyes open.
- 30 s break.
- 120 s eyes closed.
- Raw EEG recording.
- Condition markers.
- Quality control.
- PSD and alpha-power analysis.
- BIDS export.
- Automated report.

Support configurable durations, repeated blocks, and counterbalanced order.

Must operate with real or synthetic devices and must not require PsychoPy.

### Stroop

Implement a PsychoPy visual Stroop experiment:

- Congruent/incongruent stimuli.
- Randomized trials.
- Response collection.
- Reaction times and errors.
- EEG markers.
- Behavioral and EEG analyses.
- BIDS events.

### N-back

Implement an introductory working-memory experiment:

- Configurable N-back level.
- Visual stimuli.
- Trial sequence.
- Target/non-target conditions.
- Reaction time and accuracy.
- EEG markers and condition comparisons.

Provide editable Builder templates and/or equivalent PsychoPy API implementations where practical.

Additional planned experiments:

- Oddball.
- Go/No-Go.
- Continuous Performance Test.
- Attention tasks.
- Emotional stimulation.
- Stress and relaxation.
- Motor imagery.
- Neurofeedback.
- BCI experiments.

Do not register unfinished protocols as working experiments.

## 8. CRITICAL: Reliable raw EEG preservation

Every session must produce an immutable native acquisition archive before preprocessing.

Preserve:

- Original sample values and data types.
- Source channel mapping and units.
- Available timestamps.
- Sample rate and device parameters.
- Stream discontinuities and warnings.
- Condition and event metadata.
- Device/firmware information when available.
- Python/package versions.
- Experiment configuration and version.
- Recording provenance.

Use a lossless format such as NumPy NPZ with metadata or another justified native representation.

Requirements:

- SHA-256 integrity checks.
- Safe/atomic file finalization.
- Read-back verification.
- Unique session identifiers.
- Explicit incomplete-session status.
- No silent data overwrite.
- Source recordings never modified by preprocessing.
- Ability to reanalyze recordings with different parameters.

Separate raw EEG, event logs, auxiliary streams, processed data, and reports.

Never reconstruct timestamps from nominal sampling rate while misrepresenting them as measured hardware timestamps.

## 9. MANDATORY EEG-BIDS compliance

Implement real EEG-BIDS export, not merely BIDS-like filenames.

Official references:

https://bids-specification.readthedocs.io/en/stable/

https://mne.tools/mne-bids/stable/

https://github.com/bids-standard/bids-validator

Use **MNE-BIDS** for standardized export.

Prefer **BrainVision** as the raw EEG-BIDS export format:

- `.vhdr`
- `.vmrk`
- `.eeg`

Install and verify required conversion dependencies.

Keep the original acquisition archive separately from converted BIDS data.

Use valid BIDS identifiers and naming conventions.

Target example:

```text
data/bids/ds-eegathenalyze/
├── dataset_description.json
├── README
├── participants.tsv
├── participants.json
├── sub-001/
│   └── ses-01/
│       └── eeg/
│           ├── sub-001_ses-01_task-rest_eeg.vhdr
│           ├── sub-001_ses-01_task-rest_eeg.vmrk
│           ├── sub-001_ses-01_task-rest_eeg.eeg
│           ├── sub-001_ses-01_task-rest_eeg.json
│           ├── sub-001_ses-01_task-rest_channels.tsv
│           ├── sub-001_ses-01_task-rest_events.tsv
│           └── sub-001_ses-01_task-rest_events.json
└── derivatives/
    └── eeg-athenalyze/
        ├── dataset_description.json
        └── sub-001/
            └── ...
```

Generate only files applicable to each recording.

Metadata requirements:

- Dataset description and specification version.
- Pseudonymous participant information.
- Sampling frequency.
- EEG channel names, types, and units.
- Device model/manufacturer where verified.
- Reference scheme.
- Power-line frequency and software-filter information.
- Recording duration and type.
- Task description.
- Event onset, duration, condition, response and reaction time where applicable.

For unknown properties, document uncertainty rather than inventing values.

Muse S Athena channel locations must not be described as measured electrode coordinates without supporting evidence.

For events, calculate onsets relative to the corresponding EEG recording start. Preserve original event timestamps and any known synchronization uncertainty.

### BIDS Derivatives

Keep processed data outside the raw BIDS dataset content.

Store:

- Filtering and preprocessing parameters.
- Bad-channel/epoch information.
- PSD.
- Band-power metrics.
- Experimental contrasts.
- Figures.
- Quality metrics.
- Provenance.

Use valid derivatives metadata including `GeneratedBy` and source references.

If a custom analytical output does not have a standardized BIDS Derivatives representation, document it as an extension without falsely claiming full compliance.

### Formal validation

Implement:

```powershell
eeg-athenalyze bids export --session SESSION_ID
eeg-athenalyze bids validate --dataset DATASET_PATH
```

Invoke the **official BIDS Validator**, using a verified compatible installation.

- Record validator version.
- Preserve errors and warnings.
- Treat validation errors as blocking.
- Do not claim BIDS compliance when validation fails.
- Make validation reproducible in CI.

### Round-trip test

Generate synthetic EEG, save the native archive, export BrainVision EEG-BIDS, reopen it using MNE, and compare:

- Channel count and labels.
- Sampling frequency.
- Sample count.
- Numerical data within encoding tolerance.
- Event alignment.
- Metadata.

Run the BIDS Validator on the exported dataset.

## 10. Preprocessing, analytics and visualization

Implement configurable, reusable MNE pipelines.

### Preprocessing

- Data import.
- Unit conversion.
- Channel metadata.
- Bad-channel detection.
- Referencing.
- High-pass/low-pass filtering.
- Optional notch filtering.
- Artifact annotation.
- Epoching.
- Bad-epoch rejection.
- Quality-control reports.

Use approximately 1–40 Hz as the introductory default only, not a universal configuration.

Account for gaps and filter edge effects.

Do not apply ICA by default to four-channel Muse recordings.

### Analysis

Implement:

- Welch PSD.
- Absolute band power.
- Relative band power.
- Delta/theta/alpha/beta/low-gamma bands.
- Alpha peak frequency where estimable.
- Per-channel analysis.
- EO/EC alpha comparison.
- Condition-level summary statistics.
- Introductory behavioral/EEG comparisons.

Make band boundaries, algorithms, and parameters configurable.

Document physiological limitations, including the absence of occipital electrode coverage and limited spatial sampling.

Do not infer psychiatric diagnoses or uniquely identify cognitive states from EEG band power.

### Visualization

Implement publication-quality:

- Raw EEG traces.
- Filtered EEG.
- PSD plots.
- Spectrograms.
- Band-power comparisons.
- Artifact/QC plots.
- Trial and event timelines.
- Behavioral results.
- EEG/behavior comparisons.

Export PNG and SVG with correct units and labels.

Prepare extensible interfaces for future interactive visualization and live EEG dashboards.

### Reporting

Produce HTML reports containing:

- Participant pseudonym and session ID.
- Experiment parameters.
- Channel/device information.
- Recording quality.
- BIDS validation status.
- Spectral and behavioral results.
- Figures.
- Interpretation and limitations.
- Processing configuration and software versions.

Do not report successful analysis if critical processing or validation stages failed.

## 11. Windows one-click workflows

Create:

```text
windows/
├── setup_environment.bat
├── setup_psychopy.bat
├── check_environment.bat
├── check_device.bat
├── run_synthetic_demo.bat
├── run_eyes_open_closed.bat
├── run_stroop.bat
├── run_nback.bat
├── run_experiment.bat
├── preprocess_eeg.bat
├── analyze_eeg.bat
├── export_bids.bat
├── validate_bids.bat
└── generate_report.bat
```

Scripts must:

- Work by double-click on Windows 11.
- Resolve repository root dynamically.
- Use project virtual environments.
- Handle spaces in file paths.
- Check prerequisites.
- Display readable progress and errors.
- Return correct exit codes.
- Avoid requiring administrator privileges.
- Never delete or overwrite raw data automatically.

Do not duplicate Python logic inside `.bat` files.

**Complete workflow:**

Environment validation → device check → participant/session initialization → experiment → acquisition → synchronization → raw save → integrity check → BIDS export → BIDS validation → preprocessing → analysis → figures → report.

The synthetic workflow must run end to end without hardware.

The real workflow must never silently fall back to synthetic acquisition.

Offline analysis must work without reacquiring EEG.

## 12. CLI

Implement a Typer-based or equivalent CLI.

Target commands:

```powershell
eeg-athenalyze doctor
eeg-athenalyze devices list
eeg-athenalyze devices check --device muse-athena
eeg-athenalyze experiments list

eeg-athenalyze experiment run eyes-open-closed --device synthetic
eeg-athenalyze experiment run eyes-open-closed --device muse-athena
eeg-athenalyze experiment run stroop --device muse-athena

eeg-athenalyze preprocess --session SESSION_ID
eeg-athenalyze analyze --session SESSION_ID
eeg-athenalyze bids export --session SESSION_ID
eeg-athenalyze bids validate --dataset DATASET_PATH
eeg-athenalyze report --session SESSION_ID
```

Implement and test commands before presenting them in documentation as available.

Allow configuration-driven selection of experimental protocol, device, participant, session, analysis parameters, and output location.

## 13. Educational documentation

Create equivalent **English and Polish** educational materials.

English is the default software language.

Six laboratory modules:

1. EEG acquisition with Muse S Athena.
2. EEG preprocessing and artifact detection.
3. Spectral EEG analysis.
4. EO/EC neuropsychological experiment.
5. PsychoPy stimulus presentation and behavioral experiments.
6. EEG-BIDS, validation, and reproducible research.

Each module must contain:

- Learning objectives.
- Concise theoretical background.
- Requirements.
- Numbered step-by-step procedure.
- Executable commands.
- Expected results.
- Interpretation.
- Troubleshooting.
- Practical exercises.
- Verified scientific references.

Provide a complete Windows 11 beginner tutorial from installation to an automatically generated report.

Include a synthetic-data path for students without Muse hardware.

Keep documentation scientifically accurate, concise, accessible, and consistent with implemented software.

Use MkDocs Material with English/Polish navigation and GitHub Pages publication.

## 14. Public README and project quality

Create a professional English `README.md` and complete Polish `README.pl.md`.

Include:

- Project identity and description.
- Accurate feature list.
- Architecture diagram.
- Supported devices.
- Installation.
- Quick start.
- Windows `.bat` workflows.
- PsychoPy integration.
- Experiment catalog.
- BIDS support.
- Example synthetic plots.
- Documentation links.
- Development roadmap.
- License and citation.
- Contribution guidelines.

Use restrained badges and clear formatting.

Do not fabricate screenshots, scientific findings, hardware compatibility results, or benchmark measurements.

Create `AGENTS.md` describing architectural rules, testing, bilingual documentation, scientific standards, privacy requirements, and development conventions.

Before selecting a license, review compatibility with PsychoPy and other dependencies, especially if bundling or distributing integrated components.

## 15. Privacy and research ethics

Use pseudonymous participant IDs.

Keep identifying information separate from EEG data.

Do not commit, publish, or automatically upload participant recordings.

Implement:

- Protected local data storage.
- Configurable retention.
- Safe logging.
- BIDS-compatible anonymization.
- Date-shifting support for shared datasets.
- Consent/ethics documentation templates.
- Research-data provenance.

Synthetic demonstration files may be published when clearly labeled.

Do not claim that software functionality substitutes for ethics approval.

## 16. Code standards, tests and CI

Follow PEP 8, PEP 257, typing conventions, separation of concerns, and reproducible software engineering.

Use:

- Ruff.
- Mypy.
- Pytest.
- Pre-commit.
- Typed configuration models.
- Structured logging.
- Meaningful exceptions.
- Versioned dependencies.

Create automated tests for:

- Installation and CLI.
- Device interfaces.
- Synthetic acquisition.
- Raw-data integrity.
- Time/clock handling.
- Experiments and conditions.
- PsychoPy integration.
- LSL event alignment.
- EEG preprocessing.
- PSD and band power.
- BIDS export/read-back.
- Official BIDS validation.
- Reporting.
- Windows batch launchers.

Synthetic EO/EC tests must verify a controlled increase in alpha activity.

Run unit/integration tests without physical hardware.

Keep real Muse tests separate and disabled in ordinary CI.

Use economical GitHub Actions with Windows smoke tests, linting, typing, tests, BIDS validation, package build, and documentation build.

Never run untrusted pull-request code on persistent self-hosted runners.

Do not generate excessive PRs, releases, artifacts, or scheduled workflows.

## 17. Implementation milestones

**M01: Core EEG**

- Packaging, CLI and `.venv`.
- Muse and synthetic adapters.
- Native recording and integrity.
- EO/EC experiment.
- Preprocessing, PSD and plots.
- HTML report.
- Windows one-click synthetic workflow.
- Automated tests.

**M02: BIDS**

- MNE-BIDS integration.
- BrainVision export.
- Metadata and events.
- Derivatives.
- Official validation.
- Read-back integrity tests.

**M03: PsychoPy and synchronization**

- `.venv-psychopy`.
- PsychoPy API integration.
- Builder support.
- LSL markers.
- Experiment coordination.
- XDF support.
- Timing diagnostics.

**M04: Cognitive experiments**

- Stroop.
- N-back.
- Behavioral/EEG analysis.
- BIDS events.
- Complete experiment reports.

**M05: Educational platform**

- Six bilingual laboratory guides.
- MkDocs.
- GitHub Pages.
- Tutorials, notebooks and examples.

**M06: Advanced architecture**

Prepare tested extension interfaces for additional EEG devices, ERP, BCI, neurofeedback, machine learning, connectivity, and real-time visualization.

Do not implement speculative analyses merely to increase the feature count.

## 18. Mandatory acceptance criteria

The initial usable system must demonstrate:

1. Reproducible Windows 11 installation.
2. Isolated Python environments.
3. Functional CLI.
4. Complete synthetic EO/EC experiment.
5. Reliable preservation of native EEG.
6. Correct channel and timestamp metadata.
7. Successful preprocessing.
8. Valid PSD and band-power output.
9. Automatically generated figures and HTML report.
10. BrainVision EEG-BIDS export.
11. Passing official BIDS validation for synthetic fixtures.
12. Successful BIDS read-back integrity tests.
13. Separation of raw data and derivatives.
14. No silent overwriting or synthetic fallback.
15. Working Windows `.bat` launchers.
16. Passing relevant automated tests.
17. Accurate English/Polish documentation.
18. Honest reporting of untested hardware and timing-dependent functionality.

Hardware acquisition requires physical Muse S Athena testing before it may be marked verified.

PsychoPy/EEG timing precision requires measured validation before event-related analyses may be considered timing-validated.

## 19. Instructions for GitHub Copilot Agent

Operate as an autonomous implementation agent within the repository.

1. Inspect repository structure, files, dependencies, tests, and documentation.
2. Identify existing implementations and missing functionality.
3. Compare current state against this specification.
4. Prepare a concise, ordered implementation plan.
5. Implement the next incomplete milestone.
6. Write and run relevant automated tests.
7. Fix failures.
8. Update English and Polish documentation.
9. Update README, changelog, and project status.
10. Report completed work, verification evidence, limitations, and next steps.

Do not stop after producing an implementation plan.

Do not create empty directory scaffolds without real functionality.

Prefer small, working, tested feature slices.

Avoid unnecessary dependencies and disruptive rewrites.

Maintain clear distinction between implemented, tested, hardware-validated, and planned features.

Use a minimal number of coherent pull requests.

Do not automatically merge unverified changes.

Where hardware or external services are unavailable, finish synthetic/integration tests and document the remaining validation requirements without inventing results.

**FINAL DIRECTIVE:** Build a functioning, scientifically sound, extensible EEG experimentation system integrating Muse S Athena, PsychoPy API/Builder, LSL, MNE-Python, BIDS, automated Windows workflows, and bilingual teaching materials. Prioritize data integrity, experimental reproducibility, scientific validity, and practical usability over feature count.
