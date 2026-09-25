use crate::run_buffer;
use crate::types::{AuditPassport, AuditPassportActive, Config};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn run_correlate(cfg: &Config, seed: &str, survey: &str) -> Result<(), String> {
    let buf = run_buffer::read_buffer(&cfg.buffer_path)?;
    run_buffer::validate_seed_survey(&buf, seed, survey)?;
    let audit_run_id = scoped_run_id(seed, survey, buf.correlate_seq);
    let active = AuditPassportActive {
        seed: seed.to_string(),
        survey: survey.to_string(),
        audit_run_id,
        correlate_seq: buf.correlate_seq,
    };
    write_passport(&cfg.audit_passport_path, active)
}

pub fn read_active(cfg: &Config) -> Result<AuditPassportActive, String> {
    let passport = read_passport(&cfg.audit_passport_path)?;
    passport.active.ok_or_else(|| "no active audit passport row".into())
}

fn scoped_run_id(seed: &str, survey: &str, seq: u64) -> String {
    let mut hasher = Sha256::new();
    hasher.update(format!("{seed}:{survey}:{seq}"));
    let digest = hex::encode(hasher.finalize());
    format!("audit-{}", &digest[..12])
}

fn read_passport(path: &str) -> Result<AuditPassport, String> {
    if !Path::new(path).exists() {
        return Ok(AuditPassport { active: None });
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn write_passport(path: &str, active: AuditPassportActive) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let passport = AuditPassport {
        active: Some(active),
    };
    let data = serde_json::to_string_pretty(&passport).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
