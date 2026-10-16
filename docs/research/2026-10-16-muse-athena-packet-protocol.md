# Muse S Athena: BLE framing, tags, presets and timing provenance

**Date:** 2026-10-16. **Purpose:** technical reference for #47, #48, #49, #53. **Status:** based on public descriptions, not a device-validated specification. Never interpret a software comparison as hardware certification.

## 1. Four distinct layers

1. **BLE/GATT**: service FE8D, command characteristic \`273e0001-4c4d-454d-96be-f03bac821358\` and possible sensor notification characteristics \`273e0013-4c4d-454d-96be-f03bac821358\` and \`273e0014-4c4d-454d-96be-f03bac821358\`. Check actual per-characteristic notify properties before subscribing. \`0014\` may be present but not notifiable on the user's Windows session; BrainFlow logs a skip. Existence of FE8D and control characteristic is necessary but not evidence of a continuing sensor stream.
2. **BLE notifications**: a notification is an arriving transport message. One message may hold several tagged subpackets. Empty \`BoardShim.get_board_data()\` polls are empty **application-buffer** reads and cannot directly count dropped BLE notifications.
3. **Binary tagged subpackets**: tag identifies the semantic decoder and count of values. The packet has header/index and subpacket framing; offsets below are *implementation-derived*, not a firmware-certified universal ABI.
4. **Application streams**: BrainFlow organizes decoded values into \`DEFAULT_PRESET\` (EEG), \`AUXILIARY_PRESET\` (ACC/GYRO), \`ANCILLARY_PRESET\` (optics/battery); do not confuse these BrainFlow buffer presets with device command \`p21\`/\`p1041\`.

## 2. Tags and data model

| TAG | Sensor | Payload shape described in implementations | Nominal sample rate | Representation | Caveats |
|---|---|---|---|---|---|
| \`0x11\` | EEG4 | 4 channels × 4 values / subpacket | 256 Hz | 14-bit unsigned, little-endian bit order within packed bitstream | Total 16 × 14 = 224 bits = 28 EEG value bytes, excluding framing/metadata |
| \`0x12\` | EEG8 | 8 values × 2 samples / subpacket | 256 Hz | 14-bit packed | 8 values != 8 independently mounted scalp electrodes |
| \`0x47\` | accelerometer+gyroscope | 6 axes × 3 values | 52 Hz | signed 16-bit little-endian | ACC scale reported ~6.10352e-5 g / LSB; GYRO scale reported ~-7.4768e-3 degrees/s / LSB, verify in driver |
| \`0x34\` | optical 4 | 4 × 3 values | 64 Hz | 20-bit packed unsigned counts | Raw detector intensity is not automatically calibrated physiology |
| \`0x35\` | optical 8 | 8 × 2 values | 64 Hz | 20-bit packed unsigned counts | Decoder output/channel semantics need golden fixtures |
| \`0x36\` | optical 16 | 16 × 1 value | 64 Hz | 20-bit packed unsigned counts | Some third-party sources disagree about exact payload sizes/layout; verify with source byte offsets |
| \`0x88\`, \`0x98\` | battery/status | status-specific block | asynchronous telemetry | see implementation | **Disagreement**: BrainFlow/BlueMuse vs MindVault report battery scaling /512 vs /256; must verify raw units with device |

**EEG conversion:** multiple sources describe 14-bit offset binary with a 1450 µV span; e.g. \`(raw14 - 8192) * (1450 / 16384)\` µV (exact denominator varies by implementation: some use 16383). Therefore a plateau near **-725/+725 µV** is consistent with the representable code range; it does **not** alone prove clipping in the analog input. Record raw codes, full-scale-count fraction, exact version-specific scale, reference montage and physical electrode conditions. Never normalize source microvolts using audio/WAV rescaling as in the legacy MuseDataProcessing script.

**Proposed diagnostic raw-value golden fixtures:** raw code = 0, 1, 8191, 8192, 8193, 16382, 16383; all-zero, all-midpoint, alternating extremes, interleaved channels; bit-offset cross-byte boundaries; truncated subpacket and unknown tags. Compare the Python decoder with BrainFlow native output and independent BlueMuse/Amused-Py behavior; hash reference bytes and pin source commits. Packet sequence index wrap and dropped notification indicators must be tested offline before reporting real packet-loss percentages.

## 3. Possible framing details and uncertainty

The independent \`muse-rs\` technical description derived from OpenMuse depicts a packet with a leading packet-length byte, a header (including packet index), then a first tag at approximately byte offset 9 followed by a four-byte subpacket metadata section and sensor payload; subsequent subpackets contain their own tag+metadata+payload. **Do not hardcode these offsets into the production decoder yet:** derive verified offsets from version-pinned upstream source and fixtures. No physical high-resolution sample clock is proven by a packet-index field.

## 4. Device preset commands vs BrainFlow buffer presets

| Device command | Data types described by upstream sources | Use |
|---|---|---|
| \`p21\` | 4 EEG channels + IMU, without optical stream in BrainFlow's newer classification | Minimal transport diagnostic |
| \`p1035\` | EEG4 + 4 optical + IMU/battery | Reduced multimodal diagnostic |
| \`p1034\`, \`p1043\`, \`p1044\` | EEG8 (internally) + 8 optical + IMU/battery | Multiplexing stress comparison |
| \`p1041\`, \`p1042\` | EEG8 (internally) + 16 optical + IMU/battery | Existing default / high payload |
| \`p20\`, \`p50\`, \`p51\`, \`p60\`, \`p61\`, \`p1045\`, \`p1046\` and \`p4129\` | Additional firmware command options described in differing source versions | Do not assume supported by current app allowlist or installed BrainFlow without checking version |

**Important upstream conflict:** BrainFlow \`SupportedBoards.rst\` and the 5.22.0 article differ on some LED/optical power descriptions and on the treatment of 4 vs 8 EEG values in specific presets. The *EEG Neurolyze CLI* intentionally allowlists \`p21\`, \`p1035\`, \`p1041\` pending on-device testing; this is a **software safety policy**, not the list of every firmware preset. \`low_latency=true\` is independent and triggers \`L1\`, not a physical EEG sample-rate change.

## 5. Startup/shutdown commands

Upstream BrainFlow 5.22.0 documentation describes:
- \`prepare_session\`: \`v6\` (protocol), \`s\` (status), \`h\` (halt), selected \`pXXXX\`, \`s\`.
- \`start_stream\`: \`dc001\` twice and status; optional \`L1\` if low latency enabled.
- \`stop_stream\`: \`h\`.
- Control writes are length-prefixed ASCII commands ending in newline (do not send untrusted commands via production CLI).

Amused-Py advocates a *different two-stage preset switch* (\`p21\` prime; halt; then target preset; \`dc001\` again). This is an independent upstream claim, not proof that every Athena device requires two-phase init. Compare actual source and logs. A failed \`h\` after streaming already stalled indicates failure to stop an already disconnected session, **not necessarily the original disconnect cause**.

## 6. Clocks, packet counters and loss classification

At least four clock-like quantities must remain distinct:
- BLE notification **host receive time**, subject to Windows scheduling/jitter.
- Header **packet index/counter**, if decoded and its domain/wrap verified.
- Per-sample **nominal index** derived from known 256 Hz output mapping, not physical timestamp.
- Source **BrainFlow timestamp** or **BlueMuse/LSL dejittered time** generated by client software.

BlueMuse documents fitting host arrival time against sample index to dejitter streams; it does not thereby create hardware timestamps. Our measured sessions show ~74% duplicate BrainFlow source timestamp intervals; independent packet numbering may permit classification of missing chunks, but no loss metric can be claimed until tag-specific count semantics have been validated.

A \`get_board_data()\` empty poll is not a BLE packet; 40 empty polls/41 loops can be caused by lack of notifications, decoding rejection, or buffer handling, not uniquely radio packet loss. Present these stages separately: discovery → GATT control → notify subscription → raw notification → tag parsing → buffer append → EEG samples → QC.

## 7. Next tests

1. **Autonomous** (#47): verify packed 14-bit vectors, signed centered µV scale, four physical channels, frequency of full-scale raw codes, unknown/truncated tags and channel interleaving.
2. **Autonomous** (#48): parse sequence indices from fixtures; simulate wrap/drop/reorder; preserve arrival timestamps.
3. **Autonomous** (#49, #53): compare callback locking/serialization between BlueMuse 3.1 and BrainFlow's Windows native BLE implementation; create reproducible tests of stops after unexpected disconnect.
4. **Human/device** (#40, #50): matched \`p21;low_latency=true/false\` vs \`p1041\` on same Athena under Windows and Android, 3 × 60 s, log all failed trials and Bluetooth/firmware versions.
5. **Human/device** (#51): separately operate BlueMuse Windows LSL and/or OpenMuse raw acquisition; one BLE owner at a time; review MSIX certificate trust before BlueMuse install.
6. **Autonomous + human** (#43, #54): keep host/LSL dejitter clocks separate from real physical EEG timing; no real EEG-BIDS promotion without independent timing evidence.

## Sources

- BrainFlow Athena release (command sequence, packet tag table, BLE GATT): https://brainflow.org/2026-05-08-muse-anthena/
- BrainFlow Supported Boards (presets, rates, channel buffers): https://github.com/brainflow-dev/brainflow/blob/master/docs/SupportedBoards.rst
- BlueMuse Athena notes / Windows LSL: https://github.com/kowalej/BlueMuse
- Amused-Py independent BLE: https://github.com/Amused-EEG/amused-py
- OpenMuse: https://github.com/DominiqueMakowski/OpenMuse
- muse-rs protocol research: https://github.com/eugenehp/muse-rs
- MindVault alternate description, including disputed battery scale: https://github.com/mind-vault-lab/muse-athena-protocol
- Our earlier survey: [2026-10-16 Muse S Athena PC alternatives](2026-10-16-muse-athena-pc-alternatives.md)

*This file is an evidence map and test design, not a manufacturer-maintained packet specification or a demonstration that a particular firmware is correct.*
