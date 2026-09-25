use super::BatchOp;

pub fn collapse_puts(ops: &[BatchOp]) -> Vec<(String, String)> {
    let mut map = std::collections::BTreeMap::new();
    for op in ops {
        match op {
            BatchOp::Put { key, value } => {
                map.insert(key.clone(), Some(value.clone()));
            }
            BatchOp::Delete { key } => {
                map.insert(key.clone(), None);
            }
        }
    }
    map.into_iter()
        .filter_map(|(k, v)| v.map(|value| (k, value)))
        .collect()
}

pub fn append_put(
    tree: &mut crate::btree::node::BTree,
    key: String,
    value: String,
) -> Result<(), String> {
    crate::btree::insert(tree, key, value)
}
