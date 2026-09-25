use js_value::object_get;
use serde_json::Value;
use std::collections::BTreeMap;

#[derive(Debug, Clone, Default)]
pub struct AnchorIndex {
    pub anchors: BTreeMap<String, String>,
}

pub fn build_index(doc_id: &str, root: &Value) -> AnchorIndex {
    let mut idx = AnchorIndex::default();
    walk(doc_id, root, "", &mut idx);
    idx
}

fn walk(doc_id: &str, node: &Value, pointer: &str, idx: &mut AnchorIndex) {
    if let Some(anchor) = object_get(node, "$anchor").and_then(|v| v.as_str()) {
        idx.anchors.insert(format!("#{anchor}"), format!("{doc_id}{pointer}"));
    }
    if let Some(obj) = node.as_object() {
        for (k, v) in obj {
            if k.starts_with('$') {
                continue;
            }
            let child_ptr = if pointer.is_empty() {
                format!("/{k}")
            } else {
                format!("{pointer}/{k}")
            };
            walk(doc_id, v, &child_ptr, idx);
        }
    }
    if let Some(arr) = node.as_array() {
        for (i, v) in arr.iter().enumerate() {
            let child_ptr = format!("{pointer}/{i}");
            walk(doc_id, v, &child_ptr, idx);
        }
    }
}

pub fn resolve_anchor(idx: &AnchorIndex, fragment: &str) -> Option<String> {
    let key = fragment.trim_start_matches('#');
    idx.anchors.get(key).cloned()
}
