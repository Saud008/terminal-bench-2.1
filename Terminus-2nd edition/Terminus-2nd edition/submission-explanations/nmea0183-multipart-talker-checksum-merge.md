# Submission explanations — nmea0183-multipart-talker-checksum-merge

**Task folder:** tasks/nmea0183-multipart-talker-checksum-merge/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a Rust NMEA0183 merge pipeline across ingest, session replay, and export stages. Checksum rules, quoted field parsing, talker normalization, multipart payload assembly, UTC rollover, and session pending buckets each live in different modules under /app/crates/nmeapipeline. Export reads /app/state/merge-snapshot.json and must not rebuild the report by re-parsing the input stream. Session replay adds duplicate fragment reconciliation where a later message number replaces an earlier pending copy. Partial fixes pass many bundled tests but fail hidden /opt/verifier-fixtures streams and partial-golden probe patches.

## Solution Explanation

The oracle applies targeted patches to parse, merge, context, and session modules, copies golden export and reconcile helpers, rebuilds nmeapipeline, and runs merge on the baseline stream. Ingest writes the staging snapshot with a canonical digest. Export validates canonical talker prefixes on merge_key (incomplete single-pass groups are allowed through), verifies the digest, and assembles the report in stream order. Session replay merges pending fragments, sorts by message number, reconciles duplicates, buffers incomplete groups without reporting them, and only persists buckets that include fragment one.

## Verification Explanation

test.sh rebuilds the Rust binary before pytest. About 40 behavioral tests invoke nmeapipeline merge via subprocess. An independent Python reference recomputes expected JSON from fixtures. Partial-golden tests swap single modules from verifier-golden while leaving others broken. Hidden streams under /opt/verifier-fixtures catch hardcoded answers. Tests cover merge-report.json, merge-snapshot.json, and merge-session.json paths. Oracle should score 1.0 and NOP 0.0.
