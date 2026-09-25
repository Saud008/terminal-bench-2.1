use serde_json::Value;
use sha2::{Digest, Sha256};

pub fn protocol_digest(protocol: &Value) -> Result<String, String> {
    let trial_id = protocol["trial_id"].as_str().ok_or("trial_id")?;
    let arms = protocol["arms"].as_array().ok_or("arms")?;
    let mut arm_list: Vec<&str> = arms.iter().filter_map(|v| v.as_str()).collect();
    arm_list.sort_unstable();
    let block_sizes = protocol["block_sizes"].as_array().ok_or("block_sizes")?;
    let seed_salt = protocol["seed_salt"].as_str().ok_or("seed_salt")?;
    let strata = protocol["strata"].as_array().ok_or("strata")?;
    let mut parts: Vec<String> = Vec::new();
    parts.push(format!("trial_id={trial_id}"));
    parts.push(format!("arms={}", arm_list.join(",")));
    parts.push(format!("block_sizes={block_sizes:?}"));
    parts.push(format!("seed_salt={seed_salt}"));
    for row in strata {
        let sid = row["stratum_id"].as_str().ok_or("stratum_id")?;
        let factors = row["factors"].as_object().ok_or("factors")?;
        let mut keys: Vec<&str> = factors.keys().map(String::as_str).collect();
        keys.sort_unstable();
        let mut fparts: Vec<String> = Vec::new();
        for k in keys {
            fparts.push(format!("{k}={}", factors[k].as_str().unwrap_or("")));
        }
        parts.push(format!("stratum:{sid}:{}", fparts.join(",")));
    }
    let preimage = parts.join("|");
    Ok(hex::encode(Sha256::digest(preimage.as_bytes())))
}
