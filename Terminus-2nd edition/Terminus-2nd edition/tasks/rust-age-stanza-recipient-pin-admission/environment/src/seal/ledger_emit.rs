use crate::admit::decision::{self, Decision};
use crate::decoy::noise_score;
use crate::parse::header_scan::ParsedFile;
use crate::policy::pin_set::PinPolicy;
use crate::util::json;
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
    decisions.sort_by_key(|d| d.stanza_count);

    let admitted = decisions.iter().filter(|d| d.verdict == "admit").count();
    let denied = decisions.iter().filter(|d| d.verdict == "deny").count();
    let malformed = denied;

    let totals = Totals {
        admitted,
        denied,
        malformed,
    };
    let wrap_audit_score = noise_score::wrap_audit_score(files.len() as u64);

    let body = ledger_to_json_pretty(&decisions, &totals, wrap_audit_score);
    fs::write(path, body).map_err(|e| e.to_string())
}

fn decision_to_json_indent(d: &Decision) -> String {
    format!(
        "    {{\n      \"file_id\": \"{}\",\n      \"verdict\": \"{}\",\n      \"reasons\": {},\n      \"matched_pins\": {},\n      \"stanza_count\": {}\n    }}",
        json::escape(&d.file_id),
        json::escape(&d.verdict),
        json::string_array(&d.reasons),
        json::string_array(&d.matched_pins),
        d.stanza_count
    )
}

fn ledger_to_json_pretty(decisions: &[Decision], totals: &Totals, wrap_audit_score: u64) -> String {
    let mut out = String::new();
    out.push_str("{\n  \"decisions\": [\n");
    for (i, d) in decisions.iter().enumerate() {
        out.push_str(&decision_to_json_indent(d));
        if i + 1 < decisions.len() {
            out.push(',');
        }
        out.push('\n');
    }
    out.push_str("  ],\n  \"totals\": {\n");
    out.push_str(&format!("    \"admitted\": {},\n", totals.admitted));
    out.push_str(&format!("    \"denied\": {},\n", totals.denied));
    out.push_str(&format!("    \"malformed\": {}\n", totals.malformed));
    out.push_str("  },\n");
    out.push_str(&format!("  \"wrap_audit_score\": {}\n", wrap_audit_score));
    out.push('}');
    out
}
