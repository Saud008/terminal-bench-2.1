sledtool batch applies JSONL put/delete operations to /app/state/staging.json for the named table.

sledtool publish moves staging into /app/state/committed.json, writes /app/state/sled-staging-snapshot.json, flushes /app/state/page_registry.json, and appends split events to /app/state/split_journal.jsonl when splits occurred. Split journal append order and crash replay live in the journal crate under /app/crates/sled_engine/src/journal. Publish with empty staging leaves committed export byte-identical to the prior publish for that table.

sledtool snapshot-pin records pinned page ids under /app/state/pins/ for the snapshot id.

sledtool compact reclaims page ids in /app/state/page_registry.json that are not reachable from the live tree and not pinned.

sledtool journal-replay applies a crash-boundary journal file idempotently by split_seq.

sledtool scan-range exports committed keys in inclusive start/end order to JSON.

sledtool export writes the full committed table as sorted JSON.

sledtool walk prints root height, leaf count, key count, and physical entry count.

TB3_TABLE_PREFIX when set to an absolute path prefixes table names for batch, publish, scan-range, export, and walk. Verifier smoke uses /app/state/tb3_lane as an example absolute prefix.
