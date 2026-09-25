# Platform rubric — lsp-text-document-version-increment-repair

**Task folder:** tasks/lsp-text-document-version-increment-repair/

Agent rebuilds term-lsp with cargo build --release after editing Rust crates, +2
Agent applies staged edits in descending start position order on an evolving buffer, +3
Agent accumulates raw per-batch edits in staging without collapsing prior batches, +3
Agent flushes staging into committed text on both didClose and exportSnapshot, +3
Agent maps LSP UTF-16 line and character positions to byte offsets for edits, +3
Agent suppresses replay when didChange version matches last_change_version, +3
Agent seeds didOpen document version from the client-supplied textDocument.version, +2
Agent recomputes diagnostics from merged text after flush not pre-merge staging, +2
Agent fixes UTF-16 mapping alone while overlapping batch edit order still fails, -3
Agent fixes staging flush on close alone while export still skips merge_staging, -3
Agent fixes version replay gate alone while apply_edits still uses ascending order, -3
Agent resets document version to zero on restart after export round-trip, -3
