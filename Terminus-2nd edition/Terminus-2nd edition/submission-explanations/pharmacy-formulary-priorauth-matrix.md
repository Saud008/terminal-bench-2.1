# Submission explanations - pharmacy-formulary-priorauth-matrix

**Task folder:** tasks/pharmacy-formulary-priorauth-matrix/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-25T18:30:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

HARD Case 1 repair after instruction-sufficiency FAIL: agents reached ~24/27 but never cleared roster digest (date-window), step_prereq, and matrix digest because contracts left raw-vs-normalized NDC and effective_rule baseline underspecified. Specs now state normalized NDC sort for roster digests, normalized PA map keys for step therapy, and baseline effective_rule. Fixtures force raw/norm sort divergence and a two-link last-only step trap so those rules are testable. Category metadata set to build-and-dependency-management (CLI/replay tooling). Re-eval required before claiming HARD band; prior 0/5 was unfair-spec blocked.

## Solution Explanation

Oracle installs corrected Go modules for NDC padding, RxNorm rank, override precedence with date tie-break, full step-chain traversal with normalized prerequisite lookups, roster digest sort by normalized NDC, SQLite UPSERT, refresh revision bump, and ascending matrix publish. Patches land under /app/internal, then rebuild formulatrix and regenerate fixtures.

## Verification Explanation

test.sh rebuilds via verifier-rebuild.sh then pytest. Coverage rules recompute roster_digest and matrix_digest from formulatrix_refmath. Overlay traps under /opt/verifier-fixtures enforce override precedence and multi-link step boundaries. Oracle reward 1.0 and NOP 0.0 confirmed locally after this revise.
