# Crate module layout

The term-lsp workspace splits document logic across library crates. Handler code under /app/crates/term-lsp/src/ must stay thin and delegate to these owners.

## docmodel

Owns UTF-16 position mapping, edit application, and committed/staging text merging.

Public types: Document, Range, Position, ContentChange, StagedEdit (fields in types.rs).

Public functions re-exported from lib.rs:

- byte_offset(text, line, character) -> usize
- apply_edits(base, edits) -> String
- changes_to_edits(changes, full_text) -> Vec<StagedEdit>
- working_text(doc) -> String
- merge_staging(doc) -> ()

Document carries uri, version, text, staging, and last_change_version. Other crates read and mutate Document through these APIs; do not duplicate buffer state elsewhere.

## docsync

Owns RPC lifecycle for open, change, and close.

Public functions:

- handle_did_open(uri, text, version) -> Document
- handle_did_change(doc, new_version, changes) -> Result<()>
- handle_did_close(doc) -> Result<()>

Internal staging helpers (append_staging, clear_staging, staging_len) stay in staging.rs and are used by change.rs and lifecycle.rs.

## docexport

Owns doclint.exportSnapshot assembly.

Public function:

- export_snapshot(doc) -> Result<ExportSnapshot>

ExportSnapshot JSON fields: uri, version, text, diagnostics (todo_count and related counters per diagnostics-recompute.md), staging_pending.

## docdiag

Owns diagnostic recomputation from merged text only. docexport calls compute_diagnostics; handlers do not compute diagnostics directly.

## Compile contract

All workspace members must build together with cargo build --release --locked -p term-lsp. When you change one module, preserve the public function signatures and struct fields listed above so dependent crates still compile. Behavioral requirements for sync, flush, UTF-16, and export live in the other contract documents under /app/docs/; this file defines only ownership and stable cross-crate surfaces.
