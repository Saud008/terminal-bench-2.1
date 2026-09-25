use super::node::BTreeNode;
use crate::ORDER;

pub fn delete_recursive(node: BTreeNode, key: &str) -> Result<(Option<BTreeNode>, bool), String> {
    match node {
        BTreeNode::Leaf { entries } => {
            let mut entries = entries;
            if let Some(pos) = entries.iter().position(|(k, _)| k == key) {
                entries.remove(pos);
                if entries.is_empty() {
                    return Ok((None, true));
                }
                return Ok((Some(BTreeNode::leaf(entries)), true));
            }
            Ok((Some(BTreeNode::leaf(entries)), false))
        }
        BTreeNode::Internal { keys, children } => {
            if children.len() == 1 {
                return delete_recursive(children[0].clone(), key);
            }
            let idx = child_index(&keys, key);
            if idx >= children.len() {
                return Err(format!("child index {idx} exceeds children {}", children.len()));
            }
            let (new_child, removed) = delete_recursive(children[idx].clone(), key)?;
            if !removed {
                return Ok((Some(BTreeNode::internal(keys, children)), false));
            }
            let mut keys = keys;
            let mut children = children;
            if new_child.is_none() {
                children.remove(idx);
                if idx < keys.len() {
                    keys.remove(idx);
                }
                if children.len() == 1 {
                    return Ok((Some(children[0].clone()), true));
                }
                return Ok((Some(BTreeNode::internal(keys, children)), true));
            }
            children[idx] = new_child.unwrap();
            let min_keys = (ORDER + 1) / 2;
            if children[idx].key_count() < min_keys {
                return Ok((Some(BTreeNode::internal(keys, children)), true));
            }
            Ok((Some(BTreeNode::internal(keys, children)), true))
        }
    }
}

fn child_index(keys: &[String], key: &str) -> usize {
    keys.iter().position(|k| key < k.as_str()).unwrap_or(keys.len())
}
