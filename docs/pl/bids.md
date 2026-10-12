# Eksport EEG-BIDS (M02)

Zainstaluj opcjonalne biblioteki w lokalnym środowisku projektu:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[bids]"
.\.venv\Scripts\python.exe -m eeg_athenalyze bids export --session data\demo\NAGRANIE.eegz --dataset data\bids\ds-demo
.\.venv\Scripts\python.exe -m eeg_athenalyze bids validate --dataset data\bids\ds-demo
```

Zastąp NAGRANIE rzeczywistą nazwą pliku. Katalog docelowy musi być nowy lub pusty; archiwum `.eegz` nie jest nadpisywane. Sprawdzanie zgodności uruchamia **oficjalny** BIDS Validator i zwraca kod błędu przy niepowodzeniu lub braku walidatora. Raport walidacji zapisywany jest obok zbioru danych.

Pierwsza wersja eksportuje wyłącznie **jednorodnie próbkowane dane syntetyczne w mikrovoltach**. Zegary rzeczywistej opaski Muse S Athena, referencja sprzętowa, przerwy transmisji, współrzędne elektrod, synchronizacja zdarzeń i anonimizacja wymagają dalszej walidacji. Sam eksport katalogu nie potwierdza jeszcze zgodności BIDS.

Konwersja do BrainVision może zmienić reprezentację liczbową próbek w granicach tolerancji; program otwiera eksport w MNE-BIDS i porównuje rozmiary oraz wartości sygnału.
