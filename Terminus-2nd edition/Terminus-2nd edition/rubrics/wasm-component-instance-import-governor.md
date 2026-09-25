# Platform rubric — wasm-component-instance-import-governor

**Task folder:** tasks/wasm-component-instance-import-governor/

Agent canonicalizes import rows by module-then-name tuple byte rank not import name alone, +3
Agent resolves attestation type_index through component-type alias tables for local indices, +3
Agent validates export section LEB128 span before reading export kind discriminants, +3
Agent closes instance re-export alias chains transitively to terminal function exports, +3
Agent seals import_reorder_digest from post-canonical import bytes not raw wire image, +3
Agent reads /app/state/import-alias.bin in attest export without reloading component files, +2
Agent rebuilds /app/bin/component-gov with cargo build --release after editing canonicalize or attest Rust sources, +2
Agent applies TB3_TYPE_ALIAS_OFFSET when emitting module-type indices in attestation, +2
Agent leaves crates/decoy-wrap off the canonicalize and attestation hot path, +1
Agent sorts imports by concatenated module-plus-name string key for export ordering, -3
Agent emits raw local type indices when alias rows exist in the ledger, -3
Agent reads export kind tags before confirming LEB128 payload bounds, -3
Agent resolves instance re-export surfaces with single-hop alias peeling only, -3
Agent hashes pre-canonical CWRC wire bytes for import_reorder_digest, -3
