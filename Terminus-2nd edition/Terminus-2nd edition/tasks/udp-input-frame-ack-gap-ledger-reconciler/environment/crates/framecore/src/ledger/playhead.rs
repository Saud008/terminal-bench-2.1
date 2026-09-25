use crate::model::LedgerState;

pub fn recompute_playhead(ledger: &mut LedgerState) {
    if ledger.seen.is_empty() {
        ledger.playhead = 0;
        ledger.gaps.clear();
        return;
    }

    let origin = *ledger.seen.iter().min().unwrap();
    let mut playhead = origin;
    while ledger.seen.contains(&playhead.wrapping_add(1)) {
        playhead = playhead.wrapping_add(1);
    }
    ledger.playhead = playhead;
}
