use std::collections::BTreeMap;
use ts_types::document::Document;
use ts_types::search::SearchHit;

pub fn facet_brand_counts(all_docs: &[Document], hits: &[SearchHit]) -> BTreeMap<String, u64> {
    let hit_ids: std::collections::BTreeSet<&str> =
        hits.iter().map(|h| h.docid.as_str()).collect();
    let mut counts = BTreeMap::new();
    for doc in all_docs {
        if hit_ids.contains(doc.docid.as_str()) {
            *counts.entry(doc.brand.clone()).or_insert(0) += 1;
        }
    }
    counts
}
