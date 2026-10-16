# Pinned upstream BlueMuse C# DecodeEEG test, issue #47

The workflow `.github/workflows/athena-bluemuse-native.yml` checks out the *original* BlueMuse source at repository commit `4b0a307d660b4c5490078dcb1188396cf066f0e1`. It copies the **unmodified** `BlueMuse.App/Athena/AthenaDecoders.cs`, prints SHA-256 provenance, compiles it with .NET 8, and calls **its actual `DecodeEEG` method** on four hard-coded, 28-byte synthetic vectors. Checks cover both TAG-defined logical layouts (4×4 and 8×2), 128 decoded values, sample-major order, rails, reversed channels and the source-based 1450/16383 µV scaling. Explicit test-only stubs stand in for other BlueMuse application components/constants; original upstream decoder code is not edited.

Unlike earlier adapted C++ and Python oracles, this invokes **original vendor C# decoder source** in a compiled test executable. It is not the full BlueMuse application, does not exercise its GATT framing, and does not claim physical validation or native BrainFlow parity. The exact source revision is recorded, but this is not a signed build provenance statement.

Evidence level depends on CI completion: check `Athena pinned BlueMuse native decoder` run logs and reported PASS/FAIL before calling the vendor test validated. CI runs on the public repository and should not require paid subscriptions or paid external APIs.

Next separate gates: run original BrainFlow C++ decoder in a pinned build against the same byte vectors; compare both outputs and preserve compiler/platform/revision identifiers. Subsequently, human-approved raw BLE packets, hardware/firmware metadata, channel mapping, timestamps and physical analog saturation are required. Do not unlock BIDS acquisition quality based on test fixtures.
