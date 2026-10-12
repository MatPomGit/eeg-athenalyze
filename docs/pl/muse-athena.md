# Muse S Athena: rejestracja rzeczywistego EEG (M03, wersja rozwojowa)

To polecenie służy do **fizycznego pomiaru**, a nie generowania sygnału syntetycznego. Wymaga Muse S Athena, Bluetooth na Windows 11 oraz BrainFlow w izolowanym środowisku.

```powershell
.\.venv\Scripts\python.exe -m pip install ".[muse]"
.\.venv\Scripts\python.exe -m eeg_athenalyze devices check --device muse-athena
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --duration 30 --output data\local\physical-session.eegz
```

Można opcjonalnie wskazać `--serial-number` lub `--mac-address`; nie umieszczaj identyfikatorów urządzenia w repozytorium ani publicznych logach. Archiwum nie zostanie nadpisane.

Moduł rejestruje cztery podstawowe kanały EEG i źródłowe znaczniki czasu BrainFlow. Przed testem na opasce nie można uznać za zweryfikowanej referencji elektrod ani dokładności czasowej. **Eksporter EEG-BIDS nadal przyjmuje wyłącznie dane syntetyczne.**

Ograniczenia: akwizycja odbywa się w pamięci; przerwane sesje nie są jeszcze zachowywane częściowo. Długie badania, wykrywanie utraty pakietów, dodatkowe presety i kontrola jakości na sprzęcie wymagają dalszej implementacji. Zobacz [TODO](../../TODO.md).
