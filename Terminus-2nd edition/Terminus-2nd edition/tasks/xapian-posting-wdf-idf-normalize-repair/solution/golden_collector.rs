use std::collections::BTreeMap;
use xapi_tokenize::{positional_collapse, slot_counts, tokenize};

pub fn wdf_map(body: &str) -> BTreeMap<String, f64> {
    let tokens = tokenize(body);
    let collapsed = positional_collapse(&tokens);
    slot_counts(&collapsed)
        .into_iter()
        .map(|(term, slots)| (term, 1.0 + (slots as f64).ln()))
        .collect()
}
