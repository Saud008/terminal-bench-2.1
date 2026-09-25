use std::fs;

use crate::crypto::threshold;
use crate::snapshot::link;
use crate::types::{MetadataVerify, SignedDoc, VerifyResult};

pub fn verify_rotation(staging_path: &str, epoch: u64, verify_path: &str) -> Result<(), String> {
    let staging = crate::staging::load_staging(staging_path)?;
    let meta_dir = fs::read_to_string("/app/state/last-ingest-dir.txt")
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|_| "/app/data/metadata".into());

    let root = read_doc(&meta_dir, "root.json")?;
    let targets = read_doc(&meta_dir, "targets.json")?;
    let snapshot = read_doc(&meta_dir, "snapshot.json")?;

    let bias: u64 = std::env::var("TB3_EPOCH_BIAS")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);
    let effective_epoch = epoch.saturating_add(bias);

    let root_root = staging.root_role.clone();
    let targets_role = staging.targets_role.clone();
    let root_keyids = staging.root_role.keyids.clone();

    let (root_ok, root_valid, root_exp, root_reuse) = threshold::verify_doc(
        &root.signed,
        &root.signatures,
        &root_root,
        &staging.keys,
        effective_epoch,
        &[],
    );
    let (targets_ok, targets_valid, targets_exp, targets_reuse) = threshold::verify_doc(
        &targets.signed,
        &targets.signatures,
        &targets_role,
        &staging.keys,
        effective_epoch,
        &root_keyids,
    );
    let (snap_ok, snap_valid, snap_exp, snap_reuse) = threshold::verify_doc(
        &snapshot.signed,
        &snapshot.signatures,
        &targets_role,
        &staging.keys,
        effective_epoch,
        &root_keyids,
    );

    let snapshot_link_ok = link::snapshot_link_ok(&staging);
    let rotation_ok = root_ok && targets_ok && snap_ok && snapshot_link_ok;

    let result = VerifyResult {
        epoch: effective_epoch,
        rotation_ok,
        snapshot_link_ok,
        metadata: vec![
            MetadataVerify {
                role: "root".into(),
                threshold_met: root_ok,
                valid_signatures: root_valid,
                expired_keyids: root_exp,
                reuse_violations: root_reuse,
            },
            MetadataVerify {
                role: "targets".into(),
                threshold_met: targets_ok,
                valid_signatures: targets_valid,
                expired_keyids: targets_exp,
                reuse_violations: targets_reuse,
            },
            MetadataVerify {
                role: "snapshot".into(),
                threshold_met: snap_ok,
                valid_signatures: snap_valid,
                expired_keyids: snap_exp,
                reuse_violations: snap_reuse,
            },
        ],
    };

    write_verify(verify_path, &result)
}

fn read_doc(dir: &str, name: &str) -> Result<SignedDoc, String> {
    let path = std::path::Path::new(dir).join(name);
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn write_verify(path: &str, result: &VerifyResult) -> Result<(), String> {
    let parent = std::path::Path::new(path).parent().unwrap_or(std::path::Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(result).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
