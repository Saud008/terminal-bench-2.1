use serde_json::Value;

pub fn resolve_pointer(root: &Value, pointer: &str) -> Option<Value> {
    if pointer.is_empty() || pointer == "#" || pointer == "#/" {
        return Some(root.clone());
    }
    let mut p = pointer.trim_start_matches('#');
    if p.is_empty() {
        return Some(root.clone());
    }
    if !p.starts_with('/') {
        return None;
    }
    let mut cur = root;
    for part in p.trim_start_matches('/').split('/') {
        let part = part.replace("~0", "~").replace("~1", "/");
        if part.chars().all(|c| c.is_ascii_digit()) {
            let idx: usize = part.parse().ok()?;
            cur = cur.get(idx)?;
        } else {
            cur = cur.get(&part)?;
        }
    }
    Some(cur.clone())
}
