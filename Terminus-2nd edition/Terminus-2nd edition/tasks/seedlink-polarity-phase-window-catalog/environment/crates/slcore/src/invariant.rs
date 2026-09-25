use crate::message::PickRow;

pub fn invariant_ok(picks: &[PickRow], sample_count: u16) -> bool {
    picks.iter().all(|pick| pick.sample_idx < sample_count)
}
