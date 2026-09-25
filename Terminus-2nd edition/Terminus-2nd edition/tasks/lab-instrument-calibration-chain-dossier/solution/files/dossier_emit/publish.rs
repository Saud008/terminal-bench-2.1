use lab_calibration_chain::chain_schema::{DossierReport, DossierRow, DossierSummary, StagedInstrument};
use lab_calibration_chain::register_store;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn build_dossier(
    register_path: &str,
    batch_id: &str,
) -> Result<DossierReport, String> {
    let inst = register_store::load_active(register_path, batch_id)?;
    let generation = register_store::read_generation(register_path, batch_id);
    let mut rows = vec![dossier_row_from_instrument(&inst)];
    rows.sort_by(|a, b| {
        b.severity
            .cmp(&a.severity)
            .then_with(|| a.instrument_id.cmp(&b.instrument_id))
    });
    let summary = summarize(&rows);
    let digest = dossier_digest(batch_id, generation, &rows, &summary);
    Ok(DossierReport {
        batch_id: batch_id.to_string(),
        fuse_generation: generation,
        rows,
        summary,
        dossier_digest: digest,
    })
}

fn dossier_row_from_instrument(inst: &StagedInstrument) -> DossierRow {
    let severity = inst.out_of_tolerance_count * 10
        + if !inst.cert_valid { 5 } else { 0 }
        + if !inst.authorized_tech { 3 } else { 0 };
    DossierRow {
        instrument_id: inst.instrument_id.clone(),
        severity,
        out_of_tolerance_count: inst.out_of_tolerance_count,
        cert_valid: inst.cert_valid,
        authorized_tech: inst.authorized_tech,
        expanded_uncertainty: inst.expanded_uncertainty,
    }
}

fn summarize(rows: &[DossierRow]) -> DossierSummary {
    DossierSummary {
        instrument_count: rows.len() as i32,
        invalid_cert_count: rows.iter().filter(|r| !r.cert_valid).count() as i32,
        unauthorized_tech_count: rows.iter().filter(|r| !r.authorized_tech).count() as i32,
        oot_channel_total: rows.iter().map(|r| r.out_of_tolerance_count).sum(),
    }
}

pub fn dossier_digest(
    batch_id: &str,
    generation: i32,
    rows: &[DossierRow],
    summary: &DossierSummary,
) -> String {
    let mut parts: Vec<String> = rows
        .iter()
        .map(|r| format!("{}:{}:{}", r.instrument_id, r.severity, r.out_of_tolerance_count))
        .collect();
    parts.sort();
    let body = format!(
        "{}|{}|{}|{}|{}|{}",
        batch_id,
        generation,
        summary.instrument_count,
        summary.invalid_cert_count,
        summary.unauthorized_tech_count,
        parts.join(";")
    );
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())[..16].to_string()
}

pub fn write_dossier(path: &Path, report: &DossierReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let body = serde_json::to_string_pretty(report).map_err(|e| e.to_string())?;
    fs::write(path, body).map_err(|e| e.to_string())
}
