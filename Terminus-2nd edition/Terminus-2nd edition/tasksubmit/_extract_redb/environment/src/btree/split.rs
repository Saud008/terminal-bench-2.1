use super::node::BTreeNode;

/// Split a full leaf. Contract: for odd entry count n, left receives floor(n/2)
/// entries, promoted separator is the first key of the right child (index n/2).
pub fn split_leaf(entries: Vec<(String, String)>) -> Result<(BTreeNode, String, BTreeNode), String> {
    let n = entries.len();
    if n <= 1 {
        return Err("leaf too small to split".into());
    }
    let left_size = if n % 2 == 1 {
        (n + 1) / 2
    } else {
        n / 2
    };
    let left_entries = entries[..left_size].to_vec();
    let promoted = entries[left_size].0.clone();
    let right_entries = entries[left_size..].to_vec();
    Ok((
        BTreeNode::leaf(left_entries),
        promoted,
        BTreeNode::leaf(right_entries),
    ))
}

pub fn split_internal(
    keys: Vec<String>,
    children: Vec<BTreeNode>,
) -> Result<(BTreeNode, String, BTreeNode), String> {
    let n = keys.len();
    let mid = if n % 2 == 1 {
        (n + 1) / 2
    } else {
        n / 2
    };
    let promoted = keys[mid].clone();
    let left_keys = keys[..mid].to_vec();
    let right_keys = keys[mid + 1..].to_vec();
    let left_children = children[..mid + 1].to_vec();
    let right_children = children[mid + 1..].to_vec();
    Ok((
        BTreeNode::internal(left_keys, left_children),
        promoted,
        BTreeNode::internal(right_keys, right_children),
    ))
}
