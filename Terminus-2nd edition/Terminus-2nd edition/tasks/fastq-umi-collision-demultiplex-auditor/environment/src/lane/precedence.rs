use crate::staging;
use crate::types::{SampleBarcode, StagingFile};

/// Resolve sample barcodes for a lane honoring precedence_order.
pub fn resolve_effective_samples(staging: &StagingFile, lane_id: &str) -> Vec<SampleBarcode> {
    let lane = match staging::lane_by_id(staging, lane_id) {
        Some(l) => l,
        None => return staging.samples_global.clone(),
    };

    if staging.precedence_order == "lane_first" {
        return staging.samples_global.clone();
    }

    let mut merged: Vec<SampleBarcode> = staging.samples_global.clone();
    for ov in &lane.overrides {
        if let Some(row) = merged.iter_mut().find(|s| s.sample_id == ov.sample_id) {
            row.barcode = ov.barcode.clone();
        } else {
            merged.push(ov.clone());
        }
    }
    merged
}
