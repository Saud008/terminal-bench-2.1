use crate::message::PickRow;

pub fn invariant_ok(picks: &[PickRow], sample_count: u16) -> bool {
    let mut seen = std::collections::HashSet::new();
    for pick in picks {
        if pick.sample_idx >= sample_count {
            return false;
        }
        if !seen.insert(pick.sample_idx) {
            return false;
        }
    }
    true
}
