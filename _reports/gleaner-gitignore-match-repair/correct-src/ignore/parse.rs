//! Turning one line of a pattern file into a pattern.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Parsed {
    /// The line as it is reported by `check`: trailing spaces removed,
    /// everything else as written.
    pub text: Vec<u8>,
    /// What is matched: `text` without a leading `!` or a trailing `/`.
    pub body: Vec<u8>,
    pub negative: bool,
    pub dir_only: bool,
    /// No `/` left in `body`: the pattern is matched against the last path
    /// component at any depth.
    pub basename_only: bool,
}

/// Removes unescaped trailing spaces. Only the space character counts, and
/// a space preceded by a backslash is kept.
pub fn trim_trailing_spaces(line: &[u8]) -> &[u8] {
    let mut last_space: Option<usize> = None;
    let mut i = 0;
    while i < line.len() {
        match line[i] {
            b' ' => {
                if last_space.is_none() {
                    last_space = Some(i);
                }
            }
            b'\\' => {
                i += 1;
                if i >= line.len() {
                    return line;
                }
                last_space = None;
            }
            _ => last_space = None,
        }
        i += 1;
    }
    match last_space {
        Some(at) => &line[..at],
        None => line,
    }
}

pub fn parse_line(line: &[u8]) -> Option<Parsed> {
    let text = trim_trailing_spaces(line);
    if text.is_empty() {
        return None;
    }
    let mut body = text;
    let negative = body[0] == b'!';
    if negative {
        body = &body[1..];
    }
    let dir_only = body.last() == Some(&b'/');
    if dir_only {
        body = &body[..body.len() - 1];
    }
    let basename_only = !body.contains(&b'/');
    Some(Parsed {
        text: text.to_vec(),
        body: body.to_vec(),
        negative,
        dir_only,
        basename_only,
    })
}
