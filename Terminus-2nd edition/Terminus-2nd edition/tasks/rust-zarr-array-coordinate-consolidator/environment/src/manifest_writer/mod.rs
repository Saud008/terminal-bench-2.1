use crate::manifest_read::CompressorSpec;
use crate::row_stage::read_staging_snapshot;
use std::fs;
use std::path::Path;

#[derive(serde::Serialize)]
pub struct ExportedArray {
    pub name: String,
    pub shape: Vec<u64>,
    pub chunks: Vec<u64>,
    pub missing_chunks: Vec<String>,
    pub transform_ok: bool,
    pub compressor_fingerprint: String,
    pub coordinate_span: std::collections::BTreeMap<String, [f64; 2]>,
}

#[derive(serde::Serialize)]
pub struct Totals {
    pub array_count: u32,
    pub expected_chunks: u64,
    pub missing_chunks: u64,
}

#[derive(serde::Serialize)]
pub struct ConsolidatedManifest {
    pub version: u32,
    pub arrays: Vec<ExportedArray>,
    pub totals: Totals,
}

pub fn write_consolidated_manifest(staging_path: &Path, out_path: &Path) -> Result<(), String> {
    let staged = read_staging_snapshot(staging_path)?;
    let mut arrays = Vec::new();
    let mut expected_sum = 0u64;
    let mut missing_sum = 0u64;
    for row in &staged {
        expected_sum += row.expected_chunk_count;
        missing_sum += row.present_chunk_count;
        arrays.push(ExportedArray {
            name: row.array_name.clone(),
            shape: row.shape.clone(),
            chunks: row.chunks.clone(),
            missing_chunks: row.missing_chunk_keys.clone(),
            transform_ok: row.transform_ok,
            compressor_fingerprint: row.compressor_fingerprint.clone(),
            coordinate_span: row.coordinate_span.clone(),
        });
        let _ = CompressorSpec {
            id: row.compressor_fingerprint.clone(),
            level: 0,
            shuffle: 0,
        };
    }
    arrays.sort_by(|a, b| a.name.cmp(&b.name));
    let manifest = ConsolidatedManifest {
        version: 1,
        arrays,
        totals: Totals {
            array_count: staged.len() as u32,
            expected_chunks: expected_sum,
            missing_chunks: missing_sum,
        },
    };
    let json = serde_json::to_string_pretty(&manifest).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{json}
")).map_err(|e| e.to_string())
}
