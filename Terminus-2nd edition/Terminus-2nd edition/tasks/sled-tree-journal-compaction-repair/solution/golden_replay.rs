use super::BatchOp;

pub fn collapse_puts(ops: &[BatchOp]) -> Vec<(String, String)> {
    let mut map = std::collections::BTreeMap::new();
    for op in ops {
        if let BatchOp::Put { key, value } = op {
            map.insert(key.clone(), value.clone());
        }
    }
    map.into_iter().collect()
}

pub fn append_put(
    tree: &mut crate::btree::node::BTree,
    key: String,
    value: String,
) -> Result<(), String> {
    crate::btree::insert(tree, key, value)
}
