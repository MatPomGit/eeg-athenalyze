# Walidacja Muse S Athena na Windows 11

**Status:** instrukcja testu fizycznego. Pomyślne testy GitHub Actions lub diagnoza BrainFlow nie potwierdzają działania opaski.

## Etap 1. Przygotowanie

1. Na Windows 11 włącz Bluetooth. Naładuj opaskę, dopasuj elektrody i odłącz aplikacje, które mogą jednocześnie korzystać z Muse.
2. W katalogu repozytorium uruchom `windows/setup_environment.bat`.
3. Zainstaluj wymagania: `.\.venv\Scripts\python.exe -m pip install ".[muse]"`.
4. Wykonaj: `.\.venv\Scripts\python.exe -m eeg_athenalyze devices check --device muse-athena`. To tylko odczyt deskryptora biblioteki, nie próba BLE.
5. Zapisz wersję Windows i pakietu BrainFlow, model/firmware urządzenia (jeśli dostępne) oraz sposób konfiguracji Bluetooth. Nie publikuj identyfikatorów osobistych lub urządzenia.

## Etap 2. Właściwy pomiar

Zapisz 30 sekund EEG z założoną opaską:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --duration 30 --output data\local\athena-30s.eegz
```

Następnie wykonaj dłuższy pomiar, np. 5 minut, pod inną nazwą. Pliki nie mogą istnieć wcześniej. Nie podawaj identyfikatora uczestnika ani danych osobowych w nazwach plików.

## Etap 3. Kontrola jakości nagrania

Dla obu zapisów:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze devices assess --session data\local\athena-30s.eegz --report data\local\athena-30s-qc.json
```

Sprawdź liczbę próbek, nominalną częstotliwość próbkowania, medianę odstępów między znacznikami, przerwy dłuższe niż 1,5 okresu próbkowania i zakresy sygnału dla każdego kanału. Ręcznie oceń, czy sygnał wykazuje kontakt elektrody, artefakty mrugania i zmianę jakości po poprawieniu kontaktu.

Raport **nie potwierdza** dokładności zegara sprzętowego, braku strat pakietów ani poprawności referencji elektrod. Wymaga to porównania z dostępną telemetrią urządzenia i niezależną weryfikacją.

## Kryteria zakończenia M03

- Stabilny zapis 30 s i 5 min, bez błędu transmisji oraz z powtarzalnym odzyskiwaniem archiwów.
- Wyjaśnione mapowanie TP9/AF7/AF8/TP10, jednostki, częstotliwość, referencja oraz ustawienia BrainFlow.
- Przeanalizowane wszystkie anomalie czasowe, przerwy, nieciągłości i zachowanie po rozłączeniu.
- Brak nadpisywania istniejących danych i brak automatycznej zamiany pomiaru na symulację.
- Udokumentowany wynik rzeczywistego testu wraz z wersją oprogramowania, bez danych identyfikujących.

**Nie oznaczaj M03 jako sprzętowo zweryfikowanego bez wykonania powyższej procedury na fizycznej opasce.**
