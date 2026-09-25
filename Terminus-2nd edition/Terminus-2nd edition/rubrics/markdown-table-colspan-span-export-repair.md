# Platform rubric — markdown-table-colspan-span-export-repair

**Task folder:** tasks/markdown-table-colspan-span-export-repair/

Agent rebuilds mdtable with cargo build after mdtable-core Rust edits, +2
Agent implements escaped pipe cell splitting in parse/cells.rs per table-extension-contract.md, +2
Agent skips alignment rows when building body rows in parse/table.rs, +2
Agent decodes colspan and rowspan span markers in span/markers.rs, +3
Agent places cells on logical grid with rowspan occupancy tracking in span/grid.rs, +3
Agent persists grid.snapshot.json on successful export in snapshot/mod.rs, +3
Agent implements publish to read snapshot bytes only in export/publish.rs, +3
Agent exports HTML table rows with colspan and rowspan attributes in export/html.rs, +2
Agent computes column_count from grid occupancy not raw per-row cell counts, +2
Agent strips span markers from exported JSON and HTML cell text, +2
Agent fixes export/json.rs only while grid snapshot persistence stays missing, -3
Agent patches publish to recompute column_count from markdown instead of snapshot, -3
Agent edits span markers only expecting rowspan slot skipping to pass bundled fixtures, -2
Agent skips cargo rebuild after editing mdtable-core source modules, -2
Agent hardcodes fixture export output instead of parsing markdown tables, -3
