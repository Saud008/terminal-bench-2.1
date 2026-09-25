use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BTree {
    pub root: Option<BTreeNode>,
    pub height: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BTreeNode {
    Leaf { entries: Vec<(String, String)> },
    Internal {
        keys: Vec<String>,
        children: Vec<BTreeNode>,
        high_key: Option<String>,
    },
}

impl BTreeNode {
    pub fn leaf(entries: Vec<(String, String)>) -> Self {
        BTreeNode::Leaf { entries }
    }

    pub fn internal(keys: Vec<String>, children: Vec<BTreeNode>) -> Self {
        let high_key = children.last().and_then(|c| c.subtree_max_key());
        BTreeNode::Internal {
            keys,
            children,
            high_key,
        }
    }

    pub fn key_count(&self) -> usize {
        match self {
            BTreeNode::Leaf { entries } => entries.len(),
            BTreeNode::Internal { keys, .. } => keys.len(),
        }
    }

    pub fn subtree_max_key(&self) -> Option<String> {
        match self {
            BTreeNode::Leaf { entries } => entries.last().map(|(k, _)| k.clone()),
            BTreeNode::Internal { high_key, .. } => high_key.clone(),
        }
    }
}
