use crate::types::GrammarRow;

pub fn strip_standalone_ws(tokens: &[String]) -> Vec<String> {
    tokens.iter().filter(|t| *t != "WS").cloned().collect()
}

pub fn filter_sequence_tokens(tokens: &[String], _grammar: &GrammarRow) -> Result<Vec<String>, String> {
    Ok(tokens.to_vec())
}

pub fn skip_ws_between(tokens: &[String], pos: usize) -> Result<usize, String> {
    let mut p = pos;
    while p < tokens.len() && tokens[p] == "WS" {
        p += 1;
    }
    Ok(p)
}

pub fn apply_after_terminator(tokens: &[String], pos: usize) -> Result<usize, String> {
    Ok(pos)
}

pub fn between_items_only(tokens: &[String], pos: usize) -> usize {
    let mut p = pos;
    while p < tokens.len() && tokens[p] == "WS" {
        p += 1;
    }
    p
}
