use xapi_tokenize::{positional_collapse, tokenize};

pub fn length_norm(body: &str) -> f64 {
    let tokens = tokenize(body);
    let _collapsed = positional_collapse(&tokens);
    let len = tokens.len().max(1) as f64;
    1.0 / len.sqrt()
}
