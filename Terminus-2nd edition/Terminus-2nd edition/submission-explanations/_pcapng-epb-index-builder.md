# Submission explanations — _pcapng-epb-index-builder

**Task folder:** tasks/_pcapng-epb-index-builder/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is medium-hard because the PCAPng ingest pipeline must keep binary block traversal, zero-based interface assignment, CRC gating, SQLite persistence, JSONL index output, and export accounting aligned across three /app/docs contracts at once. Agents often fix block stepping or interface ids in isolation while export still sums per-interface row counts instead of counting distinct nanosecond timestamps globally, so dual-interface captures report packet_count 4 when the contract requires 3. EPB body CRC validation documented in pcapng-contract.md must reject bad blocks before any row reaches /app/state/pcap.idx, yet many partial fixes increment crc_rejected while leaving corrupt packets indexed. Replay deduplication depends on a three-part key including file_offset, so re-ingesting the same capture without that key silently duplicates rows or misses duplicate_rejected accounting. Partial fixes pass single-interface lan_single fixtures but fail hidden triple-interface captures with timestamp shifts that block hard-coded answers.

## Solution Explanation

The oracle patches five Rust modules under /app/src and rebuilds the release pcap-index binary. Block traversal advances using the leading block_total_length field rather than recomputing length from body size and padding alone. InterfaceMap assigns zero-based interface ids starting at 0 and resolves EPB interface_id values against IDB registration order. Ingest validates EPB core CRC-32 when the epb_body_crc32 option is present and skips indexing on mismatch while still recording crc_rejected. Export computes top-level packet_count as the number of unique ts_ns values across all accepted rows, not the sum of per-interface packet_count fields. Replay deduplication uses replay keys formatted as interface_id:ts_ns:file_offset so re-ingesting an identical capture increments duplicate_rejected without appending duplicate JSONL lines. Export writes capture-summary.json with per-interface counts, cumulative counters, and index_digest as lowercase SHA-256 of the exact /app/state/pcap.idx bytes.

## Verification Explanation

Five pytest functions drive /app/bin/pcap-index ingest and export through subprocess on every run after test.sh rebuilds the Rust release binary. An independent reference_pcapng module walks raw PCAPng bytes, simulates CRC rejection and deduplication, and builds expected JSONL index bytes plus capture-summary.json so answers cannot be hard-coded. Bundled lan_single, dual_iface, and crc_trap captures cover single-interface indexing, shared-timestamp deduplication in packet_count, and CRC rejections that must stay out of the index. A hidden triple_iface capture is timestamp-shifted via TB3_TS_OFFSET before ingest to verify three-interface mgmt naming and index_digest without fixture replay. Replay duplicate detection re-ingests lan_single into the same SQLite database and asserts duplicate_rejected reaches at least three while /app/state/pcap.idx bytes remain unchanged across passes.
