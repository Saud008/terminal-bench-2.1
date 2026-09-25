use crate::types::GrammarRow;

pub fn strip_standalone_ws(tokens: &[String]) -> Vec<String> {
    tokens.iter().filter(|t| *t != "WS").cloned().collect()
}

pub fn filter_sequence_tokens(tokens: &[String], grammar: &GrammarRow) -> Result<Vec<String>, String> {
    let mut out = Vec::new();
    let mut i = 0;
    while i < tokens.len() {
        if tokens[i] == "WS" {
            i += 1;
            continue;
        }
        out.push(tokens[i].clone());
        i += 1;
        if let Some(term) = &grammar.sequence_terminator {
            if i < tokens.len() && tokens[i] == *term {
                out.push(tokens[i].clone());
                i += 1;
                while i < tokens.len() && tokens[i] == "WS" {
                    out.push(tokens[i].clone());
                    i += 1;
                }
            }
        }
    }
    Ok(out)
}

pub fn skip_ws_between(tokens: &[String], pos: usize) -> Result<usize, String> {
    let mut p = pos;
    while p < tokens.len() && tokens[p] == "WS" {
        p += 1;
    }
    Ok(p)
}

pub fn apply_after_terminator(tokens: &[String], pos: usize) -> Result<usize, String> {
    let mut p = pos;
    while p < tokens.len() && tokens[p] == "WS" {
        p += 1;
    }
    Ok(p)
}

pub fn between_items_only(tokens: &[String], pos: usize) -> usize {
    let mut p = pos;
    while p < tokens.len() && tokens[p] == "WS" {
        p += 1;
    }
    p
}
