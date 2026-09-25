#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find /app/manifest /app/alpha /app/stratify /app/blocks /app/ceilings /app/closure /app/pipeline /app/decoy /app/src -name '*.rs' -exec sed -i 's/\r$//' {} +

require_grep() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if ! grep -qE "${pattern}" "${file}"; then
    echo "oracle preflight missing ${label} in ${file}" >&2
    exit 1
  fi
}

preflight_stubs() {
  require_grep /app/alpha/beta_norm.rs 'sa\.cmp.*then_with' 'seq-first sort stub'
  require_grep /app/stratify/bucket_key.rs 'to_string\(factors\)' 'unsorted bucket stub'
  require_grep /app/blocks/permuted_assign.rs 'stratum_id.as_bytes' 'stratum-only seed stub'
  require_grep /app/ceilings/limit_gate.rs '_active\)' 'all-events cap stub'
  require_grep /app/closure/imbalance_ledger.rs 'saturating_add' 'sum skew stub'
}

install_patches() {
  cat > /app/manifest/trial_digest.rs <<'ORACLE_TRIAL_DIGEST'
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
ORACLE_TRIAL_DIGEST
  cat > /app/alpha/beta_norm.rs <<'ORACLE_BETA_NORM'
use serde_json::Value;

pub fn normalize_rows(rows: &mut Vec<Value>) {
    rows.sort_by(|a, b| {
        a["ts"].as_u64().unwrap_or(0)
            .cmp(&b["ts"].as_u64().unwrap_or(0))
            .then_with(|| a["seq"].as_u64().unwrap_or(0).cmp(&b["seq"].as_u64().unwrap_or(0)))
    });
    let mut best: std::collections::HashMap<(String, String), Value> = std::collections::HashMap::new();
    for row in rows.drain(..) {
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
    rows.extend(best.into_values());
    rows.sort_by(|a, b| {
        a["ts"].as_u64().unwrap_or(0)
            .cmp(&b["ts"].as_u64().unwrap_or(0))
            .then_with(|| a["seq"].as_u64().unwrap_or(0).cmp(&b["seq"].as_u64().unwrap_or(0)))
    });
}
ORACLE_BETA_NORM
  cat > /app/stratify/bucket_key.rs <<'ORACLE_BUCKET_KEY'
use serde_json::Value;

pub fn bucket_key(factors: &Value) -> Result<String, String> {
    let obj = factors.as_object().ok_or("factors object")?;
    let mut map = serde_json::Map::new();
    let mut keys: Vec<&String> = obj.keys().collect();
    keys.sort();
    for k in keys {
        map.insert(k.clone(), obj[k].clone());
    }
    serde_json::to_string(&serde_json::Value::Object(map)).map_err(|e| e.to_string())
}
ORACLE_BUCKET_KEY
  cat > /app/blocks/permuted_assign.rs <<'ORACLE_PERMUTED_ASSIGN'
use sha2::{Digest, Sha256};

pub fn block_seed(stratum_id: &str, trial_id: &str, seed_salt: &str) -> u64 {
    let preimage = format!("{trial_id}|{stratum_id}|{seed_salt}");
    let digest = Sha256::digest(preimage.as_bytes());
    u64::from_be_bytes(digest[0..8].try_into().unwrap())
}

pub fn permute_block(arms: &[String], block_size: usize, seed: u64) -> Vec<String> {
    let mut slots: Vec<String> = Vec::new();
    let per = block_size / arms.len().max(1);
    for arm in arms {
        for _ in 0..per {
            slots.push(arm.clone());
        }
    }
    while slots.len() < block_size {
        slots.push(arms[slots.len() % arms.len()].clone());
    }
    let mut state = seed;
    for i in (1..slots.len()).rev() {
        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
        let j = (state as usize) % (i + 1);
        slots.swap(i, j);
    }
    slots
}
ORACLE_PERMUTED_ASSIGN
  cat > /app/ceilings/limit_gate.rs <<'ORACLE_LIMIT_GATE'
use std::collections::HashMap;

pub fn active_site_counts(history: &[(String, String, bool)]) -> HashMap<String, u32> {
    let mut counts: HashMap<String, u32> = HashMap::new();
    for (site, _subject, active) in history {
        if *active {
            *counts.entry(site.clone()).or_insert(0) += 1;
        }
    }
    counts
}

pub fn venues_at_cap(counts: &HashMap<String, u32>, caps: &HashMap<String, u32>) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for (site, cap) in caps {
        if counts.get(site).copied().unwrap_or(0) >= *cap {
            out.push(site.clone());
        }
    }
    out.sort();
    out
}
ORACLE_LIMIT_GATE
  cat > /app/closure/imbalance_ledger.rs <<'ORACLE_IMBALANCE_LEDGER'
use sha2::{Digest, Sha256};

pub fn max_skew(rows: &[(u32, u32)]) -> u32 {
    rows.iter().map(|(a, b)| a.abs_diff(*b)).max().unwrap_or(0)
}

pub fn closure_digest(trial_id: &str, protocol_digest: &str, max_skew: u32, run_id: u32) -> String {
    let preimage = format!("{trial_id}|{protocol_digest}|{max_skew}|{run_id}");
    hex::encode(Sha256::digest(preimage.as_bytes()))
}
ORACLE_IMBALANCE_LEDGER
}

postflight() {
  require_grep /app/manifest/trial_digest.rs 'protocol_version' 'digest includes version'
  require_grep /app/alpha/beta_norm.rs '\.then_with\(\|\|.*\["seq"\]' 'ts-seq sort'
  require_grep /app/blocks/permuted_assign.rs 'trial_id\}\|' 'trial seed preimage'
  require_grep /app/ceilings/limit_gate.rs 'if \*active' 'active-only cap counts'
  require_grep /app/closure/imbalance_ledger.rs 'abs_diff' 'absolute skew'
}

preflight_stubs
install_patches
postflight
