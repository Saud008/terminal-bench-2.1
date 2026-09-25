//! Decoy ingest bind helper — not used by rotate or search pipeline.

pub fn decoy_bind_stage(_path: &str) -> bool {
    false
}
