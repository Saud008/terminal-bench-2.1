use crate::export::wrap::merge_ranges_legacy;
use crate::model::LedgerState;
use crate::wire::gaps_from_mask;

pub fn record_frame(ledger: &mut LedgerState, frame_seq: u32) {
    ledger.frames_received += 1;
    if ledger.seen.contains(&frame_seq) {
        ledger.duplicate_acks += 1;
        return;
    }
    if !ledger.seen.is_empty() && frame_seq.wrapping_sub(ledger.playhead) > 1 {
        let start = ledger.playhead.wrapping_add(1);
        let end = frame_seq.wrapping_sub(1);
        ledger.gaps.push((start, end));
    }
    ledger.seen.insert(frame_seq);
}

pub fn apply_peer_ack(ledger: &mut LedgerState, ack_base: u32, loss_mask: u64) {
    let ranges = gaps_from_mask(ack_base, loss_mask);
    for r in ranges {
        ledger.peer_loss_gaps.push((r.start, r.end));
    }
    ledger.peer_loss_gaps = merge_ranges_legacy(&ledger.peer_loss_gaps)
        .into_iter()
        .map(|g| (g.start, g.end))
        .collect();
}
