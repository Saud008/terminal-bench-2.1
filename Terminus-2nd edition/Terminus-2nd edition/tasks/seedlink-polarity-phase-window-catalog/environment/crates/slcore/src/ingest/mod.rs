use std::path::Path;

use crate::error::SlError;
use crate::staging::{build_phase_staging, PhaseStaging};

pub fn ingest_snippet(source: &Path, stem: &str) -> Result<PhaseStaging, SlError> {
    build_phase_staging(source, stem)
}
