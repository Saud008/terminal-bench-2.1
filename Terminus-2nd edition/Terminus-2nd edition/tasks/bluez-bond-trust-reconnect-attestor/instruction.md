Implement the bondattest BlueZ bond-trust reconnect attestor subsystem under /app for the fleet trust program. The absorb and seal workflows evaluate synthetic D-Bus bonding traces through the reconnect trust policy documented under /app/docs/ and produce a sealed attestation bundle over the resulting reconnect ledger.

The bondattest entrypoint lives at /app/scripts/bondattest and is installed to /usr/local/bin/bondattest with these subcommands:

  bondattest absorb --trace PATH --config PATH --seed SEED [--midstate PATH]
  bondattest seal [--midstate PATH] [--bundle PATH]

Absorb processes a trace's seed_bond, pairing_confirm, connect, disconnect, bond_remove, adapter_power, gatt_discover, and battery_level operations against the reconnect trust policy, accumulates a reconnect ledger, and writes a midstate snapshot to /app/state/bondattest-midstate.json (default). Seal reads that midstate snapshot and writes the attestation bundle to /app/output/bond-reconnect-attestation.json (default). Both artifacts carry policy-derived digest fields; the exact digest formulas live in /app/docs/midstate-and-bundle-seals.md, and /app/lib/digest/contract_hash.py provides the shared hashing helper used across the digest surface.

Trusted reconnect with a mismatched address type, resume-token clearing on bond removal, disconnect adapter-power capture ordering, GATT UUID identity deduplication, and battery-driven reconnect debouncing are policy areas covered by /app/docs/pairing-addr-type-gate.md, /app/docs/resume-token-revoke.md, /app/docs/disconnect-power-capture.md, /app/docs/gatt-uuid-identity.md, and /app/docs/battery-debounce-policy.md.

Bundled trace fixtures live under /app/fixtures/traces/ (including mixed-fleet-core.trace.jsonl) with roles documented in /app/docs/trace-catalog.md. The TB3_TRACE_DIR environment variable, when present, redirects a relative --trace argument to an alternate directory such as /opt/verifier-fixtures/bondattest_hidden or /tests/hidden_traces, which may hold additional hidden verifier traces. Module slice overlays used only by the verifier live under /tests/verifier_complete and /tests/verifier_incomplete. Run /app/scripts/reset-state.sh prior to cross-run verifier cases. The decoy helper under /app/lib/decoy is not used by absorb or seal. Ledger event names and other opaque tokens the verifier asserts on are catalogued in /app/docs/ledger-event-vocabulary.md. The environment has no outbound network access. Do not edit /app/docs/, /app/fixtures/, or /tests/.

Tests invoke bondattest through subprocess, rebuild the installed binary between cases, and compare midstate and bundle output to tests/bondattest_oracle.py contract math. Hardcoding midstate or bundle JSON is insufficient.
