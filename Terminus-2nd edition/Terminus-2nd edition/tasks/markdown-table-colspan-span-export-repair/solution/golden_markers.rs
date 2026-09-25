use crate::RawCell;

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
                if n >= 1 {
                    return (tail.trim().to_string(), n);
                }
            }
        }
    }
    (text.to_string(), 1)
}

fn parse_rowspan_suffix(text: &str) -> (String, usize) {
    if !text.ends_with('@') {
        return (text.to_string(), 1);
    }
    let inner = &text[..text.len() - 1];
    if let Some(at) = inner.rfind('@') {
        let digits = &inner[at + 1..];
        if digits.chars().all(|c| c.is_ascii_digit()) {
            if let Ok(n) = digits.parse::<usize>() {
                if n >= 1 {
                    let body = inner[..at].trim();
                    return (body.to_string(), n);
                }
            }
        }
    }
    (text.to_string(), 1)
}
