use crate::commit::state::load_committed;
use crate::page::registry::{load_registry, save_registry};
use crate::snapshot::pin::load_pin_set;
use std::collections::BTreeSet;

pub fn compact_table(table: &str) -> Result<u32, String> {
    let committed = load_committed()?;
    let tree = committed
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let live = live_page_ids(&tree);
    let mut reg = load_registry()?;
    let _pinned = load_pin_set(table)?;
    let mut freed = 0u32;
    let ids: Vec<String> = reg.pages.keys().cloned().collect();
    for id in ids {
        if live.contains(&id) {
            continue;
        }
        reg.pages.remove(&id);
        freed += 1;
    }
    save_registry(&reg)?;
    Ok(freed)
}

fn live_page_ids(tree: &crate::btree::node::BTree) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    if let Some(root) = &tree.root {
        collect_ids(root, "root", &mut out);
    }
    out
}

fn collect_ids(node: &crate::btree::node::BTreeNode, id: &str, out: &mut BTreeSet<String>) {
    out.insert(id.to_string());
    if let crate::btree::node::BTreeNode::Internal { children, .. } = node {
        for (i, child) in children.iter().enumerate() {
            collect_ids(child, &format!("{id}-{i}"), out);
        }
    }
}
