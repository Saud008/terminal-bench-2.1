use crate::commit::state::load_committed;
use crate::btree::node::BTreeNode;

#[derive(serde::Serialize)]
pub struct ExportRow {
    pub key: String,
    pub value: String,
}

pub fn scan_committed_table(table: &str) -> Result<Vec<ExportRow>, String> {
    let committed = load_committed()?;
    let tree = committed
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let entries = crate::btree::ordered_entries(&tree);
    Ok(entries
        .into_iter()
        .map(|(key, value)| ExportRow { key, value })
        .collect())
}

pub fn scan_range(table: &str, start: &str, end: &str) -> Result<Vec<ExportRow>, String> {
    let committed = load_committed()?;
    let tree = committed
        .tables
        .tables
        .get(table)
        .cloned()
        .unwrap_or_default();
    let mut rows = Vec::new();
    if let Some(root) = tree.root {
        collect_range(&root, start, end, &mut rows);
    }
    rows.sort_by(|a, b| a.key.cmp(&b.key));
    Ok(dedupe_rows(rows))
}

fn dedupe_rows(rows: Vec<ExportRow>) -> Vec<ExportRow> {
    let mut map = std::collections::BTreeMap::new();
    for row in rows {
        map.insert(row.key, row.value);
    }
    map.into_iter()
        .map(|(key, value)| ExportRow { key, value })
        .collect()
}

fn collect_range(node: &BTreeNode, start: &str, end: &str, out: &mut Vec<ExportRow>) {
    match node {
        BTreeNode::Leaf { entries } => {
            for (key, value) in entries {
                if key.as_str() >= start && key.as_str() <= end {
                    out.push(ExportRow {
                        key: key.clone(),
                        value: value.clone(),
                    });
                }
            }
        }
        BTreeNode::Internal {
            high_key,
            children,
            ..
        } => {
            if let Some(hk) = high_key {
                if hk.as_str() < start {
                    return;
                }
            }
            for child in children {
                collect_range(child, start, end, out);
            }
        }
    }
}
