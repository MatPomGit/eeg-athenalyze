# Architecture Decision Records (ADR)

ADRs capture decisions and trade-offs independently of code implementation progress. **Accepted** means the design decision is adopted, not that all corresponding features exist or have been tested. Follow the status vocabulary in [ROADMAP](../ROADMAP.md).

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-modular-local-first.md) | Modular local-first pipeline and immutable source | Accepted |
| [0002](0002-bids-data-contract.md) | Native archival source, EEG-BIDS and formal validation | Accepted |
| [0003](0003-psychopy-lsl.md) | Optional PsychoPy engine and LSL timing model | Accepted |
| [0004](0004-windows-venv.md) | Isolated runtimes and thin Windows launchers | Accepted |
| [0005](0005-research-quality.md) | Validation gates, reproducible outputs and privacy | Accepted |
| [0006](0006-project-naming.md) | Public name and stable legacy Python import | Accepted |

Template for future ADRs: title, date, status, context, decision, consequences, alternatives, verification/migration notes. Never silently rewrite an accepted ADR; supersede it with a new numbered ADR linked in this index.
