# Muse S Athena: rejestracja rzeczywistego EEG (M03, wersja rozwojowa)

To polecenie służy do **fizycznego pomiaru**, a nie generowania sygnału syntetycznego. Wymaga Muse S Athena, Bluetooth na Windows 11 oraz BrainFlow w izolowanym środowisku.

```powershell
.\.venv\Scripts\python.exe -m pip install ".[muse]"
.\.venv\Scripts\python.exe -m eeg_athenalyze devices check --device muse-athena
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --duration 30 --output data\local\physical-session.eegz
```

Można opcjonalnie wskazać `--serial-number` lub `--mac-address`; nie umieszczaj identyfikatorów urządzenia w repozytorium ani publicznych logach. Archiwum nie zostanie nadpisane.

Moduł rejestruje cztery podstawowe kanały EEG i źródłowe znaczniki czasu BrainFlow. Przed testem na opasce nie można uznać za zweryfikowanej referencji elektrod ani dokładności czasowej. **Eksporter EEG-BIDS nadal przyjmuje wyłącznie dane syntetyczne.**

Akwizycja dopisuje próbki do dziennika `.partial.jsonl` z synchronizacją zapisu na dysk. Po przerwaniu kompletne rekordy pozostają do odzyskania funkcją `eeg_athenalyze.acquisition_journal.recover_journal`; nie są jeszcze automatycznie przekształcane w końcowe archiwum. Dziennik jest usuwany dopiero po prawidłowym utworzeniu `.eegz`. Nie usuwaj pliku dziennika po awarii.

Ograniczenia: końcowe tworzenie archiwum nadal wczytuje próbki do RAM, a odzyskiwanie częściowych nagrań nie posiada jeszcze interfejsu dla początkujących. Długie badania, wykrywanie utraty pakietów, dodatkowe presety i kontrola jakości na sprzęcie wymagają dalszej implementacji. Zobacz [TODO](../../TODO.md).


## Błąd „Invalid EEG chunk or source timestamps”

Ten komunikat pochodzi z lokalnego dziennika akwizycji, a nie bezpośrednio z BLE. Może oznaczać błędną liczbę kanałów, próbkę o wartości NaN/Inf lub powtarzający się albo cofający znacznik czasu BrainFlow. W najnowszej poprawce komunikat zawiera indeks próbki, poprzedni i aktualny znacznik czasu oraz różnicę. Nie należy usuwać ani przestawiać próbek automatycznie. Jeżeli transmisja została rozpoczęta, zachowaj plik `.partial.jsonl` do zbadania.

Zaktualizuj lokalną gałąź, przeinstaluj pakiet poleceniem `.\\.venv\\Scripts\\python.exe -m pip install -e ".[muse]"`, wykonaj pojedynczy krótki pomiar pod **nową nazwą** i przekaż sam tekst nowego błędu, bez prywatnych identyfikatorów urządzenia.
