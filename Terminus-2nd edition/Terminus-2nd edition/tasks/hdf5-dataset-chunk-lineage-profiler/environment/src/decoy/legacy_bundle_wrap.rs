use crate::hdclp_types::LineageReport;
use std::path::Path;

/// Batch-job wrapper retained off the ingest and export hot path.
pub fn wrap_export(_state: &Path, report: &LineageReport) -> Result<String, String> {
  let json = serde_json::to_string(report).map_err(|e| format!("wrap: {e}"))?;
  Ok(format!("WRAPPED:{json}"))
}
