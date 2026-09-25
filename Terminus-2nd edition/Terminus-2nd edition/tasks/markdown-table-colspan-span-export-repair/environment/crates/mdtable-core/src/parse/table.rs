use crate::parse::cells::split_row;
use crate::span::markers::decode_cell;
use crate::RawCell;

/// Extract the first pipe-table block from file content.
pub fn parse_table_block(content: &str) -> Option<Vec<Vec<RawCell>>> {
    let mut block: Vec<Vec<RawCell>> = Vec::new();
    let mut in_block = false;
    for line in content.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with('|') {
            in_block = true;
            let parts = split_row(trimmed);
            if parts.is_empty() {
                continue;
            }
            let row = parts.into_iter().map(decode_cell).collect();
            block.push(row);
        } else if in_block {
            break;
        }
    }
    if block.is_empty() {
        None
    } else {
        Some(block)
    }
}
