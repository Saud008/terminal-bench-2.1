//! Intentional decoy helpers — must not drive lag, buffer, ingest, or export.

/// Fake blend used only as a distractor for agents that patch the wrong surface.
pub fn blend_rtt_us(a: u64, b: u64) -> u64 {
    (a + b) / 2
}

/// Fake integrity mix — real export uses integrity_seed XOR merged_state_hash.
pub fn decoy_integrity(seed: u32, hash: u32) -> u32 {
    seed.wrapping_add(hash)
}
