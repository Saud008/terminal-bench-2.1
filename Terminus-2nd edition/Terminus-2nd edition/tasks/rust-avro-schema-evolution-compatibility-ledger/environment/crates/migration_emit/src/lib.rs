use pair_eval::PairResult;
use serde::Serialize;
use ledger_ingest::read_staging;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize)]
pub struct SubjectRisk {
    pub subject: String,
    pub writer_fingerprint: String,
    pub reader_fingerprint: String,
    pub compatible: bool,
    pub risk_level: String,
    pub violation_count: u32,
    pub violations: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct RiskTotals {
    pub pair_count: u32,
    pub compatible_count: u32,
    pub high_risk_count: u32,
    pub critical_risk_count: u32,
}

#[derive(Debug, Serialize)]
pub struct MigrationRiskReport {
    pub subjects: Vec<SubjectRisk>,
    pub totals: RiskTotals,
}

pub fn export_report(staging_path: &Path, out_path: &Path) -> Result<(), String> {
    let rows = read_staging(staging_path)?;
    let mut subjects = Vec::new();
    let mut compatible_count = 0u32;
    let mut high_risk = 0u32;
    let mut critical_risk = 0u32;
    for row in rows {
        let risk = classify_risk(&row);
        if row.compatible {
            compatible_count += 1;
        }
        if risk == "high" {
            high_risk += 1;
        }
        if risk == "critical" {
            critical_risk += 1;
        }
        subjects.push(SubjectRisk {
            subject: row.subject.clone(),
            writer_fingerprint: row.writer_fingerprint.clone(),
            reader_fingerprint: row.reader_fingerprint.clone(),
            compatible: row.compatible,
            risk_level: risk,
            violation_count: row.violations.len() as u32,
            violations: row.violations.clone(),
        });
    }
    subjects.sort_by(|a, b| a.subject.cmp(&b.subject));
    let report = MigrationRiskReport {
        totals: RiskTotals {
            pair_count: subjects.len() as u32,
            compatible_count,
            high_risk_count: high_risk,
            critical_risk_count: critical_risk,
        },
        subjects,
    };
    let json = serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{json}
")).map_err(|e| e.to_string())
}

fn classify_risk(row: &PairResult) -> String {
    if row.compatible {
        return "high".into();
    }
    if row.violations.iter().any(|v| v == "logical_types") {
        return "critical".into();
    }
    if row.violations.len() >= 2 {
        return "high".into();
    }
    "medium".into()
}
