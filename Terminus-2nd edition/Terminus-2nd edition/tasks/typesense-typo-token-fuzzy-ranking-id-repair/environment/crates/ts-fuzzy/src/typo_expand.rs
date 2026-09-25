use crate::edit_distance::levenshtein;

pub fn typo_distance_limit() -> usize {
    std::env::var("TB3_TYPO_DISTANCE")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(1)
}

pub fn expand_token(token: &str, vocabulary: &[String]) -> Vec<String> {
    if token.len() < 4 {
        return vec![token.to_string()];
    }
    let limit = typo_distance_limit();
    let mut out = vec![token.to_string()];
    for vocab in vocabulary {
        if vocab == token {
            continue;
        }
        if levenshtein(token, vocab) <= limit {
            out.push(vocab.clone());
        }
    }
    out.sort();
    out.dedup();
    out
}
