//! Archived single-pass rebuild path retained for regression comparison. Stage-2 publish reads staged snapshot cues instead.

use std::path::Path;

use crate::ruby::RubyCue;
use crate::types::{RUBY_SHIFT_MS, RubySegment, seed_offset_ms};

pub fn build_ruby_cues(path: &Path, seed: &str) -> Vec<RubyCue> {
    let text = std::fs::read_to_string(path).expect("read srt fixture");
    let mut blocks = Vec::new();
    let mut current = Vec::new();
    for line in text.split('\n') {
        let trimmed = line.trim_end_matches('\r').trim();
        if trimmed.is_empty() {
            if !current.is_empty() {
                blocks.push(current);
                current = Vec::new();
            }
            continue;
        }
        current.push(trimmed.to_string());
    }
    if !current.is_empty() {
        blocks.push(current);
    }

    let offset = seed_offset_ms(seed);
    let mut cues = Vec::new();
    let mut auto_index = 1u32;
    for block in blocks {
        if block.len() < 2 {
            continue;
        }
        let timing_line = &block[1];
        let Some((start_raw, end_raw)) = timing_line.split_once("-->") else {
            continue;
        };
        let start_ms = legacy_parse_timestamp(start_raw.trim()).unwrap_or(0) + offset;
        let end_ms = legacy_parse_timestamp(end_raw.trim()).unwrap_or(0) + offset;
        let lines: Vec<String> = block[2..].to_vec();
        let has_an8 = lines.iter().any(|line| line.contains("{\\an8}"));
        let raw_text = lines.join("\n");
        let (display_text, mut segments) = legacy_extract_ruby(&raw_text, start_ms);
        if has_an8 {
            for segment in &mut segments {
                segment.end_ms = segment
                    .end_ms
                    .saturating_sub(RUBY_SHIFT_MS)
                    .max(start_ms);
            }
        }
        cues.push(RubyCue {
            source_index: auto_index,
            start_ms,
            end_ms,
            text: display_text,
            ruby_segments: segments,
            rolled_up: false,
        });
        auto_index += 1;
    }

    cues.sort_by(|a, b| {
        a.start_ms
            .cmp(&b.start_ms)
            .then_with(|| a.source_index.cmp(&b.source_index))
    });
    for idx in 0..cues.len().saturating_sub(1) {
        let next_start = cues[idx + 1].start_ms;
        if cues[idx].end_ms > next_start {
            cues[idx].end_ms = cues[idx].end_ms.max(next_start);
        }
    }

    cues
}

fn legacy_parse_timestamp(raw: &str) -> Option<u32> {
    let (hms, ms_part) = raw.trim().split_once('.')?;
    let parts: Vec<&str> = hms.split(':').collect();
    if parts.len() != 3 {
        return None;
    }
    let hours: u32 = parts[0].parse().ok()?;
    let minutes: u32 = parts[1].parse().ok()?;
    let seconds: u32 = parts[2].parse().ok()?;
    let millis: u32 = ms_part.parse().ok()?;
    Some(hours * 3_600_000 + minutes * 60_000 + seconds * 1_000 + millis)
}

fn legacy_extract_ruby(raw: &str, start_ms: u32) -> (String, Vec<RubySegment>) {
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
