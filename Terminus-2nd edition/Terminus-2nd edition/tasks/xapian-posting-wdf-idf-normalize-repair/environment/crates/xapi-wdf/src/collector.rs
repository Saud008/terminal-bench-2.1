use std::collections::BTreeMap;
use xapi_tokenize::{positional_collapse, tokenize};

pub fn wdf_map(body: &str) -> BTreeMap<String, f64> {
    let tokens = tokenize(body);
    let mut counts = BTreeMap::new();
    for term in &tokens {
        *counts.entry(term.clone()).or_insert(0) += 1;
    }
    let _collapsed = positional_collapse(&tokens);
    counts
        .into_iter()
        .map(|(term, raw)| (term, 1.0 + (raw as f64).ln()))
        .collect()
}
