# Submission explanations — lsp-text-document-version-increment-repair

**Task folder:** tasks/lsp-text-document-version-increment-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is hard because DocLint incremental sync couples UTF-16 offset mapping, descending evolving-buffer edit application, cross-batch staging accumulation, version monotonicity with replay suppression, and export-time flush with diagnostic recomputation across five Rust modules in three crates. Contracts in text-document-sync.md, edit-application.md, and staging-flush.md split the rules, so fixing flush-on-close alone still fails export snapshots, and correcting UTF-16 alone still breaks overlapping same-batch edits in beta22 and gamma99 seed fixtures. Partial-trap tests hot-swap single golden modules into an otherwise broken tree and expect remaining defects to surface, punishing one-file patches. Server-restart scenarios require didOpen to honor the exported version, not reset to zero.

## Solution Explanation

The oracle replaces broken sources under docmodel, docsync, and docexport with golden implementations, then rebuilds term-lsp with cargo build --release. apply_edits must sort staging descending and mutate an evolving buffer; handle_did_change must extend staging from working text, gate replay via last_change_version, and bump version only after acceptance. handle_did_open must store the client version for restart round-trips. handle_did_close and export_snapshot must share the same merge_staging flush primitive before diagnostics run on merged text. Agents must preserve the public APIs listed in crate-module-layout.md so the workspace keeps compiling after each module change.

## Verification Explanation

Pytest runs behavioral cases after test.sh rebuilds term-lsp and drives JSON-RPC over stdio via an LspClient wrapper. Tests replay cataloged batch sequences from core-sequences.jsonl, compare export snapshots against an independent reference_lsp Python module, and pin fixture hashes so agents cannot edit catalogs or docs. Seed mutations alpha01, beta22, gamma99, epoch07, and surro88 vary edit payloads and exercise ASCII overlap, UTF-16 surrogate lines, and replay gates. Partial-trap tests install only one golden module at a time and assert cross-module failures remain, blocking shallow repairs that pass the default integration path but fail hidden overlap or restart checks.
