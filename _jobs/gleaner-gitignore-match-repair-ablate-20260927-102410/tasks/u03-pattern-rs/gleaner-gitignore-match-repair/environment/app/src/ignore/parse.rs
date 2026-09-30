//! Turning one line of a pattern file into a pattern.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Parsed {
    /// The line as it is reported by `check`.
    pub text: Vec<u8>,
    /// What is matched: `text` without a leading `!` or a trailing `/`.
    pub body: Vec<u8>,
    pub negative: bool,
    pub dir_only: bool,
    /// The pattern is matched against the last path component at any depth.
    pub basename_only: bool,
}

/// Removes trailing whitespace.
pub fn trim_trailing_spaces(line: &[u8]) -> &[u8] {
    let end = line
        .iter()
        .rposition(|b| !b.is_ascii_whitespace())
        .map_or(0, |i| i + 1);
    &line[..end]
}

pub fn parse_line(line: &[u8]) -> Option<Parsed> {
    let text = trim_trailing_spaces(line);
    if text.is_empty() {
        return None;
    }
    let mut body = text;
    if body.len() > 1 && body[0] == b'\\' && matches!(body[1], b'!' | b'#') {
        body = &body[1..];
    }
    let negative = body[0] == b'!';
    if negative {
        body = &body[1..];
    }
    let basename_only = !body.contains(&b'/');
    let dir_only = body.last() == Some(&b'/');
    if dir_only {
        body = &body[..body.len() - 1];
    }
    Some(Parsed {
        text: text.to_vec(),
        body: body.to_vec(),
        negative,
        dir_only,
        basename_only,
    })
}
