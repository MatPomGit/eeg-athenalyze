# Muse S Athena (MS-03) on PC: acquisition alternatives and diagnostic plan

**Research date:** 2026-10-16. **Scope:** direct BLE under Windows 11 (also macOS/Linux), alternative decoders, LSL acquisition, raw packet logging, preprocessing. **Evidence standard:** linked upstream project statements are not equivalent to independent on-device validation. This document reports public sources and identifies experiments still required locally. Do not confuse Muse S Gen 1/2 with MS-03 Athena.

## Executive result

**Recommendation:** first attempt a reproducible, **EEG-only BrainFlow p21** run and compare `low_latency=false` against current `preset=p1041;low_latency=true`; in parallel validate **OpenMuse** as an independent direct BLE recorder of raw packets, then **Amused-Py** for protocol/initialization cross-checking. BlueMuse 3.1 adds experimental Athena support and native Windows LSL, so it is a GUI comparator, not a certified alternative. Use **only one software stack connected to Muse at a time**. Preserve raw BLE packets and original source timestamps before deriving nominal sample times.

Existing local evidence: Bleak scans for `MuseS-C87B`, identifies FE8D and control GATT characteristic. BrainFlow connects, but one 60-s attempt delivered only 22 samples then 40/41 empty buffer polls, disconnected before `stop_stream`. Earlier 60-s archive had 15,528 samples but ~74% repeated source timestamps and severe ~50 Hz contamination. Thus discovery/GATT availability, continuity, decoding and physical quality are **separate gates**.

## Upstream comparison

| Stack | Claimed MS-03 support / platform | Raw transport / outputs | Suggested role | Qualifications |
|---|---|---|---|---|
| **BrainFlow >=5.22** | Official Athena board ID, Windows native BLE / Linux / macOS | Built-in native BLE, EEG + auxiliary/optical presets, BrainFlow buffers and playback/streaming boards | Existing baseline, vary preset/latency reproducibly | Source timestamp semantics and BLE packet integrity remain unverified on our device |
| **OpenMuse** (Dominique Makowski) | Explicit Athena support, Python | BLE raw packet recording; decoding to pandas, MNE-LSL streams; `OpenMuse view`; LabRecorder XDF | **Best independent acquisition/packet evidence** | Experimental project; upstream explicitly lists timestamp/ERP validation as future work |
| **Amused-Py** (Amused-EEG) | Explicit Athena and custom BLE implementation | Direct Bleak, EEG/PPG/IMU, binary raw replay, Qt visualization, callbacks | **Best protocol cross-check** / handshake tests | Authors describe a two-stage initialization; verify firmware compatibility and provenance rather than assuming universal requirement |
| **BlueMuse v3.1** | Athena support **experimental/unverified**, Windows WinUI3 / .NET 10 | BLE to LSL, Windows UI, alternative timestamp formats | GUI + independent streaming comparator | New sideload distribution and trust-root certificate requirement; review release signing before installing |
| **MindVault / muse-athena-protocol** | Claims native Windows/macOS/Linux Athena support | Reference Python 14-bit decoder, desktop visualization, CSV / EDF(+) advertised | Decoder specification to compare against (bit packing, ADC scaling) | Vendor claims and early-access product; reproducibility and hardware validation not established by its repository alone |
| **Legacy muselsl / older Muse S scripts** | Often Muse 2016/2/S Gen 1 only | LSL, CSV | Concepts rather than initial MS-03 driver | Do not assume Athena compatibility from a generic Muse S description |

## BrainFlow: options that change what is transmitted, not the EEG hardware sample rate

Upstream supported boards page and BrainFlow 5.22.0 release explicitly document `BrainFlowInputParams.other_info` for Athena. `preset=p1041;low_latency=true` is default; shorthand `p1035`, `preset=p1035;low_latency=false`, and a documented EEG-only `p21` are valid candidates. `low_latency=true` sends an `L1` command on starting a stream; disabling it avoids that command, but does **not** establish an alternative verified time base or alter the device's nominal 256-Hz EEG sample rate.

**Controlled order:** (A) p21 + `low_latency=false`; (B) p21 + true; (C) p1041 + false; (D) p1041 + true (current baseline); optional (E) p1035 + false. Each with explicit log of BrainFlow version, operating system, Bluetooth adapter/driver version, battery level if available, placement and ambient mains devices. Do not change more than one variable between consecutive tests if making causal inferences. Treat any unsupported preset in the installed BrainFlow version as a failure, not a reason to send unvetted raw GATT commands. Current `AthenaSettings.preset_command` is hardcoded and **CLI has no `--preset` or `--low-latency`**, so implement controlled flags and integration tests before following this test matrix using the repository CLI.

BrainFlow's `get_board_data()` drains a process-local acquisition buffer, **not** an individual BLE read: 40 empty polls do not equal 40 BLE packet losses. A failed `h` at stop likely reflects a device already disconnected; it does not identify the initiating fault.

## OpenMuse: independent BLE capture, LSL / XDF and Windows precedent

OpenMuse README: `pip install https://github.com/DominiqueMakowski/OpenMuse/zipball/main`; `OpenMuse find`; `OpenMuse record --address <device-address> --duration 60 --outfile data.txt`; `OpenMuse stream --address <device-address> --preset p1041 --record data.txt`; `OpenMuse view`. It uses **MNE-LSL** for streams, not merely a generic `pylsl` wrapper. The repository describes device-specific multiplexed data (EEG, PPG, optics, IMU). Raw BLE packet capture allows protocol analysis before sample timestamp reconstruction. An independent Windows user project documents **OpenMuse + LabRecorder XDF** acquisition for Athena and notes older BlueMuse previously lacked Athena; that historical note predates newer BlueMuse v3.1.

Recommended execution: isolate OpenMuse in its own venv; first `find`, then **60-second raw packet-only record** (if the BLE link stays up). Save raw bytes locally without committing human EEG. Later run LSL with LabRecorder for XDF, store clock metadata and synchronization limitations. Stop BrainFlow and any Muse phone app first. Windows Bleak identifiers and OpenMuse address expectations may differ: do not invent MAC values, use actual `OpenMuse find` output.

## Amused-Py: a distinct Athena handshake

Upstream documents control characteristic `273e0001` and sensor notifications on `273e0013`, with its two-stage init: connect, subscribe control, send `v6`/`s`/`h`, select `p21`, subscribe EEG notifications, send `dc001` and `L1`, halt, switch to `p1034` or `p1035`, then send `dc001` and `L1` again. Its authors argue `dc001` must be sent twice for that particular handshake; this is an **upstream implementation claim**, not yet a demonstrated requirement of all Athena firmware. Code includes binary recording/replay, basic streaming and spectrum/LSL-style examples.

This implementation is especially useful to compare control-message order, notification subscription, TAG-based subpacket parsing, 14-bit sample unpacking and USB/BLE Windows behavior to the BrainFlow C++ source. Do not transmit custom commands to the device automatically as part of research CI.

## Alternative routes / formats

1. **BLE -> direct Python decoder -> raw binary or JSONL -> .eegz**: preserves evidence for decoder comparison; keep original BLE notification metadata and receive-time timestamps distinct from per-sample reconstructed nominal indices.
2. **BLE -> OpenMuse / BlueMuse -> LSL -> LabRecorder XDF**: good for acquiring multiple streams and synchronization experiments; LSL timestamps alone do not prove hardware-synchronized individual EEG sample timestamps.
3. **BLE -> desktop application -> CSV/EDF**: possible (MindVault advertises CSV/EDF; Amused binary replay); CSV/EDF alone do not certify source timing, channel reference or BIDS. Preserve originals before transformation.
4. **BrainFlow streaming board / playback file board**: can redistribute buffers or replay data (see BrainFlow Supported Boards). These do not replace the physical Muse-to-PC BLE connection or repair packet dropout.
5. **Signal conditioning**: visualize unfiltered data, per-channel amplitudes and near-rail fractions first; report 48–52 Hz contamination, but do not blindly notch-filter until identifying whether the ~50 Hz component is mains pickup, contact/reference, or decoder-related.

## Risk and validation plan

| Gate | Experiment / evidence | Acceptance criterion (proposed, not observed) |
|---|---|---|
| A: Discover/connect | Repeated Bleak and BrainFlow detection on Windows, one client at a time | Connected, services & control characteristic identified, stable device connection |
| B: Raw continuity | 3 × 60 s per selected configuration, saved receive-time BLE notifications/counters where available | No early disconnect; approximate 256 × 60 samples; record every stall and loss without synthetic fill |
| C: Decoder validity | Replay same raw packet file through ≥2 independent decoders (where interoperable), validate channel mapping and 14-bit scaling | Per-sample matching values within documented quantization units; define packet counters and discontinuities |
| D: Timing | Compare source timestamps to packet sequence/counter and host monotonic clock; independent trigger if required | Validated per-sample timing uncertainty and lost-packet detection; do not just divide total sample count by duration |
| E: Physiological quality | Contact/ref review, 50 Hz ratio and near-rail QC, eyes-open/closed with stable recording | Quantified acceptable amplitude/artefact criteria approved by the study team |
| F: Research export | Explicit hardware validation and research approval | BIDS export gate only relaxed after traceable evidence and validator checks |

**Autonomous work:** implement CLI preset/latency options, fixed-config smoke tests with mocked hardware, raw BLE decoder review, offline comparisons, versioned reports. **Human/device work:** actual PC-BLE measurements, electrode adjustment, firmware identification, ethics/data-release decisions, physically synchronized timing. No claim of physical testing is made in this research document.

## Primary references (accessed 2026-10-16)

1. BrainFlow official board docs: https://github.com/brainflow-dev/brainflow/blob/master/docs/SupportedBoards.rst
2. BrainFlow Athena 5.22.0 release: https://brainflow.org/2026-05-08-muse-anthena/
3. OpenMuse README: https://github.com/DominiqueMakowski/OpenMuse
4. OpenMuse Windows + LabRecorder case study: https://github.com/Marchev-Science/case-EEG-analysis/blob/main/data-collection/athena-openmuse/README.md
5. Amused-Py direct protocol: https://github.com/Amused-EEG/amused-py
6. BlueMuse project and deployment: https://github.com/kowalej/BlueMuse
7. BlueMuse v3.1 releases / experimental Athena: https://github.com/kowalej/BlueMuse/releases
8. MindVault protocol reference: https://github.com/mind-vault-lab/muse-athena-protocol
9. MindVault desktop early access: https://www.usemindvault.com/
10. Community experience, independent Athena connection considerations: https://github.com/yuriy-mikityuk/athena-tmr-lucid/issues/108
11. OpenMuse user report with partial optics success: https://github.com/DominiqueMakowski/OpenMuse/issues/27
12. Older Muse Gen1 tool (not a valid MS-03 baseline): https://github.com/1jehuang/muse-eeg

**Source caveat:** all above are public project documentation or reports; neither reported device compatibility nor MindVault marketing statements are independently validated against this project's physical Muse S Athena unit.
