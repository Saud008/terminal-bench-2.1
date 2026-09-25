use crate::ax_bind::{axis_span, load_axes_catalog, shape_matches_axes};
use crate::key_ledger::{absent_chunk_keys, expected_count, present_count};
use crate::fp_seal::seal_compressor;
use crate::manifest_read::load_manifest_bundle;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StagedRow {
    pub array_name: String,
    pub shape: Vec<u64>,
    pub chunks: Vec<u64>,
    pub expected_chunk_count: u64,
    pub present_chunk_count: u64,
    pub missing_chunk_keys: Vec<String>,
    pub transform_ok: bool,
    pub compressor_fingerprint: String,
    pub coordinate_span: std::collections::BTreeMap<String, [f64; 2]>,
}

pub fn build_staging_snapshot(manifest_dir: &Path, axes_path: &Path, staging_path: &Path) -> Result<(), String> {
    let manifests = load_manifest_bundle(manifest_dir).map_err(|_| "manifest read failed".to_string())?;
    let axes = load_axes_catalog(axes_path).map_err(|_| "axes read failed".to_string())?;
    let mut rows = Vec::new();
    for manifest in manifests {
        let axis = axes.get(&manifest.name).ok_or_else(|| format!("missing axes for {}", manifest.name))?;
        let mut span = std::collections::BTreeMap::new();
        for dim in &axis.dims {
            if let Some(coord) = axis.coordinates.get(dim) {
                let (lo, hi) = axis_span(coord);
                span.insert(dim.clone(), [lo, hi]);
            }
        }
        rows.push(StagedRow {
            array_name: manifest.name.clone(),
            shape: manifest.shape.clone(),
            chunks: manifest.chunks.clone(),
            expected_chunk_count: expected_count(&manifest),
            present_chunk_count: present_count(&manifest),
            missing_chunk_keys: absent_chunk_keys(&manifest),
            transform_ok: shape_matches_axes(&manifest.shape, axis),
            compressor_fingerprint: seal_compressor(&manifest.compressor),
            coordinate_span: span,
        });
    }
    rows.sort_by(|a, b| b.array_name.cmp(&a.array_name));
    let json = serde_json::to_string_pretty(&rows).map_err(|e| e.to_string())?;
    fs::write(staging_path, format!("{json}
")).map_err(|e| e.to_string())
}

pub fn read_staging_snapshot(path: &Path) -> Result<Vec<StagedRow>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}
