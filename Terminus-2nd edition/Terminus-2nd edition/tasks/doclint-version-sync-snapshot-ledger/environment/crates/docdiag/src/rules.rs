use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiagnosticCounts {
    pub todo_count: u32,
    pub paren_delta: i32,
    pub wide_char_lines: u32,
    pub total: u32,
}

pub fn compute_diagnostics(text: &str) -> DiagnosticCounts {
    let todo_count = count_todos(text);
    let paren_delta = paren_balance(text);
    let wide_char_lines = count_wide_lines(text);
    let total = todo_count + paren_delta.unsigned_abs() + wide_char_lines;
    DiagnosticCounts {
        todo_count,
        paren_delta,
        wide_char_lines,
        total,
    }
}

fn count_todos(text: &str) -> u32 {
    let mut count = 0u32;
    let bytes = text.as_bytes();
    let mut i = 0usize;
    while i + 4 <= bytes.len() {
        if &bytes[i..i + 4] == b"TODO" {
            let before_ok = i == 0 || !bytes[i - 1].is_ascii_alphanumeric();
            let after = i + 4;
            let after_ok = after >= bytes.len() || !bytes[after].is_ascii_alphanumeric();
            if before_ok && after_ok {
                count += 1;
            }
        }
        i += 1;
    }
    count
}

fn paren_balance(text: &str) -> i32 {
    let open = text.chars().filter(|c| *c == '(').count() as i32;
    let close = text.chars().filter(|c| *c == ')').count() as i32;
    open - close
}

fn count_wide_lines(text: &str) -> u32 {
    text.lines()
        .filter(|line| line.chars().any(|c| c.len_utf16() > 1))
        .count() as u32
}
