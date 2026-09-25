use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use crate::staging;
use crate::types::ExportRollup;
use crate::DEFAULT_GENERATION_PATH;

pub fn run_export(
    _seed: &str,
    bundle_id: &str,
    _fixture_root: &str,
    output: &str,
) -> Result<(), String> {
    let snap = staging::read_stage()?;
    if snap.bundle_id != bundle_id {
        return Err("bundle mismatch".into());
    }
    let gen_text = fs::read_to_string(DEFAULT_GENERATION_PATH).map_err(|e| e.to_string())?;
    let gen_file: crate::types::GenerationFile =
        serde_json::from_str(&gen_text).map_err(|e| e.to_string())?;
    if snap.merge_generation == 0 || snap.merge_generation != gen_file.merge_generation {
        return Err("merge generation gate".into());
    }
    let table = snap
        .merged_counters
        .as_ref()
        .ok_or_else(|| "merge required".to_string())?;
    let mut estimates = BTreeMap::new();
    for key in &snap.query_keys {
        let est = crate::sketch::estimate(
            table,
            key,
            snap.hash_seed,
            &snap.namespace_salt,
        );
        estimates.insert(key.clone(), est);
    }
    let rollup = ExportRollup {
        bundle_id: snap.bundle_id.clone(),
        merge_generation: snap.merge_generation,
        overlap_ms: snap.overlap_ms,
        estimates,
        epsilon_lineage: snap.epsilon_lineage.clone(),
        stage_digest: staging::stage_digest(&snap)?,
    };
    let path = Path::new(output);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(path, serde_json::to_string_pretty(&rollup).unwrap()).map_err(|e| e.to_string())
}
