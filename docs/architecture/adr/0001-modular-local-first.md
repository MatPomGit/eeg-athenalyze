# ADR-0001: Modular local-first architecture

- Date: 2026-10-12
- Status: Accepted
- Scope: system architecture

## Context
A single script cannot safely manage hardware, stimuli, clocks, preprocessing and teaching workflows while supporting new experiments.

## Decision
Use independent device, acquisition, experiment, PsychoPy, synchronization, persistence, analysis and reporting interfaces. Provide a headless EO/EC path and a synthetic source as a first-class development target. Keep all primary participant EEG data on the local machine unless deliberate export occurs. Use validated typed protocols and versioned run configurations. Preserve the existing `src/eeg_athenalyze` APIs until migration is warranted.

## Consequences
Plugins can evolve independently and the offline analysis path remains hardware-free. More explicit interfaces and tests are required. A nominally installed module is not necessarily a validated hardware capability.

## Alternatives
One monolithic app is quicker initially but couples failures and is hard to test. Separate services/cloud-first would introduce operational and privacy complexity prematurely.

## Verification
Synthetic end-to-end execution, device contract tests, offline replay without a device, and no automatic upload.
