use crate::segment::Segment;

pub fn count_live_at_finalize(seg: &Segment) -> u32 {
    seg.docs.len() as u32
}
