# Hidden capsule override

The validation harness reads alternate `.cap` fixtures from /tests/hidden_capsules, which is mounted for validation only and is not copied into the agent image. Operators may also set TB3_CAPSULE_DIR to another directory of `.cap` files when running intake outside the bundled fixture tree.

When TB3_CAPSULE_DIR is present, intake reads capsule files from that directory instead of the bundled fixture directory under /app/environment/fixtures/capsules.

The override changes only the capsule source directory. Rebuild, ledger write, emit, session lexicographic order, JA4 derivation, and deterministic output rules remain the same.

Alternate capsule runs must still write /app/state/session_ledger.jsonl and /app/output/session_index.json using the same command surface as bundled runs.
