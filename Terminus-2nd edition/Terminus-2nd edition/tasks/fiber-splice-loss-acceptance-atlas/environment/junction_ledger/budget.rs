use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn load_inventory(path: &Path) -> Result<BTreeMap<String, f64>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let v: serde_json::Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let mut out = BTreeMap::new();
    if let Some(arr) = v["connectors"].as_array() {
        for row in arr {
            let t = row["type"].as_str().unwrap_or("").to_string();
            let loss = row["pair_loss_db"].as_f64().unwrap_or(0.0);
            out.insert(t, loss);
        }
    }
    Ok(out)
}
