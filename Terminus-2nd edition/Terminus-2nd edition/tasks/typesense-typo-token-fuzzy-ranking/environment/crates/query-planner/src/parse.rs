pub fn parse_query(raw: &str) -> Result<Vec<String>, String> {
    let tokens: Vec<String> = raw
        .split_whitespace()
        .map(|t| t.to_lowercase())
        .filter(|t| !t.is_empty())
        .collect();
    if tokens.is_empty() {
        return Err("empty query".into());
    }
    Ok(tokens)
}
