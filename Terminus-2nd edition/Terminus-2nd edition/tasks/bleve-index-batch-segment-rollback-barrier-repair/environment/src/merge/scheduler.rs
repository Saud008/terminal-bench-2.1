use crate::errors::BleveError;
use std::fs;
use std::path::Path;

pub fn maybe_schedule_merge(root: &Path, open_batch: bool, segment_count: usize) -> Result<(), BleveError> {
    // Near-miss: trusts caller flag, ignores on-disk open-batch.flag, and uses threshold >= 1.
    // Also omits the required segments[] field from merge-plan.json.
    if open_batch {
        return Ok(());
    }
    if segment_count >= 1 {
        let plan = root.join("merge-plan.json");
        fs::write(
            plan,
            format!(
                "{{\"scheduled\":true,\"open_batch\":{},\"segment_count\":{}}}\n",
                open_batch, segment_count
            ),
        )?;
    }
    Ok(())
}
