# Submission explanations — ipmi-sel-hex-export-normalizer

**Task folder:** tasks/ipmi-sel-hex-export-normalizer/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is medium-hard because the sel-chain pipeline must keep binary SEL parsing, per-run staging counters, SQLite persistence, and CSV export sorting aligned across four /app/docs contracts at once. Agents often fix sensor name lookup or checksum rejection in isolation while export still sorts rows by timestamp instead of severity rank, so a later warning can appear before an earlier critical event. OEM sensor types documented only in ipmi-sel.md must resolve alongside bundled TSV hex keys, and corrupt record_xor payloads must increment rejected_checksum without ever inserting the row. Re-ingesting the same blob must dedupe by record_id and report duplicate_rejected for the second pass while leaving the database unchanged. Partial fixes pass alpha fixtures but fail hidden blobs that combine doc-only sensor types with severity-first ordering traps.

## Solution Explanation

The oracle replaces parse.sh, sensor_map.sh, sel-ingest.sh, and sel-export.sh under /app so sel-chain ingest and export follow the documented contracts. Ingest validates the SEL1 header xor, walks fixed-length system event records, rejects bad record_xor before insert, skips duplicate record_ids, and writes a canonical staging snapshot to /app/state/sel.stage with per-run accepted, rejected_checksum, duplicate_rejected, and ingest_digest fields. Sensor names resolve from /app/config/sensor-types.tsv using uppercase 0x-prefixed keys plus the OEM types listed in ipmi-sel.md. Export reads sel_records from SQLite, formats ISO-8601 timestamps and hex columns, and sorts by severity rank then timestamp then record_id before writing /app/output/sel-events.csv.

## Verification Explanation

Twelve pytest functions drive /app/bin/sel-chain ingest and export through subprocess on every run after resetting /app/state and /app/output. An independent reference_sel module parses the same binary fixtures, simulates ingest accounting, and builds expected CSV and staging JSON so answers cannot be hard-coded. Bundled sel_alpha.bin and sel_beta.bin cover severity ordering, staging counts, TSV sensor names, OEM doc-only types, checksum rejection, and duplicate replay behavior. A hidden test synthesizes a non-bundled blob under /tmp/sel_hidden_fixtures with Platform Security and OEM Memory Channel sensors to verify severity-first export when timestamps would suggest the opposite order. Tests also assert canonical staging bytes with sorted JSON keys and trailing newline, and that CSV data row count matches sel_records row count.
