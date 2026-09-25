use std::path::Path;

use crate::model::SettlementReport;
use crate::pipeline;

pub fn run_replay(
    season_path: &Path,
    events_path: &Path,
    seasons_dir: &Path,
    output_path: &Path,
) -> Result<SettlementReport, String> {
    pipeline::run_replay(season_path, events_path, seasons_dir, output_path)
}
