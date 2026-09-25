use crate::rail_model::ScenarioFile;

pub fn load_track_bundle(sf: &ScenarioFile) -> usize {
    sf.blocks.len() + sf.adjacency.len()
}

pub fn load_claim_count(sf: &ScenarioFile) -> usize {
    sf.possessions.len() + sf.reservations.len() + sf.signals.len()
}
