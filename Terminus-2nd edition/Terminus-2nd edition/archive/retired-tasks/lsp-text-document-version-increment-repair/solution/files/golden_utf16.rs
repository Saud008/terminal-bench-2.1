/// Map an LSP (line, UTF-16 character) position to a byte offset in UTF-8 text.
pub fn byte_offset(text: &str, line: u32, character: u32) -> usize {
    let mut current_line = 0u32;
    let mut line_start = 0usize;
    for (idx, ch) in text.char_indices() {
        if ch == '\n' {
            if current_line == line {
                break;
            }
            current_line += 1;
            line_start = idx + ch.len_utf8();
        }
    }
    if current_line < line {
        return text.len();
    }
    let line_end = text[line_start..]
        .find('\n')
        .map(|i| line_start + i)
        .unwrap_or(text.len());
    let line_str = &text[line_start..line_end];
    let mut utf16 = 0u32;
    let mut byte = line_start;
    for c in line_str.chars() {
        if utf16 == character {
            break;
        }
        utf16 += c.len_utf16() as u32;
        byte += c.len_utf8();
    }
    byte
}
