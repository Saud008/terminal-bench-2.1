use super::node::BTreeNode;
use crate::ORDER;

pub fn borrow_from_sibling(
    parent_keys: &mut Vec<String>,
    parent_children: &mut Vec<BTreeNode>,
    child_idx: usize,
) -> Result<(), String> {
    let min_keys = (ORDER + 1) / 2;
    if child_idx + 1 < parent_children.len() {
        let right = &parent_children[child_idx + 1];
        if right.key_count() > min_keys {
            return borrow_from_right(parent_keys, parent_children, child_idx);
        }
    }
    if child_idx > 0 {
        let left = &parent_children[child_idx - 1];
        if left.key_count() > min_keys {
            return borrow_from_left(parent_keys, parent_children, child_idx);
        }
    }
    if child_idx > 0 {
        return merge_with_left(parent_keys, parent_children, child_idx);
    }
    merge_with_right(parent_keys, parent_children, child_idx)
}

fn borrow_from_left(
    parent_keys: &mut Vec<String>,
    parent_children: &mut Vec<BTreeNode>,
    child_idx: usize,
) -> Result<(), String> {
    let sep = parent_keys[child_idx - 1].clone();
    let left = parent_children[child_idx - 1].clone();
    let right = parent_children[child_idx].clone();
    let (new_left, new_right) = move_from_left(left, sep, right)?;
    parent_children[child_idx - 1] = new_left;
    parent_children[child_idx] = new_right;
    Ok(())
}

fn borrow_from_right(
    parent_keys: &mut Vec<String>,
    parent_children: &mut Vec<BTreeNode>,
    child_idx: usize,
) -> Result<(), String> {
    let sep = parent_keys[child_idx].clone();
    let left = parent_children[child_idx].clone();
    let right = parent_children[child_idx + 1].clone();
    let (new_left, new_right) = move_from_right(left, sep, right)?;
    parent_children[child_idx] = new_left;
    parent_children[child_idx + 1] = new_right;
    Ok(())
}

fn merge_with_left(
    parent_keys: &mut Vec<String>,
    parent_children: &mut Vec<BTreeNode>,
    child_idx: usize,
) -> Result<(), String> {
    let sep = parent_keys.remove(child_idx - 1);
    let left = parent_children.remove(child_idx - 1);
    let right = parent_children.remove(child_idx - 1);
    parent_children[child_idx - 1] = merge_nodes(left, sep, right)?;
    Ok(())
}

fn merge_with_right(
    parent_keys: &mut Vec<String>,
    parent_children: &mut Vec<BTreeNode>,
    child_idx: usize,
) -> Result<(), String> {
    let sep = parent_keys.remove(child_idx);
    let left = parent_children.remove(child_idx);
    let right = parent_children.remove(child_idx);
    parent_children[child_idx] = merge_nodes(left, sep, right)?;
    Ok(())
}

fn move_from_left(
    left: BTreeNode,
    sep: String,
    right: BTreeNode,
) -> Result<(BTreeNode, BTreeNode), String> {
    match (left, right) {
        (BTreeNode::Leaf { entries: le }, BTreeNode::Leaf { entries: re }) => {
            let mut left_entries = le;
            let last = left_entries.pop().expect("left leaf empty");
            let mut right_entries = vec![(sep, last.1)];
            right_entries.extend(re);
            Ok((BTreeNode::leaf(left_entries), BTreeNode::leaf(right_entries)))
        }
        (BTreeNode::Internal { keys: lk, children: lc }, BTreeNode::Internal { keys: rk, children: rc }) => {
            let mut left_keys = lk;
            let last_key = left_keys.pop().expect("left internal empty");
            let mut left_children = lc;
            let moved_child = left_children.pop().expect("left child missing");
            let mut right_keys = vec![last_key];
            right_keys.extend(rk);
            let mut right_children = vec![moved_child];
            right_children.extend(rc);
            Ok((
                BTreeNode::internal(left_keys, left_children),
                BTreeNode::internal(right_keys, right_children),
            ))
        }
        _ => Err("borrow type mismatch".into()),
    }
}

fn move_from_right(
    left: BTreeNode,
    sep: String,
    right: BTreeNode,
) -> Result<(BTreeNode, BTreeNode), String> {
    match (left, right) {
        (BTreeNode::Leaf { entries: le }, BTreeNode::Leaf { entries: re }) => {
            let mut right_entries = re;
            let first = right_entries.remove(0);
            let mut left_entries = le;
            left_entries.push((sep, first.1));
            Ok((BTreeNode::leaf(left_entries), BTreeNode::leaf(right_entries)))
        }
        (BTreeNode::Internal { keys: lk, children: lc }, BTreeNode::Internal { keys: rk, children: rc }) => {
            let mut right_keys = rk;
            let first_key = right_keys.remove(0);
            let mut right_children = rc;
            let moved_child = right_children.remove(0);
            let mut left_keys = lk;
            left_keys.push(first_key);
            let mut left_children = lc;
            left_children.push(moved_child);
            Ok((
                BTreeNode::internal(left_keys, left_children),
                BTreeNode::internal(right_keys, right_children),
            ))
        }
        _ => Err("borrow type mismatch".into()),
    }
}

fn merge_nodes(left: BTreeNode, sep: String, right: BTreeNode) -> Result<BTreeNode, String> {
    match (left, right) {
        (BTreeNode::Leaf { entries: le }, BTreeNode::Leaf { entries: re }) => {
            let mut merged = le;
            merged.push((sep, String::new()));
            merged.extend(re);
            Ok(BTreeNode::leaf(merged))
        }
        (BTreeNode::Internal { keys: lk, children: lc }, BTreeNode::Internal { keys: rk, children: rc }) => {
            let mut keys = lk;
            keys.push(sep);
            keys.extend(rk);
            let mut children = lc;
            children.extend(rc);
            Ok(BTreeNode::internal(keys, children))
        }
        _ => Err("merge type mismatch".into()),
    }
}
