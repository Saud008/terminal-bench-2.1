use super::BatchOp;

pub fn collapse_puts(ops: &[BatchOp]) -> Vec<(String, String)> {
    let mut out = Vec::new();
    for op in ops {
        if let BatchOp::Put { key, value } = op {
            out.push((key.clone(), value.clone()));
        }
    }
    out
}

pub fn append_put(tree: &mut crate::btree::node::BTree, key: String, value: String) -> Result<(), String> {
    if tree.root.is_none() {
        tree.root = Some(crate::btree::node::BTreeNode::leaf(vec![(key, value)]));
        tree.height = 1;
        return Ok(());
    }
    append_into_node(tree, key, value)?;
    Ok(())
}

fn append_into_node(tree: &mut crate::btree::node::BTree, key: String, value: String) -> Result<(), String> {
    let root = tree.root.take().expect("root");
    let (new_root, split) = append_recursive(root, key, value)?;
    if let Some((promoted, right)) = split {
        tree.height += 1;
        tree.root = Some(crate::btree::node::BTreeNode::internal(
            vec![promoted],
            vec![new_root, right],
        ));
    } else {
        tree.root = Some(new_root);
    }
    Ok(())
}

fn append_recursive(
    node: crate::btree::node::BTreeNode,
    key: String,
    value: String,
) -> Result<(crate::btree::node::BTreeNode, Option<(String, crate::btree::node::BTreeNode)>), String> {
    match node {
        crate::btree::node::BTreeNode::Leaf { entries } => {
            let mut entries = entries;
            entries.push((key, value));
            entries.sort_by(|a, b| a.0.cmp(&b.0));
            if entries.len() > crate::ORDER {
                let (left, promoted, right) = crate::btree::split::split_leaf(entries)?;
                return Ok((left, Some((promoted, right))));
            }
            Ok((crate::btree::node::BTreeNode::leaf(entries), None))
        }
        crate::btree::node::BTreeNode::Internal {
            keys,
            children,
            high_key: _,
        } => {
            let idx = child_index(&keys, &key);
            let (new_child, child_split) = append_recursive(children[idx].clone(), key, value)?;
            let mut keys = keys;
            let mut children = children;
            children[idx] = new_child;
            if let Some((promoted, right)) = child_split {
                keys.insert(idx, promoted);
                children.insert(idx + 1, right);
                if keys.len() > crate::ORDER {
                    let (left_i, promoted_i, right_i) =
                        crate::btree::split::split_internal(keys, children)?;
                    return Ok((left_i, Some((promoted_i, right_i))));
                }
            }
            Ok((crate::btree::node::BTreeNode::internal(keys, children), None))
        }
    }
}

fn child_index(keys: &[String], key: &str) -> usize {
    keys.iter().position(|k| key < k.as_str()).unwrap_or(keys.len())
}
