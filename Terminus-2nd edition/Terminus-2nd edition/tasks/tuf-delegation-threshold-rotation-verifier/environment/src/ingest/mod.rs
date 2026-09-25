use std::fs;
use std::path::Path;

use crate::types::{SignedDoc, StagingFile};
use serde_json::Value;

pub fn ingest_directory(dir: &str, staging_path: &str) -> Result<(), String> {
    let root = read_doc(dir, "root.json")?;
    let targets = read_doc(dir, "targets.json")?;
    let snapshot = read_doc(dir, "snapshot.json")?;

    let prev = crate::staging::load_staging(staging_path)
        .ok()
        .map(|s| s.ingest_seq)
        .unwrap_or(0);

    let staging = build_staging(&root, &targets, &snapshot, prev + 1)?;
    crate::staging::save_staging(staging_path, &staging)?;
    write_last_dir(dir)
}

fn write_last_dir(dir: &str) -> Result<(), String> {
    fs::write("/app/state/last-ingest-dir.txt", format!("{dir}\n")).map_err(|e| e.to_string())
}

fn read_doc(dir: &str, name: &str) -> Result<SignedDoc, String> {
    let path = Path::new(dir).join(name);
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn build_staging(
    root: &SignedDoc,
    targets: &SignedDoc,
    snapshot: &SignedDoc,
    ingest_seq: u64,
) -> Result<StagingFile, String> {
    let root_signed = &root.signed;
    let targets_signed = &targets.signed;
    let snapshot_signed = &snapshot.signed;

    let keys = parse_keys(root_signed.get("keys").ok_or("root keys missing")?)?;
    let root_role = parse_role(root_signed.get("roles").and_then(|r| r.get("root")).ok_or("root role")?)?;
    let targets_role = parse_role(root_signed.get("roles").and_then(|r| r.get("targets")).ok_or("targets role")?)?;
    let delegations = parse_delegations(targets_signed.get("delegations").ok_or("delegations")?)?;
    let target_map = parse_targets(targets_signed.get("targets").ok_or("targets map")?)?;

    Ok(StagingFile {
        ingest_seq,
        root_version: root_signed.get("version").and_then(|v| v.as_u64()).unwrap_or(0),
        targets_version: targets_signed.get("version").and_then(|v| v.as_u64()).unwrap_or(0),
        snapshot_version: snapshot_signed.get("version").and_then(|v| v.as_u64()).unwrap_or(0),
        keys,
        root_role,
        targets_role,
        delegations,
        targets: target_map,
        snapshot_targets_version: snapshot_signed
            .get("targets_version")
            .and_then(|v| v.as_u64())
            .unwrap_or(0),
    })
}

fn parse_keys(value: &Value) -> Result<std::collections::BTreeMap<String, crate::types::KeyEntry>, String> {
    let obj = value.as_object().ok_or("keys not object")?;
    let mut out = std::collections::BTreeMap::new();
    for (k, v) in obj {
        let entry: crate::types::KeyEntry = serde_json::from_value(v.clone()).map_err(|e| e.to_string())?;
        out.insert(k.clone(), entry);
    }
    Ok(out)
}

fn parse_role(value: &Value) -> Result<crate::types::RoleSpec, String> {
    serde_json::from_value(value.clone()).map_err(|e| e.to_string())
}

fn parse_delegations(value: &Value) -> Result<Vec<crate::types::DelegationRow>, String> {
    serde_json::from_value(value.clone()).map_err(|e| e.to_string())
}

fn parse_targets(value: &Value) -> Result<std::collections::BTreeMap<String, Value>, String> {
    let obj = value.as_object().ok_or("targets not object")?;
    let mut out = std::collections::BTreeMap::new();
    for (k, v) in obj {
        out.insert(k.clone(), v.clone());
    }
    Ok(out)
}
