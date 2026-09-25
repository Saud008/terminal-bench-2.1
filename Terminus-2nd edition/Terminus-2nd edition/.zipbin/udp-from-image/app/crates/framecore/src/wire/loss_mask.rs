use crate::model::GapRange;

pub fn decode_loss_mask(bytes: [u8; 8]) -> u64 {
    u64::from_be_bytes(bytes)
}

pub fn gaps_from_mask(ack_base: u32, mask: u64) -> Vec<GapRange> {
    let mut out = Vec::new();
    let mut start: Option<u32> = None;
    for bit in 0..64 {
        let lost = (mask >> bit) & 1 == 1;
        let seq = ack_base.wrapping_sub(1 + bit as u32);
        if lost {
            if start.is_none() {
                start = Some(seq);
            }
        } else if let Some(s) = start.take() {
            let prev = ack_base.wrapping_sub(1 + bit as u32).wrapping_add(1);
            out.push(GapRange { start: s, end: prev });
        }
    }
    if let Some(s) = start {
        let end = ack_base.wrapping_sub(64);
        out.push(GapRange { start: s, end });
    }
    out
}
