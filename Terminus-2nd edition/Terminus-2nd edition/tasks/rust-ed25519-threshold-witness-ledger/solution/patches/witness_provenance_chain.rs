use std::collections::HashMap;

use crate::types::WitnessRow;

pub fn chain_valid(all: &[WitnessRow], witness: &WitnessRow) -> bool {
    let index: HashMap<&str, &WitnessRow> = all.iter().map(|w| (w.witness_id.as_str(), w)).collect();
    match witness.prior_witness_id.as_deref() {
        None | Some("none") => true,
        Some(prior) => {
            let Some(p) = index.get(prior) else {
                return false;
            };
            p.epoch < witness.epoch
        }
    }
}

pub fn all_provenance_ok(all: &[WitnessRow], outcomes: &[crate::types::WitnessOutcome]) -> bool {
    outcomes.iter().all(|o| o.provenance_ok)
        && all.iter().all(|w| chain_valid(all, w))
}
