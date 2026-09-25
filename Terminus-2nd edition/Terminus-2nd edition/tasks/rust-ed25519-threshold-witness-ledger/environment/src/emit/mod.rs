use std::fs;

use sha2::{Digest, Sha256};

use crate::types::{LedgerDoc, LedgerWitnessRow, StagingDoc, VerifyResult};

pub fn emit_release_ledger(
    staging_path: &str,
    verdict_path: &str,
    ledger_path: &str,
) -> Result<(), String> {
    let staging: StagingDoc = read_json(staging_path)?;
    let verify: VerifyResult = read_json(verdict_path)?;
    let witnesses: Vec<LedgerWitnessRow> = verify
        .witnesses
        .iter()
        .map(|o| {
            let w = staging
                .witnesses
                .iter()
                .find(|x| x.witness_id == o.witness_id)
                .unwrap();
            LedgerWitnessRow {
                witness_id: o.witness_id.clone(),
                signer_keyid: w.signer_keyid.clone(),
                epoch: w.epoch,
                prior_witness_id: w
                    .prior_witness_id
                    .clone()
                    .unwrap_or_else(|| "none".to_string()),
                counts_toward_quorum: o.counts_toward_quorum,
            }
        })
        .collect();

    let ledger_digest = reference_ledger_digest(&staging.bundle_dir, &witnesses);
    let doc = LedgerDoc {
        release_id: staging.policy.release_id.clone(),
        artifact_digest: staging.artifact_digest.clone(),
        epoch: verify.epoch,
        quorum_met: verify.quorum_met,
        valid_witness_count: verify.valid_witness_count,
        threshold: verify.threshold,
        ingest_seq: staging.ingest_seq,
        witnesses,
        ledger_digest,
    };
    write_json(ledger_path, &doc)
}

pub fn reference_ledger_digest(
    artifact_digest: &str,
    rows: &[LedgerWitnessRow],
) -> String {
    let mut witness_blob: Vec<serde_json::Value> = rows
        .iter()
        .map(|r| {
            serde_json::json!({
                "witness_id": r.witness_id,
                "signer_keyid": r.signer_keyid,
                "epoch": r.epoch,
                "prior_witness_id": r.prior_witness_id,
                "counts_toward_quorum": r.counts_toward_quorum,
            })
        })
        .collect();
    witness_blob.sort_by(|a, b| {
        a["witness_id"]
            .as_str()
            .unwrap()
            .cmp(b["witness_id"].as_str().unwrap())
    });
    let payload = serde_json::json!({
        "artifact_digest": artifact_digest,
        "witnesses": witness_blob,
    });
    let canonical = serde_json::to_string(&payload).unwrap_or_default();
    let mut hasher = Sha256::new();
    hasher.update(canonical.as_bytes());
    hex::encode(hasher.finalize())
}

fn read_json<T: serde::de::DeserializeOwned>(path: &str) -> Result<T, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn write_json(path: &str, value: &impl serde::Serialize) -> Result<(), String> {
    if let Some(parent) = std::path::Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    fs::write(path, text + "\n").map_err(|e| e.to_string())
}
