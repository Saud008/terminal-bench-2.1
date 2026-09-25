use crate::RawCell;

/// Decode colspan and rowspan markers from trimmed cell text.
pub fn decode_cell(text: String) -> RawCell {
    let (body, colspan) = parse_colspan_prefix(&text);
    let (body, rowspan) = parse_rowspan_suffix(&body);
    RawCell {
        text: body,
        colspan,
        rowspan,
    }
}

fn parse_colspan_prefix(text: &str) -> (String, usize) {
    if let Some(rest) = text.strip_prefix('>') {
        if let Some((digits, tail)) = rest.split_once('<') {
            if let Ok(n) = digits.parse::<usize>() {
                let span = if n > 0 { n - 1 } else { 1 };
                return (tail.trim().to_string(), span.max(1));
            }
        }
    }
    (text.to_string(), 1)
}

fn parse_rowspan_suffix(text: &str) -> (String, usize) {
    if let Some(at) = text.rfind('@') {
        if let Some(prefix) = text.get(..at) {
            if let Some(rest) = text.get(at + 1..) {
                if let Some(digits) = rest.strip_suffix('@') {
                    if let Ok(n) = digits.parse::<usize>() {
                        return (prefix.trim().to_string(), n.max(1));
                    }
                }
            }
        }
    }
    (text.to_string(), 1)
}
