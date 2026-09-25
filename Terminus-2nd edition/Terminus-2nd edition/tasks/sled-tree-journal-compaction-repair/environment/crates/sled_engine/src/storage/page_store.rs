use crate::btree::node::BTreeNode;
use crate::commit::barrier::CommitRecord;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

const PAGES_PATH: &str = "/app/state/pages.json";
const RECORD_PATH: &str = "/app/state/commit_record.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PageDump {
    pub pages: BTreeMap<String, String>,
}

pub fn flush_children(tree: &crate::btree::node::BTree) -> Result<(), String> {
    let mut pages = PageDump::default();
    if let Some(root) = &tree.root {
        walk_pages(root, "root", &mut pages);
    }
    if let Some(parent) = Path::new(PAGES_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir pages: {e}"))?;
    }
    fs::write(PAGES_PATH, serde_json::to_string_pretty(&pages).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write pages: {e}"))?;
    Ok(())
}

fn walk_pages(node: &BTreeNode, id: &str, dump: &mut PageDump) {
    match node {
        BTreeNode::Leaf { entries } => {
            dump.pages.insert(id.to_string(), format!("leaf:{}", entries.len()));
        }
        BTreeNode::Internal { keys, children, .. } => {
            dump.pages.insert(id.to_string(), format!("internal:{}", keys.len()));
            for (i, child) in children.iter().enumerate() {
                let child_id = format!("{}-{}", id, i);
                walk_pages(child, &child_id, dump);
            }
        }
    }
}

pub fn write_commit_record(
    table: &str,
    height: u32,
    children_fsynced: bool,
    height_before_fsync: bool,
) -> Result<(), String> {
    let record = CommitRecord {
        table: table.to_string(),
        root_height: height,
        children_fsynced,
        height_recorded_before_child_fsync: height_before_fsync,
    };
    if let Some(parent) = Path::new(RECORD_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir record: {e}"))?;
    }
    fs::write(RECORD_PATH, serde_json::to_string_pretty(&record).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write record: {e}"))?;
    Ok(())
}
