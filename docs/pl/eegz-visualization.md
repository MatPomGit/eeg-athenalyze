# Podgląd EEGZ z CLI

Instalacja zależności w istniejącym środowisku Windows: ` .\.venv\Scripts\python.exe -m pip install -e ".[muse,plot]" `.

Otwórz cztery wykresy napięcia EEG w osobnych panelach (µV) z osią indeksu próbek i nominalnej częstotliwości próbkowania:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze plot --session data\local\athena-60s.eegz
```

Zapisz PNG bez okna:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze plot --session data\local\athena-60s.eegz --output data\local\athena-60s-plot.png
```

Obejrzyj także **niekompletny** dziennik po rozłączeniu BLE:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze plot --session data\local\eo-repeat.eegz.partial.jsonl
```

Opcja `--time-axis source` pokazuje oryginalne znaczniki czasu, także duplikaty. Domyślny czas `samples` to **nominalny indeks próbek** przy częstotliwości zapisanej w archiwum (dla dzienników 256 Hz), a nie zweryfikowany zegar sprzętowy. Opcja `--max-points 8000` reguluje liczbę punktów renderowanych przez każdą serię, bez modyfikacji oryginalnych danych. Archiwa nie są zmieniane. Brak metadanych EO/EC nie utrudnia podglądu wykresów. Nie używać niepełnych sesji do wnioskowania o reaktywności alfa.
