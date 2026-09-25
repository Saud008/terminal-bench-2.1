use crate::model::LedgerState;
use crate::wire::gaps_from_mask;
use crate::wire::seq::seq_after;

pub fn record_frame(ledger: &mut LedgerState, frame_seq: u32) {
    ledger.frames_received += 1;
    if ledger.seen.contains(&frame_seq) {
        ledger.duplicate_acks += 1;
        ledger.gaps.push((frame_seq, frame_seq));
        return;
    }
    ledger.seen.insert(frame_seq);
    if ledger.playhead == 0 {
        ledger.playhead = frame_seq;
        return;
    }
    if seq_after(frame_seq, ledger.playhead) && frame_seq != ledger.playhead.wrapping_add(1) {
        ledger
            .gaps
            .push((ledger.playhead.wrapping_add(1), frame_seq.wrapping_sub(1)));
    }
}

pub fn apply_peer_ack(ledger: &mut LedgerState, ack_base: u32, loss_mask: u64) {
    let ranges = gaps_from_mask(ack_base, loss_mask);
    for r in ranges {
        ledger.peer_loss_gaps.push((r.start, r.end));
    }
}
