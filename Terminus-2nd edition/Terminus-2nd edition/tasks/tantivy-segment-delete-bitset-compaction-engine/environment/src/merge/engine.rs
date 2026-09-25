use crate::types::SegmentRow;

pub fn remap_local_doc(local: u32, max_doc: u32, seed: u32) -> u32 {
    if seed == 0 {
        return local;
    }
    (local + seed) % max_doc.max(1)
}

pub fn segment_doc_offset(segments: &[SegmentRow], index: usize) -> u32 {
    segments.iter().take(index).map(|s| s.max_doc).sum()
}
