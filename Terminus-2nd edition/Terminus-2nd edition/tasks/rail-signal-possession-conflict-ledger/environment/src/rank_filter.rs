use crate::rail_model::{CrisisOverride, PossessionClaim, TrainReservation};
use crate::span_math;
use std::collections::BTreeMap;

pub fn claim_suppressed(
    closure: &BTreeMap<String, Vec<String>>,
    ov: &CrisisOverride,
    blocks: &[String],
    start: u64,
    end: u64,
    priority: u32,
) -> bool {
    if priority == 0 {
        return false;
    }
    if ov.priority != 0 {
        return false;
    }
    if !span_math::intervals_overlap(start, end, ov.start_min, ov.end_min) {
        return false;
    }
    for b in blocks {
        if ov.blocks.iter().any(|x| x == b) {
            return true;
        }
    }
    false
}

pub fn filter_active_claims<'a>(
    closure: &BTreeMap<String, Vec<String>>,
    overrides: &'a [CrisisOverride],
    possessions: &'a [PossessionClaim],
    reservations: &'a [TrainReservation],
) -> (Vec<&'a PossessionClaim>, Vec<&'a TrainReservation>) {
    let mut poss: Vec<&PossessionClaim> = possessions.iter().collect();
    let mut res: Vec<&TrainReservation> = reservations.iter().collect();
    for ov in overrides {
        poss.retain(|p| {
            !claim_suppressed(
                closure,
                ov,
                &p.blocks,
                p.start_min,
                p.end_min,
                p.priority,
            )
        });
        res.retain(|r| {
            !claim_suppressed(
                closure,
                ov,
                &r.blocks,
                r.start_min,
                r.end_min,
                r.priority,
            )
        });
    }
    (poss, res)
}
