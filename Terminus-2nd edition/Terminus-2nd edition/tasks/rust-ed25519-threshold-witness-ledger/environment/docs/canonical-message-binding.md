# Canonical message binding

Ed25519 witness signatures must verify over UTF-8 bytes built from the witness fields using the TW1 line format.

Build the message as lines in this exact order, each line terminated by a single newline character, with no trailing spaces:

TW1
artifact_digest=<digest>
epoch=<unsigned integer>
prior_witness_id=<witness id or the literal none>
release_id=<release id>

The artifact_digest value must match the sha256 digest computed from bundle artifact file bytes at ingest time, including the sha256: prefix and lowercase hex.

JSON serialization, compact JSON, or reordering fields invalidates signatures.
