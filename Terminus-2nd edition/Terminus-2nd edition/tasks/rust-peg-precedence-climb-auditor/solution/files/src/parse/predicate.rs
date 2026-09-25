use crate::types::Pattern;

pub fn neg_pred_matches(inner: &Pattern, tokens: &[String], pos: usize) -> bool {
    match inner {
        Pattern::Token { lit } => full_literal_match(lit, tokens, pos),
        _ => false,
    }
}

pub fn full_literal_match(lit: &str, tokens: &[String], pos: usize) -> bool {
    pos < tokens.len() && tokens[pos] == lit
}
