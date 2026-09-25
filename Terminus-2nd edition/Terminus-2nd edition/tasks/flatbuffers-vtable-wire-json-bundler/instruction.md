Task identity ecf23803ad defines the engineering problem for flatbuffers vtable wire json bundler. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Implement the Rust scene-to-JSON CLI under /app as a FlatBuffers bundler for game telemetry archives. The tool ingests little-endian scene tables from /app/fixtures/buffers/, walks signed vtable soffsets and uoffset field indirection per /app/schema/scene.fbs, and emits flatc-compatible JSON while persisting wire snapshot envelopes and decode journal lines under /app/state/. Wire hash invariants and schema slot ordering govern every snapshot reload before export. The baseline crate graph already links; complete the multi-stage pipeline so behavior matches /app/docs/wire-format.md, /app/docs/schema-contract.md, /app/docs/decode-staging.md, /app/docs/decode-ledger.md, /app/docs/decode-export-stage.md, /app/docs/decode-guard-contract.md, and /app/docs/fixture-catalog.md.

Implement missing behavior in the Rust sources under /app so every bundled buffer under /app/fixtures/buffers/ and independent verifier scenarios decode to the same JSON as flatc with strict JSON and defaults JSON for the same input. Read the docs together; no single compilation unit owns the full path.

Preserve existing public function and module names. Do not rename symbols consumed by other modules.

The tool exposes four subcommands:

Verifier helpers under /app/scripts/ include flatc_parity_ecf23803 for flatc JSON reference parity and wire_hash_helper for fixture SHA-256 digests.

- fbdecode stage with schema and input flags — wire decode, write snapshot, append ledger (no stdout JSON).
- fbdecode export with schema flag — read snapshot and ledger, render JSON to stdout.
- fbdecode verify with schema flag — report whether snapshot and ledger heads are aligned.
- fbdecode decode with schema and input flags — run stage then export in one invocation.

Successful export must read the reloaded snapshot payload and pass ledger alignment checks documented under /app/docs/decode-guard-contract.md and /app/docs/decode-export-stage.md. Restaging a different buffer must replace the snapshot at /app/state/decode.snapshot.json and advance the ledger head at /app/state/decode.ledger.jsonl before export binds.

cargo, rustc, and the CLI binary are already on PATH. Rebuild with cargo build --locked --release after Rust edits. Do not run apt-get, pip install, or other network installs.

After your implementation, fbdecode decode with schema /app/schema/scene.fbs and input /app/fixtures/buffers/shallow.bin must emit matching JSON on stdout for valid buffers, exit 1 on truncated or corrupt inputs, and exit 2 when required flags are missing.

Do not edit /app/docs/, /app/schema/scene.fbs, /app/fixtures/, or /tests/.
