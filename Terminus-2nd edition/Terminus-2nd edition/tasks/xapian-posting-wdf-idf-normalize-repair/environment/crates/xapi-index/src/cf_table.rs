use std::collections::BTreeMap;
use xapi_tokenize::{positional_collapse, tokenize};
use xapi_types::document::Document;

pub fn rebuild_cf(documents: &[Document]) -> BTreeMap<String, u64> {
    let mut cf = BTreeMap::new();
    for doc in documents {
        let tokens = tokenize(&doc.body);
        let _collapsed = positional_collapse(&tokens);
        for term in tokens {
            *cf.entry(term).or_insert(0) += 1;
        }
    }
    cf
}
