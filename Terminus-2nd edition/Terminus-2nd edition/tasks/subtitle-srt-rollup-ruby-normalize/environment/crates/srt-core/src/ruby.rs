use serde::{Deserialize, Serialize};

use crate::types::{RUBY_SHIFT_MS, RubySegment};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RubyCue {
    pub source_index: u32,
    pub start_ms: u32,
    pub end_ms: u32,
    pub text: String,
    pub ruby_segments: Vec<RubySegment>,
    pub rolled_up: bool,
}

pub fn apply_ruby_shifts(cues: Vec<crate::types::ParsedCue>) -> (Vec<RubyCue>, u32) {
    let mut out = Vec::new();
    let mut shifts = 0u32;

    for cue in cues {
        let raw_text = cue.lines.join("\n");
        let (display_text, mut segments) = extract_ruby(&raw_text, cue.start_ms, cue.end_ms);

        if cue.has_an8 {
            for segment in &mut segments {
                let shrunk = segment.end_ms.saturating_sub(RUBY_SHIFT_MS);
                if shrunk < segment.end_ms {
                    shifts += 1;
                }
                segment.end_ms = shrunk.max(cue.start_ms);
            }
        }

        out.push(RubyCue {
            source_index: cue.source_index,
            start_ms: cue.start_ms,
            end_ms: cue.end_ms,
            text: display_text,
            ruby_segments: segments,
            rolled_up: false,
        });
    }

    (out, shifts)
}

fn extract_ruby(raw: &str, start_ms: u32, _end_ms: u32) -> (String, Vec<RubySegment>) {
    let mut display = String::new();
    let mut ruby_base = String::new();
    let mut segments = Vec::new();
    let mut pos = 0usize;

    while pos < raw.len() {
        if raw[pos..].starts_with("{\\an8}") {
            pos += "{\\an8}".len();
            continue;
        }
        if raw[pos..].starts_with("{rt}") {
            let base = ruby_base.clone();
            ruby_base.clear();
            pos += "{rt}".len();
            let read_start = pos;
            while pos < raw.len()
                && !raw[pos..].starts_with("{rt}")
                && !raw[pos..].starts_with("{\\an8}")
            {
                pos += raw[pos..].chars().next().map(char::len_utf8).unwrap_or(1);
            }
            let reading = raw[read_start..pos].to_string();
            segments.push(RubySegment {
                base,
                reading,
                start_ms,
                end_ms: start_ms,
            });
            continue;
        }
        let ch = raw[pos..].chars().next().expect("char boundary");
        display.push(ch);
        ruby_base.push(ch);
        pos += ch.len_utf8();
    }

    (display.trim().to_string(), segments)
}
