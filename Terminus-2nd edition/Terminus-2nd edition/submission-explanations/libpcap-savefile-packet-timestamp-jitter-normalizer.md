# Submission explanations — libpcap-savefile-packet-timestamp-jitter-normalizer

**Task folder:** tasks/libpcap-savefile-packet-timestamp-jitter-normalizer/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is hard because the pcapjitter Rust CLI must keep libpcap ingest, on-disk staging, timeline export, and gap ledger persistence aligned across eight /app/docs contracts at once. Agents often fix endian decoding or tolerance-window ordering in one module while export still applies a full timestamp sort, skips truncation penalties on the prior packet, or writes gap rows without advancing gap-seq.txt. Normalization depends on stable window ordering where near-equal timestamps keep capture file order, then accumulates norm_ns with microsecond-to-nanosecond scaling plus per-byte truncation penalties before gap detection. Repeated export without new ingest must append duplicate gap ledger rows with monotonic sequence numbers persisted under the ledger root, which is easy to miss when bundled captures pass after a single-file patch. TB3_PCAP_DIR resolves ingest input basenames from an absolute probe directory, so path handling must follow cli.md rather than only the bundled fixture tree.

## Solution Explanation

The oracle copies corrected parse.rs, export_stage.rs, ledger.rs, and wrap.rs into /app/crates/pcapjitter/src, rebuilds with cargo, and runs ingest then export on a bundled capture. Ingest detects classic PCAP endianness from magic and version, records raw_ts_us per packet into /app/state/pcap-stage.json, and resolves --input through TB3_PCAP_DIR when set. Export reads staging, applies tolerance-window ordering, computes norm_ns with truncation penalties from the previous packet, and writes /app/output/timeline.json with packet rows and stats. Gap steps above the configured threshold append JSONL rows to gap-ledger.jsonl while gap-seq.txt tracks the next sequence across exports. Missing inputs exit 1 and malformed staging exits 2 per the export contract.

## Verification Explanation

Eleven pytest functions rebuild pcapjitter in test.sh, then drive ingest and export through subprocess with fresh /app/state and /app/output paths each run. An independent reference_parse_pcap and reference_timeline recompute staging fields, tolerance ordering, normalized nanoseconds, truncation totals, and gap rows from the same PCAP bytes, so hard-coded JSON cannot pass. Bundled captures under /app/fixtures/captures are SHA256-locked and exercise big-endian decoding, window-order stability, truncation stats, gap ledger rows, and monotonic sequence persistence across duplicate exports. Hidden capture 005-mixed-probe.pcap lives under /opt/verifier-fixtures/pcap and is ingested via TB3_PCAP_DIR basename resolution. Exit-code tests assert missing input returns 1 and invalid staging returns 2.
