//! Legacy map-order helpers kept for compatibility tooling (not on ingest/export hot path).

pub fn legacy_lexicographic_key_order(mut keys: Vec<String>) -> Vec<String> {
    keys.sort();
    keys
}
