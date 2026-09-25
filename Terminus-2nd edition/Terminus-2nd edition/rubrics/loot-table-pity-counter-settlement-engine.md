# Platform rubric — loot-table-pity-counter-settlement-engine

**Task folder:** tasks/loot-table-pity-counter-settlement-engine/

Agent rebuilds lootsettle with cargo build after lootsettle-core Rust edits, +2
Agent implements lootsettle ingest to write settlement-staging.json with events_digest, +3
Agent verifies HMAC signatures using secret and pool_epoch key material in envelope.rs, +3
Agent applies seasonal pity carryover using the new season carry_ratio on season change, +3
Agent rejects loot events whose pool_epoch does not match the active season table, +2
Agent converts duplicate item grants into shard currency per duplicate_shards table, +3
Agent skips duplicate event_id replays and records duplicate_skip audit rows, +3
Agent validates staging digest and replay generation gate before export publish, +3
Agent writes settlement-report.json with sorted audit log and settlement_digest hash, +2
Agent leaves decoy.rs weight merge helpers off settlement export hot path, +1
Agent patches export sorting only while staging digest validation stays disabled, -3
Agent fixes envelope verification but leaves duplicate shard conversion broken, -3
Agent edits decoy.rs expecting settlement balances to change without export edits, -2
Agent accepts stale pool_epoch values without season binding rejection, -2
Agent skips cargo rebuild after editing lootsettle-core source modules, -2
