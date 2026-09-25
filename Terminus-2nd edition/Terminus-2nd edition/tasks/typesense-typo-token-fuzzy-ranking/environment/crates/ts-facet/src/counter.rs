use std::collections::BTreeMap;
use ts_types::document::Document;

pub fn facet_brand_counts(all_docs: &[Document], _filtered: &[Document]) -> BTreeMap<String, u64> {
    let mut counts = BTreeMap::new();
    for doc in all_docs {
        *counts.entry(doc.brand.clone()).or_insert(0) += 1;
    }
    counts
}
