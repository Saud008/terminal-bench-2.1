use crate::tasking_types::SlotAssignment;
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize)]
pub struct MatrixAuditMeta {
    pub run_token: String,
    pub row_count: u32,
    pub matrix_fingerprint: String,
}

fn row_csv(a: &SlotAssignment) -> String {
    format!(
        "{},{},{},{},{},{},{},{},{}",
        a.request_id,
        a.pass_id,
        a.orbit_id,
        a.cell_id,
        a.mode,
        a.setup_sec,
        a.effective_start_sec,
        a.effective_end_sec,
        a.cloud_composite
    )
}

pub fn write_plan_buffer(token: &str, rows: &mut [SlotAssignment]) -> Result<MatrixAuditMeta, String> {
    rows.sort_by(|a, b| {
        a.effective_start_sec
            .cmp(&b.effective_start_sec)
            .then_with(|| a.request_id.cmp(&b.request_id))
    });
    let csv_path = Path::new(crate::VAR_ROOT).join(format!("conflict-matrix-{token}.csv"));
    let mut body = String::from("request_id,pass_id,orbit_id,cell_id,mode,setup_sec,effective_start_sec,effective_end_sec,cloud_composite\n");
    for row in rows.iter() {
        body.push_str(&row_csv(row));
        body.push('\n');
    }
    fs::write(&csv_path, &body).map_err(|e| e.to_string())?;
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    let fp = format!("sha256:{:x}", hasher.finalize());
    let meta = MatrixAuditMeta {
        run_token: token.to_string(),
        row_count: rows.len() as u32,
        matrix_fingerprint: fp,
    };
    let meta_path = Path::new(crate::VAR_ROOT).join(format!("conflict-matrix-{token}.meta.json"));
    fs::write(&meta_path, serde_json::to_string_pretty(&meta).unwrap()).map_err(|e| e.to_string())?;
    Ok(meta)
}
