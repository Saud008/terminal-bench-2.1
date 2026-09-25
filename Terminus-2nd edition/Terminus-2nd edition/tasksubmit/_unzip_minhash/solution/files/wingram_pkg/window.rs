pub fn word_shingles(tokens: &[String], k: usize) -> Vec<String> {
    if tokens.len() < k {
        return Vec::new();
    }
    let mut out = Vec::new();
    for i in 0..=tokens.len() - k {
        out.push(tokens[i..i + k].join(" "));
    }
    out
}
