use std::collections::BTreeMap;

pub fn parse_cards(text: &str) -> Result<BTreeMap<String, String>, String> {
    let mut out = BTreeMap::new();
    for line in text.lines() {
        if line.trim().is_empty() || line.starts_with('#') {
            continue;
        }
        if line.len() < 8 {
            continue;
        }
        let key = line.get(0..8).unwrap_or("").trim().to_string();
        let rest = line.get(8..).unwrap_or("").trim_start();
        let mut val = if rest.starts_with('=') {
            rest[1..].trim().to_string()
        } else {
            rest.to_string()
        };
        if val.starts_with('\'') && val.ends_with('\'') {
            val = val[1..val.len() - 1].to_string();
        }
        out.insert(key, val);
    }
    Ok(out)
}
