# Submission explanations — meilisearch-geo-bbox-filter-ranking-docid-repair

**Task folder:** tasks/meilisearch-geo-bbox-filter-ranking-docid-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is medium because the agent must align six cooperating Rust modules with Meilisearch-style geo search contracts, not fix one obvious coordinate swap. Ingest rejects nested _geo objects, the R-tree builds envelopes with latitude and longitude on the wrong axes, and export_stage ranks candidates before bbox filtering so near-but-outside points steal hit slots. Tie-breaking uses insertion order instead of lexicographic docid, cache keys omit TB3_GEO_PRECISION rounding, and store.rs persists the index before the staging snapshot. Partial repairs pass some bundled Paris fixtures yet still fail hidden traps where filter order, axis orientation, or cache precision matter independently. A spatial_wrap decoy module sits off the search hot path, so agents who chase the wrong file never reach export_stage wiring.

## Solution Explanation

The oracle copies golden implementations into the six repair-scope modules listed in /app/docs/repair-scope.md, then rebuilds geo-search-cli with cargo build --release --locked. parse.rs accepts _geo as a nested lat/lng object, rtree.rs maps lng to the x envelope axis and lat to y, and store.rs writes /app/state/ingest-staging.jsonl before updating /app/work/index.json. export_stage.rs applies strict bbox filtering on R-tree candidates before haversine ranking, tiebreak.rs breaks equal scores by ascending docid, and key.rs rounds bbox and center edges half-away-from-zero using TB3_GEO_PRECISION. The rebuilt binary is installed to /usr/local/bin/geo-search-cli and reset-state.sh clears work and output directories for a clean run.

## Verification Explanation

Pytest rebuilds the workspace in test.sh, then drives geo-search-cli ingest and search through subprocess on bundled fixture batches. An independent reference_geo_search.py recomputes staging line counts, ranked docid order, and cache keys so hard-coded JSON cannot pass. Tests assert staging precedes index updates, idempotent re-ingest, lexicographic tie-break ordering, and SHA256 integrity of protected docs, fixtures, and CLI entrypoints. Hidden batches under /opt/verifier-fixtures exercise filter-before-rank ordering when the center sits far outside the bbox, TB3_GEO_PRECISION cache-key rounding, and Japan-axis envelope overlap. Parametrized partial patches prove rtree-only or spatial_wrap decoy fixes still fail when export_stage keeps rank-then-filter semantics.
