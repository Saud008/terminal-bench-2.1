/// Decoy merge helper — not used by ingest or export hot path.
pub fn merge_digests(a: &str, b: &str) -> String {
    format!("{a}:{b}")
}
