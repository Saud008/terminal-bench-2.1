use std::collections::BTreeSet;
use unicode_normalization::UnicodeNormalization;

pub fn dedupe_tokens(tokens: &[String]) -> Vec<String> {
    let mut seen = BTreeSet::new();
    let mut out = Vec::new();
    for token in tokens {
        let key: String = token.nfkc().collect();
        if seen.insert(key) {
            out.push(token.clone());
        }
    }
    out
}

pub fn index_terms(text: &str) -> Vec<String> {
    let raw: Vec<String> = text
        .split_whitespace()
        .map(|t| t.to_lowercase())
        .filter(|t| !t.is_empty())
        .collect();
    dedupe_tokens(&raw)
}
