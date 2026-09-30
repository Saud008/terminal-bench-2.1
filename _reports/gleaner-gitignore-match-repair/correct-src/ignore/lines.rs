//! Splitting a pattern file into candidate lines.

const UTF8_BOM: &[u8] = b"\xef\xbb\xbf";

/// A line that may hold a pattern, with its 1-based line number in the file.
#[derive(Debug, Clone)]
pub struct RawLine {
    pub number: usize,
    pub text: Vec<u8>,
}

/// Splits file contents on `\n`, dropping blank lines and `#` comments.
/// A UTF-8 byte order mark at the start of the file is skipped and a `\r`
/// before the newline is not part of the line.
pub fn split(buf: &[u8]) -> Vec<RawLine> {
    let body = buf.strip_prefix(UTF8_BOM).unwrap_or(buf);
    let mut out = Vec::new();
    for (index, line) in body.split(|&b| b == b'\n').enumerate() {
        if line.is_empty() || line[0] == b'#' {
            continue;
        }
        let line = line.strip_suffix(b"\r").unwrap_or(line);
        out.push(RawLine { number: index + 1, text: line.to_vec() });
    }
    out
}
