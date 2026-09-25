# Platform rubric — clickhouse-chpart-bundle-commit-order-repair

**Task folder:** tasks/clickhouse-chpart-bundle-commit-order-repair/

Agent validates part bundle checksums before committing rows and aborts ingest on mismatch, +3
Agent merges rows by primary key keeping the highest version column value, +3
Agent applies TTL pruning after merge completes using ttl_grace_ms from table config, +3
Agent finalizes commit barrier with fsync before publishing max_block_number to snapshot, +3
Agent writes export report from parts-snapshot.json only not parts.manifest or SQLite rows, +3
Agent keeps parts.manifest rows empty at ingest start as scratch artifact export must ignore, +2
Agent skips duplicate batch_id part_id idempotency keys on replay without duplicating rows, +2
Agent stages merged rows and part stats in parts-snapshot.json before export runs, +2
Agent exports parts array sorted ascending by part_id per export-schema contract, +1
Agent patches only export publish while leaving merge comparator broken, -3
Agent reads parts.manifest during export instead of parts-snapshot.json, -3
Agent runs TTL pruning before merge so lower version rows block fresher winners, -3
Agent commits parts with invalid checksum as committed in SQLite, -2
Agent re-walks parts directory during export instead of snapshot only, -2
Agent drops hidden tmp_path part bundle coverage for independent reference decode, -2
