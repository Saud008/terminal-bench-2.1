use crate::types::SegmentRow;

pub fn live_max_doc(segments: &[SegmentRow]) -> u32 {
    segments.iter().map(|s| s.max_doc).max().unwrap_or(0)
}
