use std::collections::HashSet;

use crate::types::{LedgerComponent, ReexportEdge, WireExport};
use crate::{EXPORT_KIND_FUNC, EXPORT_KIND_INSTANCE};

pub fn resolve_surfaces(comp: &LedgerComponent) -> Vec<(String, String)> {
    let mut out = Vec::new();
    for edge in &comp.reexports {
        if let Some(leaf) = resolve_symbol(
            edge.via_instance,
            &edge.inner,
            &comp.exports,
            &comp.reexports,
            &mut HashSet::new(),
        ) {
            out.push((edge.outer.clone(), leaf));
        }
    }
    out.sort_by(|a, b| a.0.cmp(&b.0));
    out
}

fn resolve_symbol(
    inst: u16,
    sym: &str,
    exports: &[WireExport],
    reexports: &[ReexportEdge],
    seen: &mut HashSet<(u16, String)>,
) -> Option<String> {
    let key = (inst, sym.to_string());
    if seen.contains(&key) {
        return None;
    }
    seen.insert(key);
    if let Some(leaf) = func_on_instance(inst, sym, exports) {
        return Some(leaf);
    }
    let links = instance_links(exports);
    if let Some(&child) = links.get(sym) {
        if let Some(leaf) = first_func_on(child, exports) {
            return Some(leaf);
        }
    }
    for edge in reexports {
        if edge.via_instance == inst && edge.inner == sym {
            return resolve_symbol(inst, &edge.outer, exports, reexports, seen);
        }
        if edge.via_instance == inst && edge.outer == sym {
            return resolve_symbol(inst, &edge.inner, exports, reexports, seen);
        }
    }
    None
}

fn func_on_instance(inst: u16, name: &str, exports: &[WireExport]) -> Option<String> {
    if inst != 0 {
        return None;
    }
    for exp in exports {
        if exp.kind == EXPORT_KIND_FUNC && exp.name == name {
            return Some(exp.name.clone());
        }
    }
    None
}

fn first_func_on(inst: u16, exports: &[WireExport]) -> Option<String> {
    if inst != 0 {
        return None;
    }
    let mut names: Vec<String> = exports
        .iter()
        .filter(|e| e.kind == EXPORT_KIND_FUNC)
        .map(|e| e.name.clone())
        .collect();
    names.sort();
    names.into_iter().next()
}

fn instance_links(exports: &[WireExport]) -> std::collections::HashMap<String, u16> {
    let mut map = std::collections::HashMap::new();
    for exp in exports {
        if exp.kind == EXPORT_KIND_INSTANCE {
            if let Some(target) = exp.instance_target {
                map.insert(exp.name.clone(), target);
            }
        }
    }
    map
}
