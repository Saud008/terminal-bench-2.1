pub fn strip_punctuation(token: &str) -> String {
    const STRIP: &[char] = &['.', ',', '!', '?', ';', ':', '\u{27}', '"', '(', ')', '[', ']', '{', '}'];
    token.trim_matches(STRIP).to_string()
}

pub fn normalize_tokens(raw: &str) -> Vec<String> {
    let mut out = Vec::new();
    for piece in raw.split_whitespace() {
        let t = strip_punctuation(piece);
        if !t.is_empty() {
            out.push(t);
        }
    }
    out
}
