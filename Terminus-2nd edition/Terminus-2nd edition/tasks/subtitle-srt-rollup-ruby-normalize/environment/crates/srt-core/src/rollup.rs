use crate::ruby::RubyCue;
use crate::types::ROLLUP_GAP_MS;

pub fn apply_rollup(cues: Vec<RubyCue>) -> (Vec<RubyCue>, u32) {
    let mut out: Vec<RubyCue> = Vec::new();
    let mut removals = 0u32;

    for cue in cues {
        if let Some(prev) = out.last_mut() {
            let gap = cue.start_ms.saturating_sub(prev.end_ms);
            if gap <= ROLLUP_GAP_MS && !ends_sentence(&prev.text) {
                prev.text = format!("{}\n{}", prev.text, cue.text);
                prev.end_ms = cue.end_ms;
                removals += 1;
                continue;
            }
        }
        out.push(cue);
    }

    (out, removals)
}

fn ends_sentence(text: &str) -> bool {
    text.trim_end()
        .chars()
        .last()
        .map(|ch| matches!(ch, '.' | '!' | '?'))
        .unwrap_or(false)
}
