use crate::m04::{load_index, IndexRow};
use crate::m06::{snapshot_digest, QueryRow, SnapshotDoc};
use crate::m06::write_snapshot;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn analyze_run(work: &Path, state: &Path, run_id: &str) -> Result<(), String> {
    let bundle_path = work.join(format!("{run_id}-load.json"));
    let raw = fs::read_to_string(&bundle_path).map_err(|e| e.to_string())?;
    let doc: Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let meta = &doc["meta"];
    let scenario = doc["scenario"].as_str().unwrap_or("").to_string();
    let target_python = meta["target_python"].as_str().unwrap_or("3.10").to_string();
    let target_platform = meta["target_platform"].as_str().unwrap_or("linux").to_string();
    let target_arch = meta["target_arch"].as_str().unwrap_or("x86_64").to_string();
    let mut packages: Vec<IndexRow> = Vec::new();
    if let Some(arr) = doc["indices"].as_array() {
        for block in arr {
            let sid = block["source_id"].as_str().unwrap_or("primary");
            if let Some(rows) = block["rows"].as_array() {
                for r in rows {
                    let mut row: IndexRow = serde_json::from_value(r.clone()).map_err(|e| e.to_string())?;
                    row.source_id = Some(sid.to_string());
                    packages.push(row);
                }
            }
        }
    }
    let fp_raw = serde_json::to_string(&doc["indices"]).unwrap_or_default();
    let index_fingerprint = hex::encode(Sha256::digest(fp_raw.as_bytes()));
    let queries: Vec<QueryRow> = meta["queries"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .map(|q| QueryRow {
            package: q["package"].as_str().unwrap_or("").to_string(),
            spec: q["spec"].as_str().unwrap_or("").to_string(),
        })
        .collect();
    let digest = snapshot_digest(
        run_id,
        &index_fingerprint,
        &target_python,
        &target_platform,
        &target_arch,
        &packages,
    );
    let snap_doc = SnapshotDoc {
        run_id: run_id.to_string(),
        scenario,
        target_python,
        target_platform,
        target_arch,
        index_fingerprint,
        packages,
        queries,
        snapshot_digest: digest,
    };
    write_snapshot(&state.join("whres-snapshot.json"), &snap_doc)
}

mod hex {
    pub fn encode(bytes: impl AsRef<[u8]>) -> String {
        bytes.as_ref().iter().map(|b| format!("{b:02x}")).collect()
    }
}
