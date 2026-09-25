use crate::model::LedgerState;
use crate::wire::seq::seq_after;

pub fn recompute_playhead(ledger: &mut LedgerState) {
    if ledger.seen.is_empty() {
        ledger.playhead = 0;
        return;
    }
    let mut candidate = *ledger.seen.iter().next().unwrap();
    for seq in &ledger.seen {
        if seq_after(*seq, candidate) {
            candidate = *seq;
        }
    }
    ledger.playhead = candidate;
}
