#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QueryMode {
    And,
    Or,
}

#[derive(Debug, Clone)]
pub struct ParsedQuery {
    pub mode: QueryMode,
    pub terms: Vec<String>,
}

pub fn parse_query(raw: &str) -> Result<ParsedQuery, String> {
    let upper = raw.to_ascii_uppercase();
    let mode = if upper.contains(" OR ") {
        QueryMode::Or
    } else if upper.contains(" AND ") {
        QueryMode::And
    } else {
        return Err("query needs AND or OR".into());
    };
    let splitter = if matches!(mode, QueryMode::Or) { " OR " } else { " AND " };
    let terms: Vec<String> = raw
        .split(splitter)
        .map(|t| t.trim().to_ascii_lowercase())
        .filter(|t| !t.is_empty())
        .collect();
    if terms.is_empty() {
        return Err("no terms".into());
    }
    Ok(ParsedQuery { mode, terms })
}
