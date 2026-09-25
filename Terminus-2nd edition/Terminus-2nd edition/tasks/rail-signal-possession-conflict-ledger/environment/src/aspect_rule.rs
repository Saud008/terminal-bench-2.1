use crate::rail_model::{ScenarioFile, SignalRestriction, TrainReservation};
use std::collections::BTreeMap;

pub fn signal_blocks_reservation(
    closure: &BTreeMap<String, Vec<String>>,
    sig: &SignalRestriction,
    res: &TrainReservation,
) -> bool {
    if sig.aspect != "restrict" {
        return false;
    }
    if !res.blocks.iter().any(|b| b == &sig.block_id) {
        return false;
    }
    true
}

pub fn collect_signal_conflicts(
    sf: &ScenarioFile,
    closure: &BTreeMap<String, Vec<String>>,
) -> Vec<(String, String, u64, u64, Vec<String>)> {
    let mut out = Vec::new();
    for sig in &sf.signals {
        if sig.aspect != "restrict" {
            continue;
        }
        for res in &sf.reservations {
            if signal_blocks_reservation(closure, sig, res) {
                let blocks = vec![sig.block_id.clone(), res.train_id.clone()];
                out.push((
                    sig.signal_id.clone(),
                    res.train_id.clone(),
                    sig.start_min.max(res.start_min),
                    sig.end_min.min(res.end_min),
                    blocks,
                ));
            }
        }
    }
    out
}
