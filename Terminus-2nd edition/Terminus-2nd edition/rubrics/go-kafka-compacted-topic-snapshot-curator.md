# Platform rubric — go-kafka-compacted-topic-snapshot-curator

**Task folder:** tasks/go-kafka-compacted-topic-snapshot-curator/

Agent pulls seg_NNN.jsonl files in numeric order into frozen-segment-snapshot.json with staging_digest, +3
Agent orders records by partition then offset and collapses duplicate offsets keeping greater timestamp_ms, +3
Agent applies tombstone retention window from partition high-water timestamp for lineage eligibility, +2
Agent canonicalizes keys with NFC normalization and user: prefix lowercasing per key-normalize-contract.md, +2
Agent compacts latest record per canonical key and marks deleted when tombstone wins, +2
Agent publishes snapshot rows sorted by canonical_key and lineage sorted by partition then offset, +2
Agent increments curator_seal before publish-keys and blocks export when seal is zero, +2
Agent rebuilds kcompactctl with verifier-rebuild.sh after editing Go sources before pytest, +1
Agent patches only publish sorting while leaving segpull segment order broken, -3
Agent hard-codes snapshot rows instead of walking collapsed partition state, -3
Agent consults decoy rollup_alias module on segpull or publish hot path, -2
Agent weakens hidden TB3 retention-bias or canonical-trap fixture coverage, -2
Agent publishes keys before audit-log increments curator_seal barrier, -3
