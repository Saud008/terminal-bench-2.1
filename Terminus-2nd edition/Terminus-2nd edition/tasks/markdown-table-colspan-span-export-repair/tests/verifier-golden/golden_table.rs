use crate::parse::cells::split_row;
use crate::span::markers::decode_cell;
use crate::RawCell;

pub fn is_alignment_row(cells: &[String]) -> bool {
    !cells.is_empty()
        && cells.iter().all(|part| {
            let s = part.trim();
            !s.is_empty()
                && s.chars().all(|c| c == '-' || c == ':' || c == '|')
                && s.contains('-')
        })
}

pub fn parse_table_block(content: &str) -> Option<Vec<Vec<RawCell>>> {
    let mut lines: Vec<String> = Vec::new();
    let mut in_block = false;
    for line in content.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with('|') {
            in_block = true;
            lines.push(trimmed.to_string());
        } else if in_block {
            break;
        }
    }
    if lines.is_empty() {
        return None;
    }

    let mut parts_rows: Vec<Vec<String>> = lines.iter().map(|l| split_row(l)).collect();
    if parts_rows.len() >= 2 && is_alignment_row(&parts_rows[1]) {
        parts_rows.remove(1);
    }

    Some(
        parts_rows
            .into_iter()
            .map(|parts| parts.into_iter().map(decode_cell).collect())
            .collect(),
    )
}
