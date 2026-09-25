Gap events record large timeline jumps. After normalization, when the combined delta_ns plus penalty_ns for a step exceeds GAP_THRESHOLD_NS, emit one gap ledger row.

Default GAP_THRESHOLD_NS is 1_000_000_000 (one second). Override with PCAP_JITTER_GAP_NS when set to a positive integer.

Each gap row is one JSON object per line appended to gap-ledger.jsonl under the ledger root. Fields:

seq (monotonic u64 starting at 1 for a fresh ledger root), after_index (index in the exported timeline packet list), gap_ns (the delta_ns + penalty applied for that step), prev_norm_ns, next_norm_ns.

Sequence numbers persist in gap-seq.txt under the ledger root and must continue across repeated export runs without resetting when the staging input is unchanged.

stats.gap_count in timeline export equals the number of gap rows written during that export run.
