use ts_fuzzy::prefix_score::prefix_match_score;

pub fn token_match_weight(query_token: &str, index_token: &str, typo: bool) -> f64 {
    if query_token == index_token {
        return 1.0;
    }
    if typo {
        return 0.85;
    }
    prefix_match_score(query_token, index_token)
}
