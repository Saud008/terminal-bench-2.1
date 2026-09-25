# Submission explanations — geojson-polygon-ring-orientation-validity-repair

**Task folder:** tasks/geojson-polygon-ring-orientation-validity-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is medium because the agent must repair nine cooperating Rust modules so geojson-fix produces valid polygon and multipolygon geometries with a contract-correct repair report, not patch one obvious winding bug. Sanitize, close, nest, orient, multipolygon normalization, staging persistence, and export each implement part of the pipeline described in /app/docs/fixture-catalog.md, and repair.rs must orchestrate nest-then-orient in the right order. Exterior rings must end counter-clockwise and holes clockwise, but hole-outside-order and multi-hole-nest fixtures fail if nesting or area-based exterior selection is wrong even when orient alone looks fixed. Export must publish from the on-disk staging snapshot and ledger digest with a repair_binding hash, so agents who fix coordinates in memory but skip staging still fail binding and snapshot tests.

## Solution Explanation

The oracle copies golden implementations into /app/crates/geojson-core/src/ for area, close, sanitize, orient, nest, multi, staging, export, and repair, then rebuilds geojson-fix with cargo build --locked --release. Per polygon the repair path sanitizes duplicate vertices, normalizes closure to a single repeated closing vertex, nests rings so the largest exterior leads and invalid exterior holes drop, then orients CCW exteriors and CW interiors while incrementing the documented stats counters. Multipolygon members keep index order after per-member repair. Before write_report, persist_repair_snapshot sorts fixtures, writes /app/state/repair-snapshot.json, appends a ledger entry with the snapshot digest, and export derives repair_binding from that staged body rather than ad-hoc arguments. ring_audit.rs stays off the hot path as documented in /app/docs/ring-audit.md.

## Verification Explanation

Pytest rebuilds the Rust binary in test.sh, then drives geojson-fix repair via subprocess against bundled and isolated fixture directories. An independent reference_geojson.py recomputes the full repair-report.json, stats, staging digest, and repair_binding so baked JSON cannot pass. Eight catalog fixtures are checked individually and as a full tree, with signed-area assertions for winding, multipolygon order preservation, duplicate-vertex and double-close normalization, idempotent reruns, and snapshot-ledger-binding consistency. A hidden outside-hole-drop fixture under /opt/verifier-fixtures exercises dropping holes that lie outside the exterior. Seeded coordinate shifts block hard-coded outputs, and parametrized partial golden patches prove fixing only one module while leaving broken orchestration or miscounted close stats still fails the catalog.
