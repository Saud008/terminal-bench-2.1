use crate::hdclp_types::{DatasetSpec, ParentAttrs};
use std::collections::BTreeMap;

/// Effective attributes after walking the parent chain.
pub fn effective_attrs(spec: &DatasetSpec) -> BTreeMap<String, serde_json::Value> {
    let mut merged = BTreeMap::new();
    for ParentAttrs { attrs, .. } in &spec.parent_chain {
        for (k, v) in attrs {
            merged.entry(k.clone()).or_insert_with(|| v.clone());
        }
    }
    for (k, v) in &spec.attrs {
        merged.insert(k.clone(), v.clone());
    }
    merged
}
