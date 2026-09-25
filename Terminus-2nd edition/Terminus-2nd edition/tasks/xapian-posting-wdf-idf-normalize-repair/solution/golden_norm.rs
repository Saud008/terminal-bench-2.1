use std::collections::BTreeSet;
use xapi_tokenize::{positional_collapse, tokenize};

pub fn length_norm(body: &str) -> f64 {
    let collapsed = positional_collapse(&tokenize(body));
    let unique: BTreeSet<String> = collapsed.into_iter().collect();
    let len = unique.len().max(1) as f64;
    1.0 / len.sqrt()
}
