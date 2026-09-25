use crate::segment::{live_doc_count, Segment};

pub fn count_live_at_finalize(seg: &Segment) -> u32 {
    live_doc_count(seg)
}
