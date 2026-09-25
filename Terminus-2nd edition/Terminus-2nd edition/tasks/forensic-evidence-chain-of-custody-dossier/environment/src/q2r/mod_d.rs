use crate::custody_types::{IntegrityFinding, TransferEvent};
use serde_json::Value;
use std::collections::HashMap;
use std::fs;

pub fn load_status(path: &str) -> Result<HashMap<String, String>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let v: Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let mut map = HashMap::new();
    for loc in v["locations"].as_array().unwrap_or(&vec![]) {
        map.insert(
            loc["location_id"].as_str().unwrap_or("").to_string(),
            loc["status"].as_str().unwrap_or("").to_string(),
        );
    }
    Ok(map)
}

pub fn location_findings(
    catalog_path: &str,
    transfers: &[TransferEvent],
) -> Result<Vec<IntegrityFinding>, String> {
    let status = load_status(catalog_path)?;
    let mut out = Vec::new();
    for row in transfers {
        if row.event_type != "transfer" {
            continue;
        }
        let st = status
            .get(&row.from_location_id)
            .cloned()
            .unwrap_or_default();
        if st == "decommissioned" {
            out.push(IntegrityFinding {
                evidence_id: row.evidence_id.clone(),
                code: "location_invalid".into(),
                detail: row.from_location_id.clone(),
            });
        }
    }
    Ok(out)
}
