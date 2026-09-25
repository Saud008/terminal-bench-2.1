use super::checksum::page_checksum;
use super::header::PageHeader;
use crate::btree::node::{BTree, BTreeNode};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

const REGISTRY_PATH: &str = "/app/state/page_registry.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PageRecord {
    pub header: PageHeader,
    pub body: String,
    pub checksum: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PageRegistry {
    pub pages: BTreeMap<String, PageRecord>,
}

pub fn load_registry() -> Result<PageRegistry, String> {
    if !Path::new(REGISTRY_PATH).exists() {
        return Ok(PageRegistry::default());
    }
    let raw = fs::read_to_string(REGISTRY_PATH).map_err(|e| format!("read registry: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse registry: {e}"))
}

pub fn save_registry(reg: &PageRegistry) -> Result<(), String> {
    if let Some(parent) = Path::new(REGISTRY_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| format!("mkdir registry: {e}"))?;
    }
    fs::write(REGISTRY_PATH, serde_json::to_string_pretty(reg).map_err(|e| e.to_string())?)
        .map_err(|e| format!("write registry: {e}"))?;
    Ok(())
}

pub fn persist_page(page_id: &str, header: PageHeader, body: String) -> Result<(), String> {
    let mut reg = load_registry()?;
    let checksum = page_checksum(&header, body.as_bytes());
    reg.pages.insert(
        page_id.to_string(),
        PageRecord {
            header,
            body,
            checksum,
        },
    );
    save_registry(&reg)
}

pub fn sync_registry_from_tree(tree: &BTree) -> Result<(), String> {
    let mut reg = PageRegistry::default();
    if let Some(root) = &tree.root {
        walk_tree_pages(root, "root", &mut reg, 1)?;
    }
    save_registry(&reg)
}

fn walk_tree_pages(
    node: &BTreeNode,
    id: &str,
    reg: &mut PageRegistry,
    generation: u64,
) -> Result<(), String> {
    let high_key = node_high_key(node);
    let body = match node {
        BTreeNode::Leaf { entries } => format!("leaf:{entries:?}"),
        BTreeNode::Internal { keys, .. } => format!("internal:{keys:?}"),
    };
    let header = PageHeader::new(id, generation, high_key);
    let checksum = page_checksum(&header, body.as_bytes());
    reg.pages.insert(
        id.to_string(),
        PageRecord {
            header,
            body: body.clone(),
            checksum,
        },
    );
    if let BTreeNode::Internal { children, .. } = node {
        for (i, child) in children.iter().enumerate() {
            walk_tree_pages(child, &format!("{id}-{i}"), reg, generation)?;
        }
    }
    Ok(())
}

fn node_high_key(node: &BTreeNode) -> Option<String> {
    match node {
        BTreeNode::Leaf { entries } => entries.last().map(|(k, _)| k.clone()),
        BTreeNode::Internal {
            high_key,
            keys,
            children,
        } => {
            if let Some(hk) = high_key {
                return Some(hk.clone());
            }
            if let Some(last_child) = children.last() {
                return node_high_key(last_child);
            }
            keys.last().cloned()
        }
    }
}
