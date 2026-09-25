`term-lsp` is a host-local document-sync binary at `/usr/local/bin/term-lsp`. It speaks a small LSP-shaped stdio surface so offline workspace fixtures can open, change, close, and export documents. Several Rust modules under `/app/crates/` ship broken; diagnose and repair them so open / change / close / export match the contracts below. There is no live editor host and no outbound network step.

Evaluation rebuilds `/usr/local/bin/term-lsp` from the sources under `/app` before grading; replacing only the installed binary without aligning the crates will not pass.

### Glossary

- **Version monotonicity** -- accept a `didChange` batch only when its version is new for that URI; duplicate `(uri, version)` batches are ignored after the first successful apply.
- **UTF-16 positioning** -- map edit ranges with UTF-16 code-unit offsets so misaligned ranges do not shift later edits.
- **Staging queue** -- queue accepted edits separately from committed text until close or export merges them.
- **Snapshot export** -- after flush, export text, version, diagnostics, and `staging_pending`; a later reopen must round-trip those values without replaying earlier batches.

### Contracts

Contracts under `/app/docs/` define the enforceable behavior: `cli-reference.md` (supported methods and defaults), `text-document-sync.md` (open/change/close path), `utf16-positioning.md` (UTF-16 offsets), `staging-flush.md` (staging queue flush), `edit-application.md` (descending ordered merge), `version-monotonicity.md` (duplicate-version ignore), `diagnostics-recompute.md` (post-flush diagnostic counts), `export-snapshot.md` (export fields), `fixture-catalog.md` (bundled inventory), and `crate-module-layout.md` (crate layer ownership and stable public surfaces).

Open must seed committed text and document version. Change must append under version monotonicity and must ignore duplicate `(uri, version)` batches after the first successful apply. Flush on close and on snapshot export must merge staging into committed text before clearing the queue. Export must report `staging_pending` zero, flushed text, version, and diagnostics that match the post-flush buffer. A later process may reopen the same URI with that flushed text and version and must round-trip the same export values without replaying earlier change batches.

Bundled fixtures live under `/app/fixtures`; hidden verifier trees may appear under `/opt/verifier-fixtures`. Use `/app/scripts/reset-state.sh` between cross-run checks. After edits under `/app/crates/`, leave `/usr/local/bin/term-lsp` current. Do not edit `/app/docs/` or `/app/fixtures/`.
