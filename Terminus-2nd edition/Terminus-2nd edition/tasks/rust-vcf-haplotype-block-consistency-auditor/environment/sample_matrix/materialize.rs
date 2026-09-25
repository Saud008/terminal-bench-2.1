use crate::types::{Config, SamplePhaseMatrix};
use crate::vcf_read;
use std::fs;
use std::path::{Path, PathBuf};

pub fn materialize_run(
    cfg: &Config,
    run_id: &str,
    vcf_path: &Path,
    manifest_path: &Path,
) -> Result<PathBuf, String> {
    let manifest = vcf_read::load_manifest(manifest_path)?;
    let variants = vcf_read::parse_vcf(vcf_path, &manifest)?;
    let sample_lineage = crate::manifest_lineage::ordered_sample_ids(&manifest);
    let matrix_path = PathBuf::from(&cfg.sample_matrix_dir).join(format!("{run_id}.json"));
    let prev_gen = if matrix_path.exists() {
        let prev: SamplePhaseMatrix =
            serde_json::from_str(&fs::read_to_string(&matrix_path).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
        prev.ingest_generation
    } else {
        0
    };
    let matrix = SamplePhaseMatrix {
        run_id: run_id.to_string(),
        profile: manifest.profile.clone(),
        ingest_generation: prev_gen,
        sample_lineage,
        variant_catalog: variants,
    };
    fs::create_dir_all(&cfg.sample_matrix_dir).map_err(|e| e.to_string())?;
    fs::write(
        &matrix_path,
        serde_json::to_string_pretty(&matrix).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    Ok(matrix_path)
}
