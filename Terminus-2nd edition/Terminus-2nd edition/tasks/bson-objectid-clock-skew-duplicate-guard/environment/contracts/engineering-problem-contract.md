# Engineering problem contract

Wireclock materializes twelve-byte BSON ObjectId values with machine-bound fingerprints, per-second counter monotonicity, digest-hex intake batches, oidstore persistence from batch files only, and path-scoped JSONL resume cursors.

Failure modes include mono-reverse wall clocks (HTTP 409), counter exhaustion past 0xFFFFFF (HTTP 409), repeat client_seq claims that must not overwrite payload_json, batch hex mismatch on intake, and cross-path line suppression when resume cursors are not path-scoped.

Verifier hosts may inject VERIFIER_SEED. Isolation overlays follow /app/docs/isolation-overlay-contract.md: they read TB3_FIXTURE_DIR (default /opt/verifier-fixtures/wireclock) for partial golden modules and require the exported Go APIs named there (including `Generate`, `NewReplayer`, and `Replay`).

See the linked contracts for wire layout, intake batch shape, digest-hex formula (including compact-payload serialization), resume cursor ledger, and HTTP response schemas.
