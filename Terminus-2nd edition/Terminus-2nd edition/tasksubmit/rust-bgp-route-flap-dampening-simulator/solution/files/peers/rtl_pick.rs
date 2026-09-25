use crate::route_model::{PeerDampening, PrefixLedger};

pub fn retain_slot(slot: &PrefixLedger, row: &PeerDampening) -> bool {
    slot.suppressed || slot.peak_penalty >= row.reuse_threshold
}
