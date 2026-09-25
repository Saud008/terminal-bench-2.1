use crate::admit::decision::{self, Decision};
use crate::parse::header_scan::ParsedFile;
use crate::policy::pin_set::PinPolicy;
use std::fs;
use std::path::Path;

struct Totals {
    admitted: usize,
    denied: usize,
    malformed: usize,
}

/// Export path: seal the admission ledger JSON from staged witness rows.
pub fn seal_ledger(path: &Path, files: &[ParsedFile], policy: &PinPolicy) -> Result<(), String> {
    export_ledger(path, files, policy)
}

pub fn export_ledger(path: &Path, files: &[ParsedFile], policy: &PinPolicy) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let mut decisions: Vec<Decision> = files.iter().map(|f| decision::decide(f, policy)).collect();
    decisions.sort_by(|a, b| a.file_id.cmp(&b.file_id));

    let admitted = decisions.iter().filter(|d| d.verdict == "admit").count();
    let denied = decisions.iter().filter(|d| d.verdict == "deny").count();
    let malformed = decisions
        .iter()
        .filter(|d| d.reasons.iter().any(|r| r == "malformed_header"))
        .count();

    let totals = Totals {
        admitted,
        denied,
        malformed,
    };

    let parts: Vec<String> = decisions.iter().map(|d| d.to_json()).collect();
    let mut body = format!(
        "{{\"decisions\":[{}],\"totals\":{{\"admitted\":{},\"denied\":{},\"malformed\":{}}}}}",
        parts.join(","),
        totals.admitted,
        totals.denied,
        totals.malformed
    );
    body.push('\n');
    fs::write(path, body).map_err(|e| e.to_string())
}
