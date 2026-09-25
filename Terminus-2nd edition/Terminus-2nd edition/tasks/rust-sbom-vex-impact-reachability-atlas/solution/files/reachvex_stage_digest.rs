use std::fs;
use std::path::Path;

use serde_json::{json, Value};

use crate::types::{AtlasStage, RunSeqState};
use crate::RUN_SEQ_PATH;

pub fn load_stage(path: &str) -> Result<AtlasStage, String> {
    let raw = fs::read_to_string(path).map_err(|e| format!("read stage: {e}"))?;
    serde_json::from_str(&raw).map_err(|e| format!("parse stage: {e}"))
}

pub fn write_stage(path: &str, stage: &AtlasStage) -> Result<(), String> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let pretty = serde_json::to_string_pretty(stage).map_err(|e| e.to_string())?;
    fs::write(path, format!("{pretty}\n")).map_err(|e| e.to_string())
}

pub fn staging_digest(stage: &AtlasStage) -> String {
    let packages: Vec<serde_json::Value> = stage
        .packages
        .iter()
        .map(|p| {
            serde_json::json!({
                "norm_purl": p.norm_purl,
                "canonical_raw": p.canonical_raw,
                "name": p.name,
                "version": p.version,
            })
        })
        .collect();
    let edges: Vec<serde_json::Value> = stage
        .edges
        .iter()
        .map(|e| {
            serde_json::json!({
                "from": e.from,
                "to": e.to,
                "edge_kind": e.edge_kind,
            })
        })
        .collect();
    let mut vex_rows: Vec<serde_json::Value> = Vec::new();
    for v in &stage.vex {
        let mut row = serde_json::json!({
            "statement_id": v.statement_id,
            "product_purl": v.product_purl,
            "vuln_id": v.vuln_id,
            "status": v.status,
            "updated_at": v.updated_at,
        });
        if let Some(exp) = &v.expires_at {
            row["expires_at"] = serde_json::json!(exp);
        }
        vex_rows.push(row);
    }
    let body = serde_json::json!({
        "bundle_id": stage.bundle_id,
        "packages": packages,
        "edges": edges,
        "vex": vex_rows,
    });
    let bytes = serde_json::to_string(&body).unwrap_or_default();
    hash_bytes(bytes.as_bytes())
}

fn hash_bytes(data: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    hex::encode(Sha256::digest(data))
}

pub fn bump_run_seq(fingerprint: &str) -> Result<u64, String> {
    let mut state = if Path::new(RUN_SEQ_PATH).exists() {
        let raw = fs::read_to_string(RUN_SEQ_PATH).map_err(|e| e.to_string())?;
        serde_json::from_str::<RunSeqState>(&raw).unwrap_or(RunSeqState {
            run_seq: 0,
            last_fingerprint: String::new(),
        })
    } else {
        RunSeqState {
            run_seq: 0,
            last_fingerprint: String::new(),
        }
    };
    if state.last_fingerprint == fingerprint {
        return Ok(state.run_seq);
    }
    state.run_seq += 1;
    state.last_fingerprint = fingerprint.to_string();
    let pretty = serde_json::to_string_pretty(&state).map_err(|e| e.to_string())?;
    fs::write(RUN_SEQ_PATH, format!("{pretty}\n")).map_err(|e| e.to_string())?;
    Ok(state.run_seq)
}

pub fn canonical_digest_input(stage: &AtlasStage) -> Value {
    json!({
        "bundle_id": stage.bundle_id,
        "packages": stage.packages,
        "edges": stage.edges,
        "vex": stage.vex,
    })
}
