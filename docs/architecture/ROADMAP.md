# Delivery roadmap and verification gates

Statuses: **implemented** = code present; **verified** = relevant executed tests or hardware evidence; **planned** = not delivered. Each milestone builds a tested vertical slice; avoid broad speculative scaffolding.

| Milestone | Deliverables | Exit gate |
|---|---|---|
| M01 Core | Synthetic EO/EC, checksummed native archive, alpha comparison, HTML, Windows .venv launcher and PL/EN quickstart | Automated synthetic and Windows tests pass; native archive read-back; honest simulated labeling |
| M02 BIDS | MNE-BIDS BrainVision export, metadata/events, official validator and MNE read-back | Official validator reports no blocking errors; sample/channel/event integrity compared to native archive |
| M03 Hardware | Muse S Athena BrainFlow adapter, BLE diagnostics, true timestamp provenance and acquisition QC | On-device Windows 11 test with documented firmware/API, dropouts, time continuity and safe stop |
| M04 PsychoPy/LSL | Independent environment, Builder/API adapter, markers, timing logs, optional XDF | End-to-end synthetic marker alignment; documented latency experiment; no unverified timing claims |
| M05 Protocols | Stroop, N-back, extensible registry, behavior + EEG event mapping | Complete trial/response tests, valid BIDS events, validated instructional examples |
| M06 Education | Six full bilingual laboratories, MkDocs Pages, figures, Windows tutorials | PL/EN equivalence, link and executable-command checks |
| M07 Advanced | ERP/BCI/real-time features, additional devices as separately validated plugins | Scientific feasibility and hardware timing validation appropriate to each feature |

## Implementation snapshot: 2026-10-12
- M01: code and launchers present; original synthetic pipeline has automated tests. Verification status must follow actual CI, not documentation assertions.
- M02: initial BrainVision exporter and official validator merged in PR #4; custom derivative export is under review in PR #5, not yet merged. Physical device metadata/real timing remain unverified.
- M03-M07: planned. Do not mark implemented without merged code and evidence.
- Package imports retain `eeg_athenalyze`; public project is EEG Neurolyze. Naming migration requires compatibility ADR.

## Research-grade gates
1. **Data:** immutable original values and timing with checksums; interrupted session retained.
2. **Metadata:** explicit reference/units/channel provenance, experiment protocol and analysis configuration.
3. **Timing:** measured accuracy for stimulus-locked inference; otherwise mark uncertainty.
4. **BIDS:** formally validated dataset, read-back comparison, derivatives provenance.
5. **Reproducibility:** lock/constraints, seed, versions, documented reprocessing.
6. **Privacy:** pseudonymous identifiers; no accidental exposure through Git or reports.

## Next recommended implementation
M02: complete PR #5 CI and review custom derivatives, then verify the complete EEG metadata/event mapping and retained provenance against official BIDS rules before declaring the milestone fully closed. Hardware integration may progress in parallel only on separate, bounded PRs; do not merge unsupported physical-device claims.
