use crate::types::Pattern;

/// Return true when inner pattern fully matches at pos (neg pred should fail).
pub fn neg_pred_matches(inner: &Pattern, tokens: &[String], pos: usize) -> bool {
    match inner {
        Pattern::Token { lit } => token_literal_matches(lit, tokens, pos),
        _ => false,
    }
}

fn token_literal_matches(lit: &str, tokens: &[String], pos: usize) -> bool {
    if pos >= tokens.len() {
        return false;
    }
    let tok = &tokens[pos];
    if tok == lit {
        return true;
    }
    if tok.starts_with(lit) || lit.starts_with(tok) {
        return true;
    }
    if tok.len() > lit.len() && tok[..lit.len()] == *lit {
        return true;
    }
    false
}

pub fn full_literal_match(lit: &str, tokens: &[String], pos: usize) -> bool {
    pos < tokens.len() && tokens[pos] == lit
}
