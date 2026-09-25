use crate::registry_aaguid;
use crate::replay_cred;
use crate::policy_uv;
use crate::cache_batch;
use crate::attest_model::{
    Config, PolicyFile, TrustDecision, TrustReport, TrustSummary,
};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

fn trust_rank(level: &str) -> u8 {
    match level {
        "rejected" => 0,
        "untrusted" => 1,
        _ => 2,
    }
}

pub fn build_report(cfg: &Config, batch: &str) -> Result<TrustReport, String> {
    let snap = cache_batch::read_snapshot(&cfg.transcript_cache_path)?;
    if snap.batch_id != batch {
        return Err("batch mismatch".into());
    }
    let active = cache_batch::read_active_policy(cfg)?;
    let policy = load_policy(&cfg.policy_dir, &active.policy_name)?;
    let reg = registry_aaguid::load_registry(&crate::metadata_path(cfg))?;
    let ids: Vec<String> = snap.rows.iter().map(|r| r.credential_id.clone()).collect();
    let dups = replay_cred::duplicate_ids(&ids);
    let mut decisions = Vec::new();
    let mut summary = TrustSummary {
        trusted: 0,
        untrusted: 0,
        rejected: 0,
        dedupe_blocked: 0,
    };
    for (idx, row) in snap.rows.iter().enumerate() {
        let mut reasons = Vec::new();
        let mut level = "trusted".to_string();
        if !row.chain_ok {
            reasons.push("chain_invalid".into());
            level = "rejected".to_string();
        }
        if !policy.allowed_formats.contains(&row.attestation_format) {
            reasons.push("format_blocked".into());
            level = "rejected".to_string();
        }
        if !row.metadata_hit {
            reasons.push("unknown_aaguid".into());
            level = "untrusted".to_string();
        }
        if !policy_uv::uv_satisfied(&policy, row.uv) {
            reasons.push("uv_policy".into());
            level = "rejected".to_string();
        }
        if row.sign_count < policy.min_sign_count {
            reasons.push("sign_count_low".into());
            level = "rejected".to_string();
        }
        if policy.reject_duplicate_credential_id && dups.contains(&row.credential_id) {
            let count_before = ids.iter().take(idx + 1).filter(|x| *x == &row.credential_id).count();
            if count_before > 1 {
                reasons.push("duplicate_credential".into());
                level = "rejected".to_string();
                summary.dedupe_blocked += 1;
            }
        }
        if let Some(entry) = registry_aaguid::lookup(&reg, &row.aaguid) {
            let root = row.cert_chain.last().map(|c| c.subject_fp.as_str()).unwrap_or("");
            if root != entry.trust_anchor_fp {
                reasons.push("anchor_mismatch".into());
                if level == "trusted" {
                    level = "untrusted".to_string();
                }
            }
        }
        match level.as_str() {
            "trusted" => summary.trusted += 1,
            "untrusted" => summary.untrusted += 1,
            _ => summary.rejected += 1,
        }
        decisions.push(TrustDecision {
            credential_id: row.credential_id.clone(),
            aaguid: row.aaguid.clone(),
            trust_level: level,
            reasons,
            sign_count: row.sign_count,
        });
    }
    decisions.sort_by(|a, b| {
        trust_rank(&a.trust_level)
            .cmp(&trust_rank(&b.trust_level))
            .then(a.credential_id.cmp(&b.credential_id))
    });
    let mut rep = TrustReport {
        batch_id: batch.to_string(),
        policy_name: active.policy_name.clone(),
        decisions,
        summary,
        audit_digest: String::new(),
    };
    rep.audit_digest = audit_digest(&rep);
    Ok(rep)
}

fn load_policy(dir: &str, name: &str) -> Result<PolicyFile, String> {
    let path = Path::new(dir).join(format!("{name}.json"));
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn audit_digest(rep: &TrustReport) -> String {
    let decision_ids: Vec<&str> = rep.decisions.iter().map(|d| d.credential_id.as_str()).collect();
    let mut map = serde_json::Map::new();
    map.insert("batch_id".into(), serde_json::Value::String(rep.batch_id.clone()));
    map.insert(
        "decision_ids".into(),
        serde_json::Value::Array(
            decision_ids
                .into_iter()
                .map(|id| serde_json::Value::String(id.to_string()))
                .collect(),
        ),
    );
    map.insert(
        "policy_name".into(),
        serde_json::Value::String(rep.policy_name.clone()),
    );
    map.insert(
        "rejected".into(),
        serde_json::Value::Number(rep.summary.rejected.into()),
    );
    map.insert(
        "dedupe_blocked".into(),
        serde_json::Value::Number(rep.summary.dedupe_blocked.into()),
    );
    map.insert(
        "trusted".into(),
        serde_json::Value::Number(rep.summary.trusted.into()),
    );
    map.insert(
        "untrusted".into(),
        serde_json::Value::Number(rep.summary.untrusted.into()),
    );
    let raw = serde_json::to_string(&serde_json::Value::Object(map)).unwrap_or_default();
    hex::encode(Sha256::digest(raw.as_bytes()))
}
