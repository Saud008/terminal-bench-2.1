# Snapshot export contract

topic-key-snapshot.jsonl rows: canonical_key, partition, offset, value_raw, deleted.

deleted is true when the winning record for the key is a tombstone.

tombstone-lineage.jsonl rows: canonical_key, partition, offset, timestamp_ms for eligible tombstones only.

publish-keys requires curator_seal > 0.
