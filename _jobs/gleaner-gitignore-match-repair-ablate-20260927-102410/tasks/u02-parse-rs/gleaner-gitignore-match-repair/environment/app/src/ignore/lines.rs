//! Splitting a pattern file into candidate lines.

/// A line that may hold a pattern, with its 1-based line number.
#[derive(Debug, Clone)]
pub struct RawLine {
    pub number: usize,
    pub text: Vec<u8>,
}

/// Splits file contents on `\n`, dropping blank lines and `#` comments.
pub fn split(buf: &[u8]) -> Vec<RawLine> {
    let mut out = Vec::new();
    for line in buf.split(|&b| b == b'\n') {
        if line.is_empty() || line[0] == b'#' {
            continue;
        }
        out.push(RawLine { number: out.len() + 1, text: line.to_vec() });
    }
    out
}
