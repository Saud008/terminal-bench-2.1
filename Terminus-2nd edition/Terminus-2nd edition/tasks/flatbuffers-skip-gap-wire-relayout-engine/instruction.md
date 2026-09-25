Implement the fbctl wire-buffer relayout governor on the working Rust baseline under /app. The tool scans game-asset FlatBuffers wire images from a directory, materializes a binary relocation ledger at /app/state/vtable-ledger.bin, and exports a relaid wire image plus sealed attestation under /app/output.

Your work must satisfy every contract cited below. The src/decoy module is not on the ingest or relayout export hot path and must not be edited for a correct export.

Build /app/bin/fbctl from the workspace root. Subcommands:

  fbctl ingest <wires-dir>
  fbctl relayout export

After ingest, /app/state/vtable-ledger.bin must capture each source wire in sorted filename order with decoded vtable slot maps, skip-gap span coordinates, and root table offsets copied from the wire bytes.

relayout export reads the ledger only (never re-reads raw wire files from the ingest directory). It writes /app/output/relayout.wire and derives /app/output/wire-seal.txt from the final wire bytes defined in /app/docs/wire-seal-export.md

Vtable scalar decode must follow /app/docs/vtable-decode-contract.md: all vtable header and slot offsets are little-endian on the wire. Using native-endian reads for u16 or u32 vtable fields is incorrect.

Relayout padding must follow /app/docs/relayout-padding.md: alignment padding for relocated tables is applied only after vtable pointer fixup completes. Inserting padding before rewriting the vtable soffset corrupts the root offset.

Skip-gap preservation must follow /app/docs/skip-gap-preservation.md: GAPS-marked filler spans between tables must be copied verbatim into the export buffer. Discarding gap bytes during relayout is incorrect.

Vtable validation must follow /app/docs/staging-ledger.md: the ledger writer must confirm vtable byte length is at least four before consulting field presence slots. Checking presence bits on a truncated vtable is incorrect.

Wire seal ordering must follow /app/docs/wire-seal-export.md: the SHA-256 digest must cover the relayout buffer after the gap restoration pass completes. Hashing the post-relayout buffer before gap bytes are restored is incorrect.

Multi-root wire images use the MR2R footer described in /app/docs/wire-buffer-layout.md. Bundled fixtures use /app/data/wires. Hidden verifier fixtures may supply additional wire directories at runtime.
