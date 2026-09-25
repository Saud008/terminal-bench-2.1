use serde_json::Value;

pub fn normalize_rows(rows: &mut Vec<Value>) {
    rows.sort_by(|a, b| {
        let sa = a["seq"].as_u64().unwrap_or(0);
        let sb = b["seq"].as_u64().unwrap_or(0);
        sa.cmp(&sb).then_with(|| a["ts"].as_u64().unwrap_or(0).cmp(&b["ts"].as_u64().unwrap_or(0)))
    });
    let mut best: std::collections::HashMap<(String, String), Value> = std::collections::HashMap::new();
    for row in rows.iter().cloned() {
        let subject = row["subject_id"].as_str().unwrap_or("").to_string();
        let event = row["event"].as_str().unwrap_or("").to_string();
        let key = (subject, event);
        let replace = match best.get(&key) {
            None => true,
            Some(prev) => row["seq"].as_u64().unwrap_or(0) >= prev["seq"].as_u64().unwrap_or(0),
        };
        if replace {
            best.insert(key, row);
        }
    }
    let mut out: Vec<Value> = best.into_values().collect();
    rows.sort_by(|a, b| a["ts"].as_u64().unwrap_or(0).cmp(&b["ts"].as_u64().unwrap_or(0)));
    rows.clear();
    rows.extend(out);
}
