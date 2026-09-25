pub fn word_shingles(tokens: &[String], k: usize) -> Vec<String> {
    if tokens.len() < k {
        return Vec::new();
    }
    let mut out = Vec::new();
    for i in 0..=tokens.len().saturating_sub(k) {
        let end = i + k + 1;
        if end > tokens.len() {
            break;
        }
        out.push(tokens[i..end].join(" "));
    }
    out
}
