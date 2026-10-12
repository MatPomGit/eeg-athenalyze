# EEG-BIDS export (M02)

Install the optional BIDS environment using the project-local interpreter:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[bids]"
.\.venv\Scripts\python.exe -m eeg_athenalyze bids export --session data\demo\RECORDING.eegz --dataset data\bids\ds-demo
.\.venv\Scripts\python.exe -m eeg_athenalyze bids validate --dataset data\bids\ds-demo
```

Replace RECORDING with a real filename. The dataset destination must be new or empty; original `.eegz` files are never overwritten. Validation uses the **official** external BIDS Validator and returns a nonzero exit code on error or missing validator. Review the validation report alongside the dataset, not inside it.

The initial export accepts **uniformly sampled synthetic streams with known microvolt units**. Real Muse S Athena clocks, hardware reference, gap handling, electrode coordinates, event alignment and anonymization still require measured validation. A generated folder does not prove formal BIDS compliance until the validator passes.

BrainVision conversion can change sample representation within documented numerical tolerance; the exporter reopens the data using MNE-BIDS and verifies sample shape and approximate values.
