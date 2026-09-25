use std::collections::BTreeMap;

pub fn remap_postings(postings: &BTreeMap<String, Vec<u32>>, offset: u32) -> BTreeMap<String, Vec<u32>> {
    let mut merged = postings.clone();
    for ids in merged.values_mut() {
        for id in ids.iter_mut() {
            *id += offset;
        }
        ids.sort_unstable();
        ids.dedup();
    }
    merged
}

pub fn merge_posting_maps(
    base: &BTreeMap<String, Vec<u32>>,
    other: &BTreeMap<String, Vec<u32>>,
) -> BTreeMap<String, Vec<u32>> {
    let mut out = base.clone();
    for (term, ids) in other {
        out.entry(term.clone()).or_default().extend(ids.clone());
        if let Some(list) = out.get_mut(term) {
            list.sort_unstable();
            list.dedup();
        }
    }
    out
}
