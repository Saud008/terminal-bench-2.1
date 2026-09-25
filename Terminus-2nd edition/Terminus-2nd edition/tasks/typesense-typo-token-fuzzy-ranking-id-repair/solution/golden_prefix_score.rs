pub fn prefix_match_score(query_token: &str, index_token: &str) -> f64 {
    if !index_token.starts_with(query_token) {
        return 0.0;
    }
    if query_token == index_token {
        return 1.0;
    }
    let q_len = query_token.len().max(1) as f64;
    let t_len = index_token.len().max(1) as f64;
    0.5 + 0.5 * (q_len / t_len)
}
