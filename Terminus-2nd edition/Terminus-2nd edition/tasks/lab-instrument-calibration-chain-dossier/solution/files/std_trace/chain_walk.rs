use lab_calibration_chain::chain_schema::StandardLink;

pub fn trace_root(chain: &[StandardLink]) -> Result<String, String> {
    if chain.is_empty() {
        return Err("empty standard chain".into());
    }
    for link in chain {
        if link.parent_std.is_none() {
            return Ok(link.std_id.clone());
        }
    }
    Err("no trace root".into())
}

pub fn chain_complete(chain: &[StandardLink]) -> bool {
    if chain.is_empty() {
        return false;
    }
    let mut prev_id: Option<&str> = None;
    for (i, link) in chain.iter().enumerate() {
        if i == 0 {
            if link.parent_std.is_some() {
                return false;
            }
        } else if link.parent_std.as_deref() != prev_id {
            return false;
        }
        prev_id = Some(&link.std_id);
    }
    true
}
