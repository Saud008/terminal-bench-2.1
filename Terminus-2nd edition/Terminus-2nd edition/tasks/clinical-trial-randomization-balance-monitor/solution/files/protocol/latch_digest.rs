use serde_json::Value;
use sha2::{Digest, Sha256};

pub fn protocol_digest(protocol: &Value) -> Result<String, String> {
    let trial_id = protocol["trial_id"].as_str().ok_or("trial_id")?;
    let version = protocol["protocol_version"].as_str().ok_or("protocol_version")?;
    let arms = protocol["arms"].as_array().ok_or("arms")?;
    let mut arm_list: Vec<String> = arms.iter().filter_map(|v| v.as_str().map(String::from)).collect();
    arm_list.sort();
    let block_sizes = protocol["block_sizes"].clone();
    let seed_salt = protocol["seed_salt"].as_str().ok_or("seed_salt")?;
    let strata = protocol["strata"].as_array().ok_or("strata")?;
    let mut strata_rows = Vec::new();
    for row in strata {
        let sid = row["stratum_id"].as_str().ok_or("stratum_id")?;
        let factors = &row["factors"];
        strata_rows.push(serde_json::json!({"stratum_id": sid, "bucket_key": bucket_key(factors)?}));
    }
    strata_rows.sort_by(|a, b| a["stratum_id"].as_str().cmp(&b["stratum_id"].as_str()));
    let body = serde_json::json!({
        "trial_id": trial_id,
        "protocol_version": version,
        "arms": arm_list,
        "block_sizes": block_sizes,
        "seed_salt": seed_salt,
        "strata": strata_rows,
    });
    let canonical = serde_json::to_string(&body).map_err(|e| e.to_string())?;
    Ok(hex::encode(Sha256::digest(canonical.as_bytes())))
}

fn bucket_key(factors: &Value) -> Result<String, String> {
    let obj = factors.as_object().ok_or("factors object")?;
    let mut map = serde_json::Map::new();
    let mut keys: Vec<&String> = obj.keys().collect();
    keys.sort();
    for k in keys {
        map.insert(k.clone(), obj[k].clone());
    }
    serde_json::to_string(&serde_json::Value::Object(map)).map_err(|e| e.to_string())
}
