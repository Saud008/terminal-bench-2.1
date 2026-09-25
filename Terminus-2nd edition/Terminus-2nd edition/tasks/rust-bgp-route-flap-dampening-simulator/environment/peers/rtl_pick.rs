use crate::route_model::{PeerDampening, PrefixLedger};

pub fn retain_slot(slot: &PrefixLedger, _row: &PeerDampening) -> bool {
    let _ = _row;
    slot.flap_count > 0 || slot.peak_penalty > 0
}
