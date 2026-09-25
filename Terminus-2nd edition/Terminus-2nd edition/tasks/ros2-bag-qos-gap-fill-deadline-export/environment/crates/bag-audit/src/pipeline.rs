use std::path::Path;

use anyhow::Result;

use crate::bag::{gap, read};
use crate::export::sqlite;
use crate::qos::deadline;

pub fn run_audit(bag_dir: &Path, export: &Path, speed: f64, seed: u64) -> Result<()> {
    let (meta, raw) = read::load_bag(bag_dir)?;
    let filled = gap::fill_gaps(raw, seed);
    let misses = deadline::find_deadline_misses(&meta, &filled, speed, seed);
    sqlite::write_export(export, &filled, &misses)?;
    Ok(())
}
