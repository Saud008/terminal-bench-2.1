use crate::{
    active_set, imbalance_ledger, bucket_key, limit_gate, permuted_assign, BALANCE_PATH, LATCH_PATH,
    CHRONICLE_PATH,
};
use serde_json::Value;
use std::{collections::HashMap, fs, path::Path};

pub fn run_balance(trial_id: &str, root: &str) -> Result<(), String> {
    let latch: Value = serde_json::from_str(&fs::read_to_string(LATCH_PATH).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let chronicle: Value = serde_json::from_str(&fs::read_to_string(CHRONICLE_PATH).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let sites: Value = serde_json::from_str(
        &fs::read_to_string(Path::new(root).join("ceilings").join(format!("{trial_id}.json")))
            .map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let caps: HashMap<String, u32> = sites["site_caps"]
        .as_object()
        .ok_or("site_caps")?
        .iter()
        .map(|(k, v)| (k.clone(), v.as_u64().unwrap_or(0) as u32))
        .collect();
    let arms: Vec<String> = latch["arms"]
        .as_array()
        .ok_or("arms")?
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect();
    let block_sizes: Vec<usize> = latch["block_sizes"]
        .as_array()
        .ok_or("block_sizes")?
        .iter()
        .map(|v| v.as_u64().unwrap_or(4) as usize)
        .collect();
    let seed_salt = latch["seed_salt"].as_str().unwrap_or("");
    let mut history: Vec<(String, String, String, String)> = Vec::new();
    let mut stratum_of: HashMap<String, String> = HashMap::new();
    let mut block_idx: HashMap<String, usize> = HashMap::new();
    let mut block_pos: HashMap<String, usize> = HashMap::new();
    let mut current_block: HashMap<String, Vec<String>> = HashMap::new();
    let mut active_site: HashMap<String, u32> = HashMap::new();
    for row in chronicle["rows"].as_array().ok_or("rows")? {
        let subject = row["subject_id"].as_str().unwrap_or("").to_string();
        let site = row["site_id"].as_str().unwrap_or("").to_string();
        let stratum = row["stratum_id"].as_str().unwrap_or("").to_string();
        let event = row["event"].as_str().unwrap_or("").to_string();
        stratum_of.insert(subject.clone(), stratum.clone());
        if event == "withdraw" {
            if active_site.get(&site).copied().unwrap_or(0) > 0 {
                *active_site.get_mut(&site).unwrap() -= 1;
            }
            history.push((subject, "withdraw".into(), String::new(), site));
            continue;
        }
        if event != "enroll" {
            continue;
        }
        let _bucket = bucket_key::bucket_key(
            latch["strata"]
                .as_array()
                .ok_or("strata")?
                .iter()
                .find(|s| s["stratum_id"].as_str() == Some(stratum.as_str()))
                .and_then(|s| s.get("factors"))
                .ok_or("factors")?,
        )?;
        if active_site.get(&site).copied().unwrap_or(0) >= caps.get(&site).copied().unwrap_or(u32::MAX) {
            history.push((subject, "cap_rejected".into(), String::new(), site));
            continue;
        }
        let b_i = block_idx.entry(stratum.clone()).or_insert(0);
        let pos = block_pos.entry(stratum.clone()).or_insert(0);
        let bsize = block_sizes[*b_i % block_sizes.len()];
        if !current_block.contains_key(&stratum) || *pos >= current_block.get(&stratum).map(|b| b.len()).unwrap_or(0) {
            current_block.insert(
                stratum.clone(),
                permuted_assign::permute_block(
                    &arms,
                    bsize,
                    permuted_assign::block_seed(&stratum, trial_id, seed_salt) ^ (*b_i as u64),
                ),
            );
            *block_pos.get_mut(&stratum).unwrap() = 0;
        }
        let block = current_block.get(&stratum).unwrap();
        let pos_now = *block_pos.get(&stratum).unwrap();
        let arm = block[pos_now].clone();
        *block_pos.get_mut(&stratum).unwrap() = pos_now + 1;
        if *block_pos.get(&stratum).unwrap() >= bsize {
            *block_idx.get_mut(&stratum).unwrap() += 1;
            *block_pos.get_mut(&stratum).unwrap() = 0;
            current_block.remove(&stratum);
        }
        *active_site.entry(site.clone()).or_insert(0) += 1;
        history.push((subject.clone(), "assign".into(), arm.clone(), site.clone()));
    }
    let (arm_map, withdrawn) = active_set::apply_events(
        &history
            .iter()
            .map(|(s, e, a, site)| (s.clone(), e.clone(), a.clone(), site.clone()))
            .collect::<Vec<_>>(),
    );
    let mut per_stratum = Vec::new();
    for s in latch["strata"].as_array().ok_or("strata")? {
        let sid = s["stratum_id"].as_str().unwrap_or("");
        let (a, b) = active_set::active_arm_counts(&arm_map, &withdrawn, &stratum_of, sid);
        per_stratum.push(serde_json::json!({"stratum_id": sid, "arm_a": a, "arm_b": b, "active_total": a + b}));
    }
    let skew_rows: Vec<(u32, u32)> = per_stratum
        .iter()
        .map(|r| (r["arm_a"].as_u64().unwrap_or(0) as u32, r["arm_b"].as_u64().unwrap_or(0) as u32))
        .collect();
    let site_history: Vec<(String, String, bool)> = history
        .iter()
        .map(|(s, e, _a, site)| {
            let active = e == "assign" && !withdrawn.contains(s);
            (site.clone(), s.clone(), active)
        })
        .collect();
    let body = serde_json::json!({
        "trial_id": trial_id,
        "protocol_digest": latch["protocol_digest"],
        "run_id": 1,
        "per_stratum": per_stratum,
        "max_skew": imbalance_ledger::max_skew(&skew_rows),
        "venues_at_cap": limit_gate::venues_at_cap(&limit_gate::active_site_counts(&site_history), &caps),
        "open_slots": latch["strata"].as_array().unwrap_or(&vec![]).iter().map(|s| {
            let sid = s["stratum_id"].as_str().unwrap_or("");
            let pos = block_pos.get(sid).copied().unwrap_or(0);
            let b_i = block_idx.get(sid).copied().unwrap_or(0);
            let bsize = block_sizes[b_i % block_sizes.len()];
            serde_json::json!({"stratum_id": sid, "remaining_slots": bsize.saturating_sub(pos), "block_size": bsize})
        }).collect::<Vec<_>>(),
        "assignment_history": history,
    });
    if let Some(parent) = Path::new(BALANCE_PATH).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(BALANCE_PATH, serde_json::to_string_pretty(&body).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())
}
