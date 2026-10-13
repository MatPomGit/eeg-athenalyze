# Muse S Athena: błąd GATT na Windows 11

## Zaobserwowany problem (13.10.2026)
Urządzenie o nazwie reklamowanej `MuseS-C87B` jest sparowane z Windows. BrainFlow wykrywa adapter i urządzenie oraz raportuje `Connected to MuseAthena Device`, ale `prepare_session()` kończy się komunikatami `failed to find control characteristic` i `BOARD_NOT_READY_ERROR:7`. **Nie było jeszcze próbek EEG.** Wersja firmware, lista rzeczywistych usług GATT i wersja BrainFlow użyta podczas błędu pozostają niepotwierdzone.

## Co oznacza ten błąd
Obsługa Athena w BrainFlow oczekuje usługi BLE `FE8D` i charakterystyki sterującej `273e0001-4c4d-454d-96be-f03bac821358`. Połączenie radiowe może działać mimo braku oczekiwanego profilu usług. Możliwe przyczyny: inny model/protokół firmware, konflikt aplikacji BLE, niepełna enumeracja GATT Windows albo niezgodność wersji BrainFlow. Zmiana presetu EEG następuje za późno, aby naprawić brak charakterystyki.

## Diagnostyka bez zapisu do opaski

1. Zamknij aplikacje Muse, które mogły połączyć się z opaską. Rozłącz też telefon. Wyłącz/włącz Bluetooth i ponownie uruchom opaskę.
2. W `.venv` wykonaj `python -m pip show brainflow` i zachowaj numer wersji.
3. Uruchom:

```powershell
.\.venv\Scripts\python.exe -m pip install bleak
.\.venv\Scripts\python.exe tools\diagnose_muse_gatt.py --name MuseS-C87B
```

Skrypt **tylko odczytuje** wykrywane UUID usług i sprawdza obecność charakterystyki. Nie wysyła poleceń do firmware ani nie zapisuje danych w opasce.

4. Gdy obie oczekiwane wartości są obecne, ponów pojedynczą próbę:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[muse]"
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --serial-number MuseS-C87B --discovery-timeout 20 --duration 30 --output data\local\athena-retry.eegz
```

Wybierz nową nazwę pliku, jeżeli docelowe archiwum lub dziennik częściowych próbek już istnieje. **Nie usuwaj** plików `.partial.jsonl` po przerwanym nagraniu. Sprawdzenie samych deskryptorów komendą `devices check` nie ustanawia połączenia BLE.

5. Gdy brak usługi FE8D albo charakterystyki sterującej, nie wykonuj wielokrotnych niekontrolowanych prób. Trzeba ustalić rzeczywisty wariant sprzętu i firmware, a następnie porównać jego profil GATT z implementacją BrainFlow. Nie zmieniaj automatycznie identyfikatora na starszy `MUSE_S_BOARD`.

## Materiały referencyjne
- https://brainflow.readthedocs.io/en/stable/SupportedBoards.html
- https://brainflow.org/2026-05-08-muse-anthena/

Wynik eksperymentu sprzętowego pozostaje **NIEZWERYFIKOWANY** do uzyskania rzeczywistych próbek, kontroli ciągłości i jakości sygnału.
