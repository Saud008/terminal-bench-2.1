use crate::hdclp_types::{DatasetSpec, ParentAttrs};
use std::collections::BTreeMap;

/// Effective attributes after walking the parent chain.
pub fn effective_attrs(spec: &DatasetSpec) -> BTreeMap<String, serde_json::Value> {
    let mut merged = spec.attrs.clone();
    for ParentAttrs { attrs, .. } in spec.parent_chain.iter().rev() {
        for (k, v) in attrs {
            merged.insert(k.clone(), v.clone());
        }
    }
    merged
}
