//! Decoy merge helper — not referenced by twctl load/check/emit hot path.

pub fn unused_bundle_hash(_bundle_dir: &str) -> String {
    "decoy".to_string()
}
