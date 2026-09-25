//! Pass eligibility filter — map imaging requests to orbit pass windows.

use crate::tasking_types::{ImagingRequest, PassWindow};

pub fn eligible_passes(req: &ImagingRequest, windows: &[PassWindow]) -> Vec<PassWindow> {
    windows
        .iter()
        .filter(|p| p.cells.iter().any(|c| c == &req.cell_id))
        .cloned()
        .collect()
}
