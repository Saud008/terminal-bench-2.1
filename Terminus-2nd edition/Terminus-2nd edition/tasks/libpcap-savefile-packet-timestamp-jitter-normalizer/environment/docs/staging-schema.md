Ingest writes /app/state/pcap-stage.json (or the path passed to --staging) with:

source (string path ingested), snaplen (u32 from global header), network (u32 link type), packets (array ordered by original file index).

Each packet object: index, ts_sec, ts_usec, incl_len, orig_len, raw_ts_us (u64 pre-normalization sum from savefile-format.md using correct endianness).

Staging must reflect parsed header fields before tolerance reordering.
