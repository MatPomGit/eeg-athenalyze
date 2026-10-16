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


## Implementation status (2026-10-16)

The repository now exposes BrainFlow's allowlisted preset and latency choices without allowing arbitrary GATT commands:

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze record --device muse-athena --preset p21 --no-low-latency --duration 60 --discovery-timeout 30 --output data\local\athena-p21-no-ll-01.eegz
```

Use a distinct output name for each condition. `--preset` accepts `p21`, `p1035`, `p1041`; `--low-latency` / `--no-low-latency` sets the BrainFlow option. Defaults stay at `p1041` with low latency enabled. The actual on-device effects of each option remain **unverified**; successful software CI is not hardware validation. Backend import for OpenMuse raw packet logs, Amused-Py format and LSL/XDF are **not yet implemented** and must satisfy independent format, timestamp provenance and privacy gates before being considered interchangeable with `.eegz`. Follow linked implementation issues.


### Optional OpenMuse external invocation (new CLI)

OpenMuse is **not** installed automatically, not imported into the main interpreter, and its raw data is **not** silently converted to EEGZ. First install it into a separate environment using the upstream instructions; discover the actual `OpenMuse.exe` path in that environment.

```powershell
.\.venv\Scripts\python.exe -m eeg_athenalyze devices openmuse find --openmuse-executable .\.venv-openmuse\Scripts\OpenMuse.exe
.\.venv\Scripts\python.exe -m eeg_athenalyze devices openmuse record --openmuse-executable .\.venv-openmuse\Scripts\OpenMuse.exe --address DEVICE_FROM_FIND --duration 60 --output data\local\openmuse-raw01.txt
```

The wrapper calls upstream `find`/`record` without a shell; on success requires a nonempty output and refuses existing paths. If upstream emits a partial file on failure, retain it and treat it as **unverified**, not a complete recording. Only one BLE acquisition program may connect at a time. Do not commit raw human EEG. Subsequent decoding and direct import are tracked in issue #41. These subcommands have mocked software tests; they have **not been verified on a physical Athena device**.


---

## Addendum: six additional resources examined (2026-10-16)

This review is grounded in the actual GitHub READMEs, the \`MuseDataProcessing/ProcessData.py\` source file, the GitHub commit comparison for the user's BrainFlow fork, and the public Open Collective page. Links are included at the point of discussion. Source claims concerning hardware operation are distinguished from tests performed in *this* repository. None of these applications was executed with the user's Athena in this review.

### 1. BlueMuse: Windows BLE-to-LSL reference implementation

Repository: https://github.com/kowalej/BlueMuse ; specific release: https://github.com/kowalej/BlueMuse/releases/tag/v3.1.0 .

BlueMuse **3.1.0** declares Athena support *experimental/not verified*, even though 3.1.0 is called a stable application release. It is a modernized .NET 10/WinUI 3 single-process Windows BLE/LSL implementation. Earlier **2.5/3.0** releases reportedly had EEG/telemetry consumption bugs, so avoid those as a benchmark. The README also describes fixes for reentrant GATT callbacks and serializing GATT operations **per device**. Those are particularly relevant to this project's intermittent early disconnects.

**Protocol findings from its README:**
- Athena is differentiated by GATT \`273e0013-...\`, **not** by the \`MuseS-XXXX\` name alone.
- The sensor stream uses tagged, multiplexed notifications on \`273e0013-...\` and \`273e0014-...\`. The existence of a characteristic does not guarantee Windows can subscribe to notifications on every characteristic in a given session. This project's BrainFlow logs explicitly report skipping notifications for 0014; do not call that error by itself.
- EEG packing: **four channels × four samples per packet**, 14-bit offset-binary LSB-first. The stated full span is **1450 µV** after subtracting the 2^13 midpoint. Thus observed approximate **-725/+725 µV bounds** in our TP9/TP10 are consistent with the documented conversion range but **not proof of analog ADC saturation**; compare discrete raw-code counts at the rails and decoder equivalence.
- A packet header contains an **index** but not a physical clock. BlueMuse derives per-sample stream times from host notification arrival time via a dejittering fit. Those fitted times are **not directly validated physical sample timestamps**; source-receive and derived times must remain separately labeled.
- Additional sensors: accelerometer/gyro in a shared tagged packet, optical channels (16 detector counts on PPG outlet), battery percentage only. Avoid interpreting optical detector counts as ordinary Muse legacy PPG.
- LSL timestamp output is configurable, including LSL local-clock/Unix-time representations, and data may be float32 or double64. These represent *format choices*, not independent EEG-rate settings.
- PowerShell protocol URLs allow programmatic start/stop, discovery and stream enable flags, e.g. \`start bluemuse://start?streamfirst=true\`. This feature can support supervised diagnostics but must not auto-connect concurrently with BrainFlow.

**Security/cost:** distribution is an MSIX sideload. Its setup describes installing a certificate into the **Local Machine Trusted Root** store and potentially changing developer settings. Do not automatically install/trust a new root certificate, bypass execution policy or suppress safety warnings. Inspect release signatures/artifacts manually and seek explicit consent first. Software is optional; no paid service is needed for the described LSL path.

**Decision:** P1 independent Windows GUI acquisition and protocol/dejitter reference; later feed LSL into a provenance-preserving XDF reader. Do not import fitted BlueMuse samples directly into research BIDS as hardware-verified.

### 2. MatPomGit/MuseDataProcessing: Mind Monitor CSV to WAV, not Athena BLE driver

Repository: https://github.com/MatPomGit/MuseDataProcessing ; actual source: https://github.com/MatPomGit/MuseDataProcessing/blob/main/ProcessData.py .

The README describes an earlier Muse S/Muse 2 workflow: export \`sleepData.csv\` from **Mind Monitor**, process **AF7 + AF8 average** into normalized 256-Hz floating-point \`Raw.wav\` for Audacity/spectrogram and write downsampled \`relativeBrainwaves.csv\`. It explicitly notes that the CSV column positions vary. **It does not connect to Muse S Athena, handle BLE packets or validate physical timestamps.** Its README also reports an apparent ~50-Hz spectral bar in an example recording, providing independent anecdotal context rather than proof about this device.

**Audited source problems, requiring correction before scientific reuse:**
1. Hardcoded indices \`row[22]\`, \`row[23]\` for AF7/AF8, and \`row[10]\`, \`row[14]\`, \`row[2]\`, \`row[6]\`, \`row[18]\` for bands. No header/schema validation; a changed CSV column order silently mislabels data.
2. Bare \`except:\` replaces corrupted raw EEG with **last known sample**, which fabricates flatline segments without an explicit validity mask. Empty band cells are silently converted to zero.
3. Empty-value tests for beta/theta/gamma/delta accidentally check \`row[10]\` in the alternate condition (copy/paste error), rather than the corresponding band's cell.
4. Its purported "relative" alpha/beta/delta/theta/gamma formulas each omit **the numerator's own band's power from the denominator**; the resulting values need not sum to one and are not valid fractional band powers. Recalculate on a well-defined scale only after verifying the Mind Monitor log-power convention.
5. \`np.interp(rawData, (min,max), (-1,1))\` globally rescales the EEG amplitude to arbitrary audio units, destroying **µV calibration** in the WAV. The WAV is visualization-only and cannot substitute the immutable source.
6. No obvious numeric bounds for \`10**band\`, finite/NaN input controls, source timestamps, continuity masks, participant metadata or verification tests; \`math.isnan\` after earlier replacements is insufficient.
7. CSV export uses one point per 1024 rows rather than time-aware downsampling; its 256-Hz constant sampling assumption needs checking for each recording.

**Decision:** use as a legacy visual-inspection concept only, not a decoding or acquisition backend. Our existing non-destructive EEGZ trace/PSD/spectrogram is preferable. Any CSV or WAV bridge must preserve original raw values, labels, and timestamps, and mark invalid samples rather than fill them silently.

### 3. MatPomGit/brainflow: exact upstream mirror at the compared head, not an Athena patch

Repositories: https://github.com/MatPomGit/brainflow and https://github.com/brainflow-dev/brainflow .

The user's GitHub repository is a fork. A GitHub compare request \`brainflow-dev:master...MatPomGit:master\`, executed on **2026-10-16**, returned status **identical**, \`ahead_by=0\`, \`behind_by=0\`, commit **e3caf4b7289a2616efb76c8a3276d2c2086fd488** (comparison snapshot). Therefore the compared \`master\` tips contain **no known fork-specific fixes** for Athena BLE, decoding or timestamps. Treat it as a convenient code-inspection/future patch workspace, **not** a solved replacement driver. Its README describes the normal cross-language BrainFlow SDK (C++ implementation and Python/Java/C#/MATLAB bindings), synthetic/streaming boards, filtering and CI.

**Next engineering investigation:** compare the installed Windows \`brainflow\` version and native library with this fork/upstream HEAD, inspect Muse Athena 14-bit scaling and notification subscription, startup/stop control sequences, packet indices, low-latency command and epoch timestamp assignment. A validated fix belongs in reproducible unit/byte fixtures and ideally an upstream PR. Avoid installing random fork HEAD into the research venv before testing provenance and compatibility.

### 4. BrainFlowUnrealPlugin: application integration, not a new acquisition transport

Repository: https://github.com/brainflow-dev/BrainFlowUnrealPlugin .

Provides a C++ BrainFlow integration plugin for Unreal Engine **4.25+** (README) with instructions to build the native BrainFlow binaries for OS/architecture/runtime and add \`BrainFlowPlugin\` as a module dependency. Windows setup references Visual Studio 2019 and matching BrainFlow build-toolchain settings. Because it wraps BrainFlow's native SDK, the plugin **does not independently fix Athena connection loss, 14-bit decoding, clock/timestamp semantics or 50-Hz contamination**. It is useful for later neuroadaptive 3D/VR experiments in Unreal; the current teaching software stack uses Unity, so it is not a priority for the Windows Athena diagnostic path. Note Unreal 4.25-era build guidance may require migration for modern Unreal/Visual Studio.

**Decision:** P3 integration candidate contingent on clean acquisition via a validated backend; do not add the plugin to the present Python app.

### 5. BrainFlow Open Collective: funding channel, not technical driver or requirement

Source: https://opencollective.com/brainflow .

This is the collective's financial/support page. It confirms BrainFlow promotes its open-source SDK as **free** and lists **optional paid** sponsorship, datasets, classifiers and support tiers. It is **not** an additional acquisition library, an Athena driver, a data streaming protocol or a proof of compatibility. The research project has **no need to purchase** these products or sponsorship for SDK use. No payments, memberships, API subscriptions or paid support are authorized or suggested.

**Decision:** metadata in the report only; no software integration or cost.

### 6. BrainFlowAndroidTest: independent Android hardware-control experiment

Repository: https://github.com/brainflow-dev/BrainFlowAndroidTest ; README: https://github.com/brainflow-dev/BrainFlowAndroidTest/blob/master/README.md .

The project explicitly lists Muse S Athena and includes a **BrainFlow 5.23.0** Android AAR, Java/JNA, an Android BLE permission flow and separate \`DEFAULT_PRESET\` EEG / \`AUXILIARY_PRESET\` accelerometry handling. Its README claims a **physical test on 2026-09-26** using Samsung Galaxy S23 Ultra / Android 15 and Athena: **29,392 EEG samples at 256 Hz after a 114-s checkpoint**, accelerometer **52 Hz**, live band-power estimates, and clean shutdown. This is a **self-reported upstream physical test**, not something verified here; its apparent Android success makes an Android-vs-Windows test particularly useful to localize the disconnect to the host BLE stack or BrainFlow native build versus the device itself.

The documented Android test connection uses \`params.serial_number="MuseS-XXXX"\` optionally and \`params.other_info="preset=p21;low_latency=true"\`, *not* the current Windows Python baseline \`p1041;low_latency=true\`. The comparison must control for **both host and preset**; otherwise a successful phone test cannot isolate the Windows BLE stack. The app uses a serialized worker to ensure prepare/start/poll/stop/release calls do not overlap; this is a testable robustness lesson. It also waits for **real samples**, rather than accepting prepare_session alone as device success.

The example's 16-s PSD path detrends, notch-filters 48–52 and 58–62 Hz, bandpasses 2–45 Hz, discards edge transients, then calculates central 10-s band powers. That is an **educational signal-processing example**, not evidence that notch filtering fixes the user's severe ~50-Hz raw contamination. In EEG Neurolyze keep unfiltered measurements and contamination QC before filtering.

**Decision:** P1 comparative Android acquisition path for isolating Windows-specific BLE issues. Running the actual app on the user's phone and headset is a physical test requiring explicit action. The app is a developer example, not production-grade research certification.

### Cross-source observations relevant to the current failures

1. Approximate \`±725 µV\` is **the documented Athena 14-bit offset-binary range** in BlueMuse. The observed TP9/TP10 plateaus might reflect rail codes but the raw packet sample bits are needed to distinguish decoder/clipping/contact from normal saturation.
2. BlueMuse's packet header **index** offers a promising route to check missing notifications independent of repeated BrainFlow timestamps; packet-index wrap/restart and multiplexing need careful decoding.
3. BlueMuse's mention of **per-device GATT serialization** and the Android app's **single-worker BrainFlow lifecycle** are independently actionable clues for investigating Windows disconnects.
4. BlueMuse LSL timestamps are **host-derived/dejittered**, not an EEG hardware clock, so LSL/XDF may support useful practical acquisition without resolving absolute physiological latency precision.
5. MuseDataProcessing's resampled WAV and relative-band CSV must **never** be treated as raw, calibrated EEG or evidence of Athena physical compatibility.
6. The unchanged BrainFlow fork is an upstream-contribution opportunity, **not** a quick fix. BrainFlowUnrealPlugin adds no new transport. Open Collective adds no technical capability or mandatory fee.

### Proposed work items and provenance matrix

| Priority | Work package | Execution | Evidence needed |
|---|---|---|---|
| P0 | Inspect BlueMuse Athena packet-index, scaling, host dejittering and GATT serialization against BrainFlow native code | Autonomous source audit + software tests | Source-pinned decoder fixtures, wraparound cases, 14-bit rail checks |
| P0 | Run matched \`p21;low_latency=true\` 60-s tests on Windows/Android where possible | Human/device | Same headset, battery/contact protocol, BrainFlow versions, sample counts/stalls/logs |
| P1 | Test BlueMuse 3.1 Windows LSL/XDF with safe sideloading approval | Human/device | Raw stream and host-clock provenance; no automatic trust-root installation |
| P1 | Preserve/use packet sequence counters in independent raw BLE backend | Autonomous code + device verification | Packet loss/jitter vs duplicated timestamp summary, not synthetic gap filling |
| P2 | Add safe, schema-validated Mind Monitor CSV ingest *only if necessary* | Autonomous | No fill-forward, explicit invalid masks and sample rate/timestamps |
| P3 | Unreal Engine plugin pathway | Autonomous architectural planning | Separate VR/HRI research requirements; no interference with existing Python core |
| N/A | Open Collective financing | None | No cost, subscription or purchase required |

**General restrictions:** no real participant EEG in public CI or documentation; retain source bytes; no auto-filtering of suspected mains artifacts; preserve measured/host/reconstructed timestamp distinctions; do not unlock real EEG-BIDS based on simulated or self-reported external validation.

**New reference links:** [BlueMuse README](https://github.com/kowalej/BlueMuse/blob/master/README.md), [BlueMuse release 3.1](https://github.com/kowalej/BlueMuse/releases/tag/v3.1.0), [MuseDataProcessing script](https://github.com/MatPomGit/MuseDataProcessing/blob/main/ProcessData.py), [BrainFlow fork](https://github.com/MatPomGit/brainflow), [Unreal plugin](https://github.com/brainflow-dev/BrainFlowUnrealPlugin), [BrainFlow collective](https://opencollective.com/brainflow), [Android test README](https://github.com/brainflow-dev/BrainFlowAndroidTest/blob/master/README.md).


## Detailed packet protocol reference

See [Muse S Athena BLE packet types, tagged payloads, preset command semantics and time sources](2026-10-16-muse-athena-packet-protocol.md). This reference separates documented packet formats, conflicting third-party descriptions and unverified hardware hypotheses, and maps to issues #47–#54.
