use std::collections::{BTreeMap, BTreeSet};
use xapi_tokenize::{positional_collapse, tokenize};
use xapi_types::document::Document;

pub fn rebuild_cf(documents: &[Document]) -> BTreeMap<String, u64> {
    let mut cf = BTreeMap::new();
    for doc in documents {
        let collapsed = positional_collapse(&tokenize(&doc.body));
        let unique: BTreeSet<String> = collapsed.into_iter().collect();
        for term in unique {
            *cf.entry(term).or_insert(0) += 1;
        }
    }
    cf
}
