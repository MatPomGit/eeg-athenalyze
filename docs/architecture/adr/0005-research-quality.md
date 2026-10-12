# ADR-0005: Scientific validation, privacy and status transparency

- Date: 2026-10-12
- Status: Accepted
- Scope: scientific integrity and governance

## Context
A successful command exit, simulator test or BIDS-like folder does not establish hardware validity, synchronization precision, research safety, or scientific reproducibility.

## Decision
Report separately: implementation status, unit/integration test status, physical hardware validation, timing validation, BIDS validation and scientific inference limitations. Make raw archive immutability, pseudonym IDs, explicit clock-domain provenance, failure retention, config/version capture and no participant data in Git mandatory. Use synthetic CI by default and separate opt-in physical-device tests. Avoid diagnostic/clinical claims and unsupported inference from four-channel EEG.

## Consequences
Some attractive features remain gated; reporting and documentation must disclose unknowns. Expands scientific trust and prevents false precision.

## Alternatives
Marketing-driven 'supported' labels or implicit validation are unacceptable; manual-only checks are not scalable.

## Verification
CI evidence, timing protocol, data integrity reports, validator output, bilingual tutorial consistency and privacy review.
