# Platform rubric — mavlink-crc-extra-message-id-routing

**Task folder:** tasks/mavlink-crc-extra-message-id-routing/
**Written:** 2026-06-25T18:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent validates MAVLink v2 CRC with catalog crc_extra bytes, +3
Agent permutes frames by seed and frame offset before validation, +3
Agent applies per sysid compid session guard with u8 wrap-forward, +3
Agent deduplicates on sysid compid msg_id seq tuple, +2
Agent merges checkpoint frames before new rows on resume, +3
Agent writes decode.snapshot.json with payload as JSON byte arrays, +3
Agent publishes export from snapshot without re-decoding streams, +3
Agent rebuilds mavctl with cargo before pytest subprocess calls, +2
Agent ignores decoy_wrap export helper off publish hot path, +1
Agent hardcodes export JSON without running mavctl decode, -3
Agent stores snapshot payload as hex string instead of byte array, -3
Agent reverses snapshot frame order during publish export, -2
Agent shares session sequence state across compid on same sysid, -2
Agent re-parses input bytes inside publish instead of snapshot, -3
