use crate::chain_schema::StandardLink;

pub fn trace_root(chain: &[StandardLink]) -> Result<String, String> {
    if chain.is_empty() {
        return Err("empty standard chain".into());
    }
    let mut current = chain[0].std_id.clone();
    for link in chain.iter().skip(1) {
        if link.parent_std.as_deref() == Some(&current) {
            current = link.std_id.clone();
        }
    }
    Ok(current)
}

pub fn chain_complete(chain: &[StandardLink]) -> bool {
    if chain.is_empty() {
        return false;
    }
    let mut parent: Option<&str> = None;
    for link in chain {
        if link.parent_std.as_deref() != parent {
            return false;
        }
        parent = Some(&link.std_id);
    }
    true
}
