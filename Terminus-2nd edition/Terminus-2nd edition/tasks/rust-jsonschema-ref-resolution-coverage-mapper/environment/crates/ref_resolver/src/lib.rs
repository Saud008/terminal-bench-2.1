use anchor_index::{build_index, resolve_anchor, AnchorIndex};
use doc_loader::SchemaDoc;
use pointer_walk::resolve_pointer;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use visit_guard::VisitGuard;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RefEdge {
    pub schema_id: String,
    pub ref_pointer: String,
    pub target_id: String,
    pub status: String,
    pub anchor_name: Option<String>,
}

pub fn resolve_all(docs: &[SchemaDoc], _schema_root: &std::path::Path) -> Vec<RefEdge> {
    let mut by_id = BTreeMap::new();
    let mut anchor_maps: BTreeMap<String, AnchorIndex> = BTreeMap::new();
    for d in docs {
        by_id.insert(d.id.clone(), d.clone());
        anchor_maps.insert(d.id.clone(), build_index(&d.id, &d.root));
    }
    let mut edges = Vec::new();
    let mut guard = VisitGuard::new();
    for d in docs {
        collect_refs(
            &d.id,
            &d.root,
            "",
            &d.root,
            &by_id,
            &anchor_maps,
            &mut guard,
            &mut edges,
        );
    }
    edges.sort_by(|a, b| {
        (a.schema_id.as_str(), a.ref_pointer.as_str()).cmp(&(b.schema_id.as_str(), b.ref_pointer.as_str()))
    });
    edges
}

fn collect_refs(
    doc_id: &str,
    node: &serde_json::Value,
    pointer: &str,
    root: &serde_json::Value,
    by_id: &BTreeMap<String, SchemaDoc>,
    anchors: &BTreeMap<String, AnchorIndex>,
    guard: &mut VisitGuard,
    out: &mut Vec<RefEdge>,
) {
    if let Some(r) = node.get("$ref").and_then(|v| v.as_str()) {
        let edge = resolve_one(doc_id, pointer, r, root, by_id, anchors, guard);
        out.push(edge);
    }
    if let Some(obj) = node.as_object() {
        for (k, v) in obj {
            if k.starts_with('$') {
                continue;
            }
            let child = if pointer.is_empty() {
                format!("/{k}")
            } else {
                format!("{pointer}/{k}")
            };
            collect_refs(doc_id, v, &child, root, by_id, anchors, guard, out);
        }
    }
    if let Some(arr) = node.as_array() {
        for (i, v) in arr.iter().enumerate() {
            let child = format!("{pointer}/{i}");
            collect_refs(doc_id, v, &child, root, by_id, anchors, guard, out);
        }
    }
}

fn resolve_one(
    doc_id: &str,
    pointer: &str,
    raw_ref: &str,
    root: &serde_json::Value,
    by_id: &BTreeMap<String, SchemaDoc>,
    anchors: &BTreeMap<String, AnchorIndex>,
    guard: &mut VisitGuard,
) -> RefEdge {
    let ref_pointer = if pointer.is_empty() {
        "$ref".into()
    } else {
        format!("{pointer}/$ref")
    };
    if raw_ref.starts_with("http://") || raw_ref.starts_with("https://") {
        return RefEdge {
            schema_id: doc_id.to_string(),
            ref_pointer,
            target_id: raw_ref.to_string(),
            status: "unresolved".into(),
            anchor_name: None,
        };
    }
    if raw_ref.starts_with('#') {
        let anchor_key = raw_ref.trim_start_matches('#');
        if !raw_ref.starts_with("#/") {
            if let Some(anchor_target) = anchors.get(doc_id).and_then(|idx| resolve_anchor(idx, raw_ref)) {
                return RefEdge {
                    schema_id: doc_id.to_string(),
                    ref_pointer,
                    target_id: anchor_target,
                    status: "resolved".into(),
                    anchor_name: Some(anchor_key.to_string()),
                };
            }
        }
        let visit_key = (doc_id.to_string(), ref_pointer.clone());
        if !guard.enter(doc_id, &ref_pointer) {
            return RefEdge {
                schema_id: doc_id.to_string(),
                ref_pointer,
                target_id: format!("{doc_id}{raw_ref}"),
                status: "recursive".into(),
                anchor_name: None,
            };
        }
        let target = resolve_pointer(root, raw_ref).map(|_| format!("{doc_id}{raw_ref}"));
        guard.leave(doc_id, &ref_pointer);
        return RefEdge {
            schema_id: doc_id.to_string(),
            ref_pointer,
            target_id: target.clone().unwrap_or_else(|| format!("{doc_id}{raw_ref}")),
            status: if target.is_some() { "resolved" } else { "unresolved" }.into(),
            anchor_name: None,
        };
    }
    let (file_part, frag) = if let Some((f, g)) = raw_ref.split_once('#') {
        (f, format!("#{g}"))
    } else {
        (raw_ref, String::new())
    };
    let stem = std::path::Path::new(file_part)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or(file_part)
        .to_string();
    if let Some(target_doc) = by_id.get(&stem) {
        if !frag.is_empty() {
            let anchor_key = frag.trim_start_matches('#');
            if !frag.starts_with("#/") {
                if let Some(anchor_target) = anchors.get(&stem).and_then(|idx| resolve_anchor(idx, &frag)) {
                    return RefEdge {
                        schema_id: doc_id.to_string(),
                        ref_pointer,
                        target_id: anchor_target,
                        status: "resolved".into(),
                        anchor_name: Some(anchor_key.to_string()),
                    };
                }
            }
            if resolve_pointer(&target_doc.root, &frag).is_some() {
                return RefEdge {
                    schema_id: doc_id.to_string(),
                    ref_pointer,
                    target_id: format!("{stem}{frag}"),
                    status: "resolved".into(),
                    anchor_name: None,
                };
            }
        }
        return RefEdge {
            schema_id: doc_id.to_string(),
            ref_pointer,
            target_id: stem,
            status: "resolved".into(),
            anchor_name: None,
        };
    }
    RefEdge {
        schema_id: doc_id.to_string(),
        ref_pointer,
        target_id: file_part.to_string(),
        status: "unresolved".into(),
        anchor_name: None,
    }
}
