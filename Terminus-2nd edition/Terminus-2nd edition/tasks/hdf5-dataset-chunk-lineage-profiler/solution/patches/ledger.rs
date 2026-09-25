use crate::s5pipe::fchain;
use crate::s5pipe::oscale;
use crate::facetgraph;
use crate::s5pipe::amerg;
use crate::s5pipe::btally;
use crate::parse::catalog;
use crate::s5pipe::ixwalk;
use crate::hdclp_types::{
    ChunkRecord, CompressionTotals, StagingSnapshot, total_chunks,
};
use std::fs;
use std::path::{Path, PathBuf};

fn catalog_dir_for_ingest(catalog_dir: &Path) -> PathBuf {
    if let Ok(override_dir) = std::env::var("TB3_BUNDLE") {
        PathBuf::from(override_dir)
    } else {
        catalog_dir.to_path_buf()
    }
}

pub fn run_ingest(catalog_dir: &Path, state_dir: &Path) -> Result<(), String> {
    fs::create_dir_all(state_dir).map_err(|e| format!("mkdir state: {e}"))?;
    let bundle = catalog_dir_for_ingest(catalog_dir);
    let cat = catalog::load_catalog(&bundle)?;
    let mut chunks = Vec::new();
    let mut totals = CompressionTotals::default();

    for ds in &cat.datasets {
        let ndims = ds.dims.len();
        let index_blob = catalog::load_index_bytes(&bundle, &ds.path)?;
        if !facetgraph::facet_count_ok(ndims, ndims) {
            return Err(format!("facet dimension mismatch for {}", ds.path));
        }
        let entries = ixwalk::parse_index(&index_blob, ndims)?;
        let expected = total_chunks(&ds.dims, &ds.chunk_dims) as usize;
        if entries.len() != expected {
            return Err(format!(
                "chunk count mismatch for {}: index {} expected {}",
                ds.path,
                entries.len(),
                expected
            ));
        }
        let eff = amerg::effective_attrs(ds);
        let mask_bytes = if let Some(rel) = &ds.mask_rel {
            catalog::load_mask_bytes(&bundle, rel)?
        } else {
            vec![]
        };
        let cells_per_chunk: usize = ds
            .chunk_dims
            .iter()
            .product::<u64>() as usize;
        let ds_hash = fchain::filter_chain_hash(&ds.filters);

        for (i, entry) in entries.iter().enumerate() {
            let linear_origin =
                ixwalk::linear_to_origin(i as u32, &ds.dims, &ds.chunk_dims);
            let masked = if mask_bytes.is_empty() {
                entry.masked_cells
            } else {
                btally::count_masked(&mask_bytes, cells_per_chunk, ds.fill_value)
            };
            let labels = oscale::coord_labels(&entry.origin, &ds.chunk_dims, &eff);
            let consistent = oscale::coord_consistent(&linear_origin, &entry.origin, &labels);
            totals.total_payload_bytes += entry.payload_bytes as u64;
            totals.total_masked_cells += masked as u64;
            for f in &ds.filters {
                *totals.filter_usage.entry(f.clone()).or_insert(0) += 1;
            }
            chunks.push(ChunkRecord {
                dataset_path: ds.path.clone(),
                chunk_index: i as u32,
                origin: entry.origin.clone(),
                filter_chain_id: entry.filter_chain_id,
                filter_chain_hash: ds_hash.clone(),
                payload_bytes: entry.payload_bytes,
                masked_cells: masked,
                effective_attrs: eff.clone(),
                coord_labels: labels,
                coord_consistent: consistent,
            });
        }
    }

    let seq_path = state_dir.join("sequence.txt");
    let sequence = if seq_path.exists() {
        fs::read_to_string(&seq_path)
            .ok()
            .and_then(|s| s.trim().parse().ok())
            .unwrap_or(1)
            + 1
    } else {
        1
    };
    fs::write(&seq_path, sequence.to_string()).map_err(|e| format!("write sequence: {e}"))?;

    let snap = StagingSnapshot {
        version: 1,
        catalog_root: cat.root.clone(),
        sequence,
        chunks,
        compression_totals: totals,
    };
    let out = state_dir.join("staging.json");
    let json = serde_json::to_string_pretty(&snap).map_err(|e| format!("encode staging: {e}"))?;
    fs::write(&out, json).map_err(|e| format!("write staging: {e}"))?;
    Ok(())
}
