use crate::arc_cache;
use crate::plant_schema::{BreachRow, SafetyReport, SafetySummary};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

use std::cmp::{Greater, Less};

pub fn build_safety(ledger_path: &str, plant_id: &str) -> Result<SafetyReport, String> {
    let ledger = arc_cache::read_ledger(ledger_path)?;
    if ledger.plant_id != plant_id {
        return Err("plant mismatch".into());
    }
    let mut breaches: Vec<BreachRow> = ledger
        .chemicals
        .iter()
        .filter(|c| c.total_dose_mg > c.max_dose_mg)
        .map(|c| {
            let severity = ((c.total_dose_mg - c.max_dose_mg) / c.max_dose_mg) * 100.0;
            BreachRow {
                chem_id: c.chem_id.clone(),
                total_dose_mg: c.total_dose_mg,
                max_dose_mg: c.max_dose_mg,
                severity_pct: severity,
            }
        })
        .collect();
    breaches.sort_by(|a, b| {
        match a.severity_pct.partial_cmp(&b.severity_pct) {
            Some(Less) => Less,
            Some(Greater) => Greater,
            _ => a.chem_id.cmp(&b.chem_id),
        }
    });
    let summary = SafetySummary {
        plant_id: plant_id.to_string(),
        shift: ledger.shift.clone(),
        chemical_count: ledger.chemicals.len() as u32,
        breach_count: breaches.len() as u32,
        max_severity_pct: breaches.first().map(|b| b.severity_pct).unwrap_or(0.0),
    };
    let digest = breach_atlas_seal(&summary);
    Ok(SafetyReport {
        plant_id: plant_id.to_string(),
        shift: ledger.shift,
        rows: breaches,
        summary,
        breach_atlas_seal: digest,
    })
}

pub fn write_safety(path: &Path, report: &SafetyReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(report).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}

fn breach_atlas_seal(summary: &SafetySummary) -> String {
    let body = serde_json::json!({
        "breach_count": summary.breach_count,
        "chemical_count": summary.chemical_count,
        "max_severity_pct": summary.max_severity_pct,
        "plant_id": summary.plant_id,
        "shift": summary.shift,
    });
    let raw = serde_json::to_string(&body).unwrap_or_default();
    let mut hasher = Sha256::new();
    hasher.update(raw.as_bytes());
    hex::encode(hasher.finalize())
}
