use crate::types::ParsedCue;

pub fn resolve_overlaps(mut cues: Vec<ParsedCue>) -> (Vec<ParsedCue>, u32) {
    cues.sort_by(|a, b| {
        a.start_ms
            .cmp(&b.start_ms)
            .then_with(|| a.source_index.cmp(&b.source_index))
    });

    let mut trims = 0u32;
    for idx in 0..cues.len().saturating_sub(1) {
        let next_start = cues[idx + 1].start_ms;
        if cues[idx].end_ms > next_start {
            cues[idx].end_ms = next_start;
            trims += 1;
        }
    }

    (cues, trims)
}
