pub mod cost;
pub mod fixed;
pub mod graph;
pub mod ingest;
pub mod model;
pub mod pathfind;
pub mod seed;
pub mod validate;

#[path = "../../../scout_decoy/astar.rs"]
#[allow(dead_code)]
mod scout_decoy;

use crate::model::{MeshBundle, PathExport, ValidateExport};
use serde_json::json;
use std::fs;
use std::path::Path;

fn write_staging_snapshot(mesh: &MeshBundle, seed: u64) -> Result<(), String> {
    let dir = Path::new("/app/state/playfield-staging");
    fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    let path = dir.join(format!("{}-{}.json", mesh.mesh_id, seed));
    let snap = json!({
        "mesh_id": mesh.mesh_id,
        "seed": seed,
        "cell_count": mesh.cells.len(),
        "edge_count": mesh.edges.len(),
        "portal_count": mesh.portals.len(),
        "offmesh_count": mesh.offmesh.len(),
    });
    let raw = serde_json::to_string_pretty(&snap).map_err(|e| e.to_string())?;
    fs::write(path, raw + "\n").map_err(|e| e.to_string())
}

pub fn run_validate(mesh_path: &Path, seed: u64) -> Result<ValidateExport, String> {
    let mesh = ingest::load_mesh(mesh_path)?;
    write_staging_snapshot(&mesh, seed)?;
    Ok(validate::validate_mesh(&mesh, seed))
}

pub fn run_path(mesh_path: &Path, seed: u64, from: &str, to: &str) -> Result<PathExport, String> {
    let mesh = ingest::load_mesh(mesh_path)?;
    write_staging_snapshot(&mesh, seed)?;
    pathfind::find_path(&mesh, seed, from, to)
}
