# Muse S Athena Windows 11: GATT control characteristic unavailable

Observed on 2026-10-13: Windows pairs with `MuseS-C87B`; BrainFlow discovers and connects but `prepare_session()` reports `failed to find control characteristic` followed by `BOARD_NOT_READY_ERROR:7`. No EEG samples have yet been recorded.

BrainFlow's Athena driver expects BLE service FE8D and characteristic `273e0001-4c4d-454d-96be-f03bac821358`. A BLE link does not guarantee the correct GATT protocol is exposed. Investigate firmware/model compatibility, BLE competing clients, Windows GATT caching and installed BrainFlow version before changing the streaming preset.

Use the non-destructive diagnostic:

```powershell
.\.venv\Scripts\python.exe -m pip show brainflow
.\.venv\Scripts\python.exe -m pip install bleak
.\.venv\Scripts\python.exe tools\diagnose_muse_gatt.py --name MuseS-C87B
```

The script lists service UUIDs and tests whether the expected Athena FE8D service and control characteristic are available. It never issues device commands or stores the MAC address. Quit competing Muse phone/desktop applications, restart the headband, toggle Bluetooth and repeat once if required.

If both UUIDs exist, try a uniquely named output with `--serial-number MuseS-C87B --discovery-timeout 20` after `pip install -e ".[muse]"`. Preserve any `.partial.jsonl` recovery journal. If UUIDs are missing, do not switch silently to the older Muse board ID or repeatedly change presets. Compare actual BLE GATT layout and firmware against the BrainFlow driver.

Documentation: https://brainflow.readthedocs.io/en/stable/SupportedBoards.html and https://brainflow.org/2026-05-08-muse-anthena/.
