# M02: wyniki analizy alfa jako pochodne danych

Po eksporcie i walidacji syntetycznego zbioru EEG-BIDS wykonaj:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze bids derivatives --session data\demo\NAGRANIE.eegz --dataset data\bids\ds-demo
```

Program tworzy nienadpisywany plik TSV z mocą alfa dla kanałów oraz metadane JSON w `derivatives/eeg-neurolyze/`. Metadane obejmują SHA-256 archiwum źródłowego i informacje o przetwarzaniu; oryginalny plik `.eegz` pozostaje bez zmian.

Jest to **niestandardowa tabela pochodna**, a nie potwierdzenie pełnej zgodności każdego pliku z BIDS Derivatives. Oddzielnie uruchom oficjalny walidator. Referencja rzeczywistego Muse, precyzja znaczników czasu i przetwarzanie rzeczywistych danych nadal wymagają walidacji.
