use crate::types::{ContentChange, Position, Range, StagedEdit};
use crate::utf16::byte_offset;

pub fn apply_edits(base: &str, edits: &[StagedEdit]) -> String {
    let mut ordered: Vec<&StagedEdit> = edits.iter().collect();
    ordered.sort_by(|a, b| {
        b.range
            .start
            .line
            .cmp(&a.range.start.line)
            .then(b.range.start.character.cmp(&a.range.start.character))
    });

    let mut out = base.to_string();
    for edit in ordered {
        let start = byte_offset(&out, edit.range.start.line, edit.range.start.character);
        let end = byte_offset(&out, edit.range.end.line, edit.range.end.character);
        if start <= end && end <= out.len() {
            out.replace_range(start..end, &edit.text);
        }
    }
    out
}

pub fn changes_to_edits(changes: &[ContentChange], full_text: &str) -> Vec<StagedEdit> {
    changes
        .iter()
        .map(|c| {
            let range = c.range.clone().unwrap_or_else(|| full_range(full_text));
            StagedEdit {
                range,
                text: c.text.clone(),
            }
        })
        .collect()
}

fn full_range(text: &str) -> Range {
    let line = text.matches('\n').count() as u32;
    let last_line = text.split('\n').last().unwrap_or("");
    let character = last_line.chars().map(|c| c.len_utf16()).sum::<usize>() as u32;
    Range {
        start: Position { line: 0, character: 0 },
        end: Position { line, character },
    }
}
