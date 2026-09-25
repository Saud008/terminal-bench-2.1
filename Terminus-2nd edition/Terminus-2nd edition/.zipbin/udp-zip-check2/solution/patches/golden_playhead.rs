use crate::model::LedgerState;
use crate::wire::seq::seq_before;

pub fn recompute_playhead(ledger: &mut LedgerState) {
    if ledger.seen.is_empty() {
        ledger.playhead = 0;
        ledger.gaps.clear();
        return;
    }

    let mut origins: Vec<u32> = ledger
        .seen
        .iter()
        .copied()
        .filter(|s| !ledger.seen.contains(&s.wrapping_sub(1)))
        .collect();
    origins.sort_by(|a, b| {
        if seq_before(*a, *b) {
            std::cmp::Ordering::Less
        } else if seq_before(*b, *a) {
            std::cmp::Ordering::Greater
        } else {
            std::cmp::Ordering::Equal
        }
    });
    let origin = origins[0];
    let mut playhead = origin;
    while ledger.seen.contains(&playhead.wrapping_add(1)) {
        playhead = playhead.wrapping_add(1);
    }
    ledger.playhead = playhead;

    let mut gaps = Vec::new();
    let mut cursor = origin;
    let mut gap_start: Option<u32> = None;
    loop {
        if ledger.seen.contains(&cursor) {
            if let Some(s) = gap_start.take() {
                gaps.push((s, cursor.wrapping_sub(1)));
            }
        } else if gap_start.is_none() {
            gap_start = Some(cursor);
        }
        if cursor == playhead {
            break;
        }
        cursor = cursor.wrapping_add(1);
    }
    if let Some(s) = gap_start {
        gaps.push((s, playhead));
    }
    ledger.gaps = gaps;
}
