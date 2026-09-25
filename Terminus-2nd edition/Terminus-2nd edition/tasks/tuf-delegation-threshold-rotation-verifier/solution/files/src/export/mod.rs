use std::fs;

use sha2::{Digest, Sha256};

use crate::canonical;
use crate::delegation::paths;
use crate::types::{DecisionRow, RejectedRow, ReportFile, VerifyResult};

pub fn export_report(
    staging_path: &str,
    verify_path: &str,
    report_path: &str,
    rejected_path: &str,
) -> Result<(), String> {
    let staging = crate::staging::load_staging(staging_path)?;
    let verify = load_verify(verify_path)?;
    let mut decisions = Vec::new();

    for path in staging.targets.keys() {
        let (allowed, delegation, reason) = if verify.rotation_ok {
            paths::target_allowed(path, &staging.delegations)
        } else {
            (false, None, "rotation_failed".into())
        };
        decisions.push(DecisionRow {
            path: path.clone(),
            allowed,
            delegation,
            reason,
        });
    }
    decisions.sort_by(|a, b| a.path.cmp(&b.path));

    let digest = audit_digest(&decisions)?;
    let report = ReportFile {
        epoch: verify.epoch,
        rotation_ok: verify.rotation_ok,
        decisions: decisions.clone(),
        audit_digest: digest,
    };

    write_report(report_path, &report)?;
    write_rejected(rejected_path, &decisions)
}

fn load_verify(path: &str) -> Result<VerifyResult, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn audit_digest(decisions: &[DecisionRow]) -> Result<String, String> {
    let value = serde_json::to_value(decisions).map_err(|e| e.to_string())?;
    let text = canonical::canonical_string(&value)?;
    let mut hasher = Sha256::new();
    hasher.update(text.as_bytes());
    Ok(hex::encode(hasher.finalize()))
}

fn write_report(path: &str, report: &ReportFile) -> Result<(), String> {
    let parent = std::path::Path::new(path).parent().unwrap_or(std::path::Path::new("/app/output"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let data = serde_json::to_string_pretty(report).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}

fn write_rejected(path: &str, decisions: &[DecisionRow]) -> Result<(), String> {
    let parent = std::path::Path::new(path).parent().unwrap_or(std::path::Path::new("/app/output"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let mut lines = Vec::new();
    for row in decisions {
        if !row.allowed {
            let rej = RejectedRow {
                path: row.path.clone(),
                reason: row.reason.clone(),
                delegation: row.delegation.clone(),
            };
            lines.push(serde_json::to_string(&rej).map_err(|e| e.to_string())?);
        }
    }
    fs::write(path, format!("{}\n", lines.join("\n"))).map_err(|e| e.to_string())
}
