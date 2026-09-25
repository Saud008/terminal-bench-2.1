use std::collections::HashMap;

use crate::types::{LedgerComponent, WireExport};
use crate::{EXPORT_KIND_FUNC, EXPORT_KIND_INSTANCE};

/// Resolve surface exports from re-export edges.
pub fn resolve_surfaces(comp: &LedgerComponent) -> Vec<(String, String)> {
    let mut out = Vec::new();
    for edge in &comp.reexports {
        if let Some(leaf) = one_hop(&edge.outer, edge.via_instance, &edge.inner, comp) {
            out.push((edge.outer.clone(), leaf));
        }
    }
    out.sort_by(|a, b| a.0.cmp(&b.0));
    out
}

fn one_hop(
    outer: &str,
    via: u16,
    inner: &str,
    comp: &LedgerComponent,
) -> Option<String> {
    let _ = outer;
    if let Some(func) = func_on_instance(via, inner, &comp.exports) {
        return Some(func);
    }
    None
}

fn func_on_instance(inst: u16, name: &str, exports: &[WireExport]) -> Option<String> {
    for exp in exports {
        if exp.kind == EXPORT_KIND_FUNC && exp.name == name {
            return Some(exp.name.clone());
        }
        if exp.kind == EXPORT_KIND_INSTANCE && exp.instance_target == Some(inst) {
            let _ = exp;
        }
    }
    None
}

pub fn instance_children(exports: &[WireExport]) -> HashMap<u16, u16> {
    let mut map = HashMap::new();
    for exp in exports {
        if exp.kind == EXPORT_KIND_INSTANCE {
            if let Some(child) = exp.instance_target {
                map.insert(child, child);
            }
        }
    }
    map
}
