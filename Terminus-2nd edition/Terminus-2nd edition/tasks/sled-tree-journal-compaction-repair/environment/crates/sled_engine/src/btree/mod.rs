pub mod merge;
pub mod node;
pub mod split;
pub mod underflow;

use crate::ORDER;
use node::{BTree, BTreeNode};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub fn insert(tree: &mut BTree, key: String, value: String) -> Result<(), String> {
    if tree.root.is_none() {
        tree.root = Some(BTreeNode::leaf(vec![(key, value)]));
        tree.height = 1;
        return Ok(());
    }
    let root = tree.root.take().expect("root");
    let (new_root, split_promote) = insert_node(root, key, value)?;
    if let Some((promoted_key, right)) = split_promote {
        tree.height += 1;
        tree.root = Some(BTreeNode::internal(
            vec![promoted_key],
            vec![new_root, right],
        ));
    } else {
        tree.root = Some(new_root);
    }
    Ok(())
}

fn insert_node(node: BTreeNode, key: String, value: String) -> Result<(BTreeNode, Option<(String, BTreeNode)>), String> {
    match node {
        BTreeNode::Leaf { entries } => {
            let mut entries = entries;
            if let Some(pos) = entries.iter().position(|(k, _)| k == &key) {
                entries[pos].1 = value;
                return Ok((BTreeNode::leaf(entries), None));
            }
            entries.push((key, value));
            entries.sort_by(|a, b| a.0.cmp(&b.0));
            if entries.len() > ORDER {
                let (left, promoted, right) = split::split_leaf(entries)?;
                return Ok((left, Some((promoted, right))));
            }
            Ok((BTreeNode::leaf(entries), None))
        }
        BTreeNode::Internal {
            keys,
            children,
            high_key: _,
        } => {
            let idx = child_index(&keys, &key);
            let (new_child, child_split) = insert_node(children[idx].clone(), key, value)?;
            let mut keys = keys;
            let mut children = children;
            children[idx] = new_child;
            if let Some((promoted, right)) = child_split {
                keys.insert(idx, promoted);
                children.insert(idx + 1, right);
                if keys.len() > ORDER {
                    let (left_internal, promoted_key, right_internal) =
                        split::split_internal(keys, children)?;
                    return Ok((left_internal, Some((promoted_key, right_internal))));
                }
            }
            Ok((BTreeNode::internal(keys, children), None))
        }
    }
}

pub fn delete(tree: &mut BTree, key: &str) -> Result<bool, String> {
    if tree.root.is_none() {
        return Ok(false);
    }
    let root = tree.root.take().expect("root");
    let (new_root, removed) = underflow::delete_recursive(root, key)?;
    tree.root = new_root;
    if tree.root.is_none() {
        tree.height = 0;
    } else if tree.height > 1 {
        if let Some(BTreeNode::Internal { keys, children, .. }) = &tree.root {
            if keys.is_empty() && children.len() == 1 {
                tree.root = Some(children[0].clone());
                tree.height -= 1;
            }
        }
    }
    Ok(removed)
}

pub fn ordered_entries(tree: &BTree) -> Vec<(String, String)> {
    let mut out = Vec::new();
    if let Some(root) = &tree.root {
        collect_leaves(root, &mut out);
    }
    out.sort_by(|a, b| a.0.cmp(&b.0));
    dedupe_last_wins(&mut out);
    out
}

fn dedupe_last_wins(entries: &mut Vec<(String, String)>) {
    if entries.is_empty() {
        return;
    }
    let mut seen = std::collections::BTreeMap::new();
    for (k, v) in entries.drain(..) {
        seen.insert(k, v);
    }
    entries.extend(seen.into_iter());
}

pub fn physical_entry_count(tree: &BTree) -> u32 {
    let mut out = Vec::new();
    if let Some(root) = &tree.root {
        collect_leaves(root, &mut out);
    }
    out.len() as u32
}

pub fn unique_key_count(tree: &BTree) -> u32 {
    ordered_entries(tree).len() as u32
}

fn collect_leaves(node: &BTreeNode, out: &mut Vec<(String, String)>) {
    match node {
        BTreeNode::Leaf { entries } => out.extend(entries.iter().cloned()),
        BTreeNode::Internal { children, .. } => {
            for child in children {
                collect_leaves(child, out);
            }
        }
    }
}

pub fn leaf_count(tree: &BTree) -> u32 {
    let mut count = 0u32;
    if let Some(root) = &tree.root {
        count_leaves(root, &mut count);
    }
    count
}

fn count_leaves(node: &BTreeNode, count: &mut u32) {
    match node {
        BTreeNode::Leaf { .. } => *count += 1,
        BTreeNode::Internal { children, .. } => {
            for c in children {
                count_leaves(c, count);
            }
        }
    }
}

fn child_index(keys: &[String], key: &str) -> usize {
    keys.iter().position(|k| key < k.as_str()).unwrap_or(keys.len())
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct TableMap {
    pub tables: BTreeMap<String, BTree>,
}

impl TableMap {
    pub fn get_or_insert(&mut self, name: &str) -> &mut BTree {
        self.tables.entry(name.to_string()).or_default()
    }
}
