# ADR-0006: Public name EEG Neurolyze and legacy package compatibility

- Date: 2026-10-12
- Status: Accepted
- Scope: naming and migration

## Context
The repository has been renamed to `MatPomGit/eeg-neurolyze`, but its current Python distribution/import and CLI still use `eeg-athenalyze`/`eeg_athenalyze`. The original implementation specification also mentions the obsolete repository name.

## Decision
Use **EEG Neurolyze** as public product and repository name, and use `MatPomGit/eeg-neurolyze` in all new user-facing documentation. Retain existing Python import and CLI names temporarily to avoid breaking current workflows. Treat rename of distribution, console entry point, and module namespace as an explicit versioned migration with redirects/compatibility aliases, tests and release notes. Do not perform an unplanned bulk rename in a documentation PR.

## Consequences
Temporary naming asymmetry must be explained clearly. Future renaming should be tracked as implementation work, not silently changed in documentation.

## Alternatives
Immediate rename would risk breaking CLI and examples. Keeping the obsolete public title permanently confuses project identity.

## Verification
README naming, working existing CLI and explicit follow-up migration task.
