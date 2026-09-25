pub mod precedence;

use crate::types::{SampleBarcode, StagingFile};

pub fn effective_samples(staging: &StagingFile, lane_id: &str) -> Vec<SampleBarcode> {
    precedence::resolve_effective_samples(staging, lane_id)
}
