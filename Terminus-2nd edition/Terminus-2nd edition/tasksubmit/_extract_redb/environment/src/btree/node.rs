use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BTree {
    pub root: Option<BTreeNode>,
    pub height: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BTreeNode {
    Leaf { entries: Vec<(String, String)> },
    Internal { keys: Vec<String>, children: Vec<BTreeNode> },
}

impl BTreeNode {
    pub fn leaf(entries: Vec<(String, String)>) -> Self {
        BTreeNode::Leaf { entries }
    }

    pub fn internal(keys: Vec<String>, children: Vec<BTreeNode>) -> Self {
        BTreeNode::Internal { keys, children }
    }

    pub fn key_count(&self) -> usize {
        match self {
            BTreeNode::Leaf { entries } => entries.len(),
            BTreeNode::Internal { keys, .. } => keys.len(),
        }
    }
}
