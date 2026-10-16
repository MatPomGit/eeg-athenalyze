# M03 GATT partial initialization cleanup (2026-10-16)

Code review found that the optional raw Bleak collector attempted the final `h` halt only after all streaming initialization commands had succeeded. If an earlier command in the partially completed sequence failed, the session could exit without a best-effort halt, even if the GATT client remained connected.

Fix: record the fact that the command sequence was attempted *before* its first write and perform an allowlisted best-effort `h` in `finally` whenever the link is still connected. This does not mask the original write exception. The partially written local capture remains available. Added mocked regression for failure on the preset command and a disconnect case. No actual headset was accessed, no firmware settings were modified, and a failed halt or disconnected link still requires operator review.

Issues: #44 and #49. Acceptance: both platform CI tests and physical confirmation of GATT stop semantics (still blocked).