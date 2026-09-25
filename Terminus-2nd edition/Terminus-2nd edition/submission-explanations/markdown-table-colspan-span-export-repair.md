# Submission explanations — markdown-table-colspan-span-export-repair

**Task folder:** tasks/markdown-table-colspan-span-export-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must repair the mdtable Rust CLI so pipe-style Markdown tables export to JSON and HTML across eight interacting modules. Contracts spread colspan prefix markers, rowspan suffix markers, alignment-row skipping, escaped pipes, and logical grid placement across five docs under /app/docs/. Export is a two-stage pipeline: parse and place cells, write /app/state/grid.snapshot.json, then publish output from that snapshot only. Partial fixes pass simple bundled tables but fail mixed-grid column_count traps, publish-after-snapshot-mutation checks, hidden duplicate-text spans from verifier-fixtures, and dynamically seeded tables. Every source edit requires a cargo rebuild and mdtable reinstall.

## Solution Explanation

The oracle copies eight golden Rust modules from solution into mdtable-core parse, span, snapshot, and export paths, then runs cargo build release for mdtable. Cells and table parsing handle escaped pipes and alignment rows. Markers and grid modules decode span syntax and track rowspan occupancy when placing body rows. Snapshot writes the logical grid model before JSON or HTML publish reads those bytes without re-parsing the input file. Publish fails when the snapshot file is missing.

## Verification Explanation

Pytest drives mdtable export and publish through subprocess CLI calls and compares JSON and HTML semantics to an independent Python reference_parser. Bundled fixtures under /app/fixtures/tables cover basic, colspan, rowspan, escaped pipe, alignment, and mixed-grid cases. Hidden trap 007-duplicate-text loads from verifier-fixtures only. Snapshot tests mutate grid.snapshot.json column_count and assert publish honors the file. test.sh rebuilds mdtable before pytest. Oracle reward is 1 only when all 23 behavioral tests pass.
