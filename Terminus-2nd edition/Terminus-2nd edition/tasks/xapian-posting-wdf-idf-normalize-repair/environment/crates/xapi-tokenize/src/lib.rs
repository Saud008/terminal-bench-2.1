pub fn tokenize(body: &str) -> Vec<String> {
    body.split_whitespace()
        .map(|t| t.to_ascii_lowercase())
        .collect()
}

pub fn positional_collapse(tokens: &[String]) -> Vec<String> {
    if tokens.is_empty() {
        return Vec::new();
    }
    let mut out = Vec::new();
    let mut i = 0;
    while i < tokens.len() {
        let term = tokens[i].clone();
        out.push(term);
        i += 1;
        while i < tokens.len() && tokens[i] == tokens[i - 1] {
            i += 1;
        }
    }
    out
}

pub fn slot_counts(collapsed: &[String]) -> std::collections::BTreeMap<String, u64> {
    let mut counts = std::collections::BTreeMap::new();
    for term in collapsed {
        *counts.entry(term.clone()).or_insert(0) += 1;
    }
    counts
}
