pub mod cost;
pub mod fixed;
pub mod graph;
pub mod ingest;
pub mod model;
pub mod pathfind;
pub mod seed;
pub mod validate;

use crate::model::{PathExport, ValidateExport};
use std::path::Path;

pub fn run_validate(mesh_path: &Path, seed: u64) -> Result<ValidateExport, String> {
    let mesh = ingest::load_mesh(mesh_path)?;
    Ok(validate::validate_mesh(&mesh, seed))
}

pub fn run_path(mesh_path: &Path, seed: u64, from: &str, to: &str) -> Result<PathExport, String> {
    let mesh = ingest::load_mesh(mesh_path)?;
    pathfind::find_path(&mesh, seed, from, to)
}
