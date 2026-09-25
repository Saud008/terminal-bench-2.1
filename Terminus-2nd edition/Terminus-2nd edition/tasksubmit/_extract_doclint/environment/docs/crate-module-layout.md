# Authenticity-policy layer ownership

The document-integrity control plane splits authenticity policy across library layers under `/app/crates/`. Admission handlers under `/app/crates/term-lsp/src/` must stay thin and delegate to these owners so version anti-replay, position integrity, staging flush, and snapshot attestation remain mutually compatible.

## docmodel

Owns UTF-16 position integrity mapping, edit application, and committed/staging text merging.

Public types: Document, Range, Position, ContentChange, StagedEdit (fields in types.rs).

Public functions re-exported from lib.rs:

- byte_offset(text, line, character) -> usize
- apply_edits(base, edits) -> String
- changes_to_edits(changes, full_text) -> Vec<StagedEdit>
- working_text(doc) -> String
- merge_staging(doc) -> ()

Document carries uri, version, text, staging, and last_change_version. Other layers read and mutate Document through these APIs; do not duplicate buffer state elsewhere.

## docsync

Owns open, change, and close admission lifecycle under version-monotonicity policy.

Public functions:

- handle_did_open(uri, text, version) -> Document
- handle_did_change(doc, new_version, changes) -> Result<()>
- handle_did_close(doc) -> Result<()>

Internal staging helpers (append_staging, clear_staging, staging_len) stay in staging.rs and are used by change.rs and lifecycle.rs.

## docexport

Owns `doclint.exportSnapshot` attestation assembly.

Public function:

- export_snapshot(doc) -> Result<ExportSnapshot>

ExportSnapshot fields: uri, version, text, diagnostics (todo_count and related counters per diagnostics-recompute.md), staging_pending.

## docdiag

Owns diagnostic recomputation from merged text only. docexport calls compute_diagnostics; handlers do not compute diagnostics directly.

## Compatibility

All authenticity-policy layers must remain mutually composable so `cargo build --release --locked -p term-lsp` succeeds after mixed baseline/agent layer trees. When you change one policy layer, preserve the public function signatures and struct fields listed above. Behavioral requirements for admission, flush, UTF-16 integrity, and export live in the other contract documents under `/app/docs/`; this file defines only ownership and stable cross-layer surfaces.
