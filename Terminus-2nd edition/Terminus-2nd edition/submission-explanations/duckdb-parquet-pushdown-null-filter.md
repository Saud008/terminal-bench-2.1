# Submission explanations — duckdb-parquet-pushdown-null-filter

**Task folder:** tasks/duckdb-parquet-pushdown-null-filter/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must align five interacting Go modules for Parquet predicate pushdown. IS NULL pruning must treat omitted null_count stats as unknown, not zero. Dictionary and null_bitmap pages decode in catalog-specific order, and timestamp bounds must stay UTC even when the shell TZ differs. Parallel worker slices depend on chunk_size metadata. Fixing one module passes some bundled catalogs but fails hidden verifier fixtures and partial-fix traps.

## Solution Explanation

The oracle copies golden planner, stats, page, timezone, and parallel modules into /app/internal, then rebuilds parquet-pushdown-scan with go build. Ingest loads catalog JSON through the parse stage while staging writes /app/state/pushdown-plan.json with plan_written set before export runs. Export computes plan_checksum as the first 16 hex characters of SHA-256 over compact JSON of that plan and emits matched_row_ids plus pruned_row_groups. A smoke filter on the merged catalog confirms the full ingest-to-export path. The decoy ledger wrap module is not on the hot path and should remain untouched.

## Verification Explanation

test.sh rebuilds the Go CLI before pytest. Twenty-three behavioral tests call parquet-pushdown-scan via subprocess and compare output to an independent reference_pushdown implementation. Two tests read catalogs from /opt/verifier-fixtures for traps not in the bundled tree. Partial-fix tests swap single golden modules into a broken baseline and assert results still disagree with reference. NOP on the unpatched image scores zero.
