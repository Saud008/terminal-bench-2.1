# BGP feed format

NDJSON lines with fields ts_ms, peer, prefix, kind where kind is announce or withdraw.

After normalize, events sort by ts_ms ascending, peer, prefix, announce before withdraw at equal ts_ms.

Drop duplicate lines with identical ts_ms, peer, prefix, kind keeping first only.

Per-peer ts_ms must be non-decreasing in source sequence before global sort.
