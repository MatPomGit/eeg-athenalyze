# Windows 11 quick start (synthetic EEG)

This tutorial uses a **synthetic** recording. It does not connect to the Muse S Athena headband. Physical device acquisition, PsychoPy, and EEG-BIDS export are not implemented in the current MVP.

## Prerequisites
Install Python 3.12 for Windows, including the Python launcher (`py`), and Git. No administrator privileges should be necessary for ordinary project installation.

## Steps
1. Clone the repository: `git clone https://github.com/MatPomGit/eeg-neurolyze.git`.
2. Open the repository's `windows` directory and run `setup_environment.bat` once. This creates an isolated `.venv` and installs the package into it.
3. Run `run_synthetic_demo.bat`. The launcher checks the environment and executes a shortened EO/EC synthetic experiment using seed 42.
4. Open the new `.html` report in `data/demo/`. The corresponding `.eegz` archive contains the original synthetic samples, elapsed timestamps, metadata and a SHA-256 manifest.
5. To reanalyze existing data, execute from the repository root:

   ```powershell
   .\.venv\Scripts\python.exe -m eeg_athenalyze analyze --session "data\demo\<ARCHIVE_NAME>.eegz"
   ```

   Replace `<ARCHIVE_NAME>` with a generated file name. Existing raw archives are not overwritten.

The default protocol comprises stabilization (30 s), eyes open (120 s), break (30 s), and eyes closed (120 s). The demo uses `--duration-scale 0.05` solely to finish faster.

## Interpreting results
Inspect the per-channel alpha-band power (8–13 Hz) and EO/EC comparison. These are artificial signals, not observations from a participant. The four channel labels are TP9, AF7, AF8 and TP10.

## Troubleshooting
- **`py -3.12` not found:** install Python 3.12 and the Windows Python launcher.
- **Missing environment:** run `setup_environment.bat`.
- **Dependency installation fails:** check connectivity to your configured Python package index.
- **Existing output name:** the experiment uses a new session ID. Never manually overwrite a completed archive.

## Data standards
Native `.eegz` is an internal, checksummed format, **not BIDS**. BIDS conversion and formal validator integration remain separate planned milestones.
