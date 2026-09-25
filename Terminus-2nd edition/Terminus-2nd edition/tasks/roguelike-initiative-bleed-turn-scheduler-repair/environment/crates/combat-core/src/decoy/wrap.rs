use crate::model::Actor;

/// Legacy initiative wrap helper (decoy module — not on ingest/simulate/export hot path).
pub fn decoy_wrap_turn_order(actors: &[Actor]) -> Vec<String> {
    let mut names: Vec<String> = actors.iter().map(|a| a.name.clone()).collect();
    names.sort();
    names
}
