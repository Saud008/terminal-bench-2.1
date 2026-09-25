use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use sha2::{Digest, Sha256};

use crate::ledger::replay;
use crate::types::{KeyEntry, PolicyDoc, RevocationRow, StagingDoc, WitnessRow};

pub fn load_bundle_dir(bundle_dir: &str, staging_path: &str) -> Result<(), String> {
    let bundle = Path::new(bundle_dir);
    if !bundle.is_dir() {
        return Err(format!("bundle dir missing: {bundle_dir}"));
    }
    let policy: PolicyDoc = read_json(bundle.join("policy.json"))?;
    let keys_map: BTreeMap<String, KeyEntry> = read_json(bundle.join("keys.json"))?;
    let revocations = read_revocations(bundle.join("revocations.jsonl"))?;
    let artifact_path = bundle.join(&policy.artifact_file);
    let artifact_digest = hash_file(&artifact_path)?;
    let mut incoming = load_witnesses(bundle.join("witnesses"))?;
    for w in &mut incoming {
        w.artifact_digest = artifact_digest.clone();
    }

    let existing = if Path::new(staging_path).exists() {
        Some(read_json::<StagingDoc>(staging_path)?)
    } else {
        None
    };
    let ingest_seq = replay::next_ingest_seq(existing.as_ref());
    let prior_witnesses = existing.as_ref().map(|s| s.witnesses.as_slice()).unwrap_or(&[]);
    let (witnesses, replay_deduped) = replay::merge_witnesses(prior_witnesses, &incoming);

    let staging = StagingDoc {
        ingest_seq,
        bundle_dir: bundle_dir.to_string(),
        policy,
        artifact_digest,
        keys: keys_map,
        revocations,
        witnesses,
        replay_deduped,
    };
    write_json(staging_path, &staging)
}

fn hash_file(path: &Path) -> Result<String, String> {
    let bytes = fs::read(path).map_err(|e| format!("artifact read: {e}"))?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

fn load_witnesses(dir: std::path::PathBuf) -> Result<Vec<WitnessRow>, String> {
    let mut rows = Vec::new();
    for entry in fs::read_dir(&dir).map_err(|e| format!("witnesses dir: {e}"))? {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) == Some("json") {
            rows.push(read_json(path)?);
        }
    }
    rows.sort_by(|a: &WitnessRow, b: &WitnessRow| a.witness_id.cmp(&b.witness_id));
    Ok(rows)
}

fn read_revocations(path: std::path::PathBuf) -> Result<Vec<RevocationRow>, String> {
    if !path.exists() {
        return Ok(Vec::new());
    }
    let text = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    let mut rows = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        rows.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(rows)
}

fn read_json<T: serde::de::DeserializeOwned>(path: impl AsRef<Path>) -> Result<T, String> {
    let text = fs::read_to_string(path.as_ref()).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn write_json(path: &str, value: &impl serde::Serialize) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    fs::write(path, text + "\n").map_err(|e| e.to_string())
}
