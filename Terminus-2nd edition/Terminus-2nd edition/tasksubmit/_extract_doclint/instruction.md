Build a host-local document-integrity attestation control plane at `/usr/local/bin/term-lsp` that admits offline workspace document batches, enforces version anti-replay and position-integrity gates, stages a tamper-evident edit queue, and publishes a digest-sealed snapshot attestation only after lifecycle authenticity gates hold--without a live editor host or outbound network step.

This is a security document-integrity and version-admission workflow: keep version-monotonicity anti-replay, UTF-16 position integrity, tamper-evident staging flush, lifecycle authenticity, and digest-sealed snapshot attestation aligned. It is not a generic language-server, Rust crate rebuild, editor-plugin, or CI tooling exercise.

### Glossary

- **Version admission** -- accept a document batch only when its version advances under monotonicity policy; duplicate `(uri, version)` batches are anti-replay rejects after the first successful apply.
- **Position integrity** -- map edit ranges with UTF-16 code-unit offsets so tampered or misaligned ranges cannot shift later edits.
- **Tamper-evident staging** -- queue admitted edits separately from committed text until a flush authenticity gate merges them.
- **Snapshot attestation** -- export flushed text, version, diagnostics, and `staging_pending` only after flush; a later reopen must round-trip those attested values without replaying earlier batches.

### Security contracts

Contracts under `/app/docs/` define the enforceable gates: `cli-reference.md` (admission verbs and defaults), `text-document-sync.md` (open/change/close admission path), `utf16-positioning.md` (position integrity), `staging-flush.md` (tamper-evident queue flush), `edit-application.md` (ordered merge under authenticity policy), `version-monotonicity.md` (anti-replay), `diagnostics-recompute.md` (post-flush diagnostic counts), `export-snapshot.md` (digest-bound attestation fields), `fixture-catalog.md` (bundled inventory), and `crate-module-layout.md` (authenticity-policy layer ownership).

Open must seed committed text and document version. Stage must append under monotonic version admission and must ignore duplicate `(uri, version)` batches after the first successful apply. Flush on close and on snapshot export must merge staging into committed text before clearing the queue. Export must report `staging_pending` zero, flushed text, version, and diagnostics that match the post-flush buffer. A later process may reopen the same URI with that flushed text and version and must round-trip the same export values without replaying earlier change batches.

Bundled fixtures live under `/app/fixtures`; hidden verifier trees may appear under `/opt/verifier-fixtures`. Use `/app/scripts/reset-state.sh` between cross-run checks. After authenticity-policy edits under `/app/crates/`, leave `/usr/local/bin/term-lsp` current. Do not edit `/app/docs/` or `/app/fixtures/`.
