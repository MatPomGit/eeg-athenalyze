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

## Interaktywny podgląd i analiza widmowa

W trybie graficznym można powiększać i przesuwać wykres przyciskami na pasku Matplotlib oraz regulować pionową skalę przebiegu suwakiem **Scale (µV)**. Wybrany zakres zapisu można ustalić parametrami `--start` i `--duration`. Parametr `--view` przyjmuje wartości: `trace`, `psd`, `spectrogram`, `all`; `--channel` wybiera kanał. Przy spektrogramie wielokanałowym wyświetlany jest pierwszy kanał (domyślnie TP9), dlatego do badania AF7 użyj `--channel AF7`.

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze plot --session data\local\athena-60s.eegz --view all --channel AF7 --start 5 --duration 20
.\.venv\Scripts\python.exe -m eeg_athenalyze plot --session data\local\athena-60s.eegz --view spectrogram --channel AF8 --output data\local\af8-spectrogram.png
```

PSD i spektrogram są obliczane z próbek przy **nominalnym** fs zapisanym w archiwum, nie ze zweryfikowanej osi czasu. Są to narzędzia eksploracyjne. Duplikaty czasu, artefakty i brak ciągłości BLE ograniczają interpretację częstotliwości; nie wolno traktować widoków jako certyfikacji klinicznej.
