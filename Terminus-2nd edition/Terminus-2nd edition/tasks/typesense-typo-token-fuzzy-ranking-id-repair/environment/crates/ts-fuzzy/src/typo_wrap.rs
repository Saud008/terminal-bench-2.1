use crate::edit_distance::levenshtein;

pub fn wrapped_typo_score(query: &str, candidate: &str) -> f64 {
    let dist = levenshtein(query, candidate) as f64;
    1.0 / (1.0 + dist)
}
