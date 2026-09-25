# Submission explanations - doclint-version-sync-snapshot-ledger

**Task folder:** tasks/doclint-version-sync-snapshot-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-29T20:45:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category (escalated — round 3):** Zip now sets `category = "debugging"` with `subcategories = ["tool_specific"]` — primary activity is diagnosing/repairing five broken Rust modules (`utf16.rs`, `apply.rs`, `change.rs`, `lifecycle.rs`, `snapshot.rs`) so document-sync behaves. Prior `security` remint rejected: no hash/signature/digest primitive in the crates (HashMap aside); `export_snapshot` emits `{uri, version, text, diagnostics, staging_pending}` with no attestation math. Taxonomy keys on primary activity, not theme. Harbor hard-blocks `debugging` / `software-engineering` for new uploads — **keep escalated for a team decision**; do not remint to `security`, `games`, or `system-administration` lipstick. Reviewer flagged the same on 2026-07-29.

**Done this round:**
- Dropped security / attestation / tamper-evident / anti-replay framing from `instruction.md` and `/app/docs/`; prompt describes plain document-sync repair (removed the “not a language-server / Rust crate rebuild…” negation).
- `subcategories = ["tool_specific"]` (LSP-shaped sync tool surface).
- `difficulty = "medium"` kept (measured gpt5 60% / opus 5/5).
- `solve.sh` buffer.rs no-op copy already comments that it ships correct on purpose.
- `solution/files/*.rs` already LF (matches verifier-golden).

**CI noise to ignore (do not revise for these):**
- Agent review “non-canonical base image” — `FROM` is already `public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe…` (canonical Rust image + digest). Leave it.
- Agent-failure / “Task Instruction Sufficiency: FAIL” on stable `lib.rs` surface — documented in `crate-module-layout.md` (preserve listed public signatures; “do not add new lib.rs re-exports”). Failed trials added prohibited cross-module exports; opus 5/5 shows the constraint is navigable.
- Automated review push to `hard` off time estimate — ignore; difficulty is measured pass rate, not LOC/complexity. Keep `medium`.
- Local `ensure_category_allowed` / `subcategories_empty` gates will fail on this slug by design while Harbor blocks honest debugging — do not auto-remap.

## Difficulty Explanation

Eval measured medium (opus 5/5, gpt5 3/5), so `difficulty = "medium"`. The work still spans UTF-16 offsets, descending edit order, staging accumulation/flush, and post-flush snapshot assembly across docmodel/docsync/docexport, but the measured agent success rate no longer supports hard.

## Solution Explanation

The oracle drops corrected sources for the five broken modules into `/app/crates/` (plus a no-op overwrite of already-correct `buffer.rs` for overlay parity), rebuilds `term-lsp`, and exercises open/change/close/export against the same fixtures agents see. Open seeds committed text and version; change appends under version monotonicity; close and export flush staging before export. Key insight: keep UTF-16 mapping, edit ordering, staging merge, and snapshot assembly aligned across layers instead of patching one handler in isolation. A reopen with exported text and version must round-trip without replaying earlier batches.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest drives `/usr/local/bin/term-lsp` via the stdio client and compares against an independent reference model. Hidden fixtures under `/opt/verifier-fixtures` and broken-layer overlays catch partial fixes. The partial-patch / mixed-layer constraint is documented in `crate-module-layout.md` (mutually composable layers; no new `lib.rs` re-exports). NOP on the broken baseline should score below a full reward. After the oracle patches and rebuild, the suite should pass cleanly.
