# Prefix-overlap ops contract

geocur admits overlapping IPv4 prefix announcements from independent GeoIP and routing-table feeds on this host. The ops problem is network prefix reconciliation under admission and export barriers, not probabilistic sketch estimation or counter aggregation.

Correct behavior requires normalized CIDR keys, RFC-reserved range drops, lexicographically smaller feed_id winners when multiple feeds supply the same normalized prefix key, asn_lineage chains listing every distinct feed lineage_id on shared keys, containment edges between nested blocks, and a sealed atlas report with an audit digest tied to summary counters and lineage chains.

State moves from raw bundle compile-feeds to a feed-normalize WAL snapshot, then to a seed-scoped overlap-generation ledger row, then to a caller-selected overlap report file. emit-overlap must read persisted feed-cache bytes rather than re-derive overlap rows from raw bundle JSON alone.

Ops validation refreshes /app/bin/geocur from the on-host Rust source tree under /app before grading CLI behavior (cargo build --release --locked), and overwrites any prior binary at that path. The graded surface is that source tree: STUB-marked policy modules under /app must satisfy the contracts above. A swapped or non-Rust binary alone is not sufficient.
