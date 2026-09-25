//! Decoy bloom filter helpers — not used on wal ingest or compact export hot path.

pub fn bloom_hash(key: &str) -> u64 {
    key.bytes().fold(0u64, |acc, b| acc.wrapping_mul(131).wrapping_add(b as u64))
}
