use std::path::Path;

use crate::types::ParsedCue;

pub fn parse_file(path: &Path) -> Vec<ParsedCue> {
    let raw = std::fs::read_to_string(path).expect("read srt fixture");
    let text = raw.strip_prefix('\u{feff}').unwrap_or(raw.as_str());
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

    let mut cues = Vec::new();
    let mut auto_index = 1u32;

    for block in blocks {
        if block.len() < 2 {
            continue;
        }
        let _index_line = &block[0];
        let timing_line = &block[1];
        let source_index = auto_index;
        auto_index += 1;

        let Some((start_raw, end_raw)) = timing_line.split_once("-->") else {
            continue;
        };

        let start_ms = parse_timestamp(start_raw.trim()).unwrap_or(0);
        let end_ms = parse_timestamp(end_raw.trim()).unwrap_or(0);
        let lines: Vec<String> = block[2..].to_vec();
        let has_an8 = lines.iter().any(|line| line.contains("{\\an8}"));

        cues.push(ParsedCue {
            source_index,
            start_ms,
            end_ms,
            lines,
            has_an8,
        });
    }

    cues
}

fn parse_timestamp(raw: &str) -> Option<u32> {
    let normalized = raw.trim().replace(',', ".");
    let (hms, ms_part) = normalized.split_once('.')?;
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
