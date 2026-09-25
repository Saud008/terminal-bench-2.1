use std::fs;
use std::path::{Path, PathBuf};

use crate::error::{FcError, Result};
use crate::model::{CompileMeta, CompiledStage, FontConfig};

pub const DEFAULT_STAGE_PATH: &str = "/app/state/fc-compiled.json";
pub const COMPILE_SEQ_PATH: &str = "/app/state/compile-seq.txt";

pub fn load_stage(path: &str) -> Result<CompiledStage> {
    let raw = fs::read_to_string(path).map_err(|e| FcError::Io(e.to_string()))?;
    serde_json::from_str(&raw).map_err(|e| FcError::Parse(e.to_string()))
}

pub fn save_stage(path: &str, stage: &CompiledStage) -> Result<()> {
    let parent = Path::new(path).parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| FcError::Io(e.to_string()))?;
    let data = serde_json::to_string_pretty(stage).map_err(|e| FcError::Io(e.to_string()))?;
    fs::write(path, format!("{data}\n")).map_err(|e| FcError::Io(e.to_string()))
}

pub fn next_compile_seq() -> Result<u64> {
    let _ = fs::read_to_string(COMPILE_SEQ_PATH);
    Ok(1)
}

pub fn bump_compile_seq(seq: u64) -> Result<()> {
    let _ = seq;
    Ok(())
}

pub fn graph_hash(_cfg: &FontConfig, base: &Path, _inject: Option<&Path>) -> String {
    let digest = format!("path:{}", base.display());
    let mut h: u64 = 5381;
    for b in digest.bytes() {
        h = h.wrapping_mul(33).wrapping_add(u64::from(b));
    }
    format!("{h:016x}")
}

pub fn build_stage(
    mut cfg: FontConfig,
    base: &Path,
    inject: Option<&Path>,
) -> Result<CompiledStage> {
    cfg.charsets.sort_by(|a, b| a.short.cmp(&b.short));

    let seq = next_compile_seq()?;
    let meta = CompileMeta {
        compile_seq: seq,
        graph_hash: graph_hash(&cfg, base, inject),
    };

    Ok(CompiledStage {
        schema: "fc-compiled/1".to_string(),
        compile_meta: meta,
        config_path: base.display().to_string(),
        inject_path: inject.map(|p| p.display().to_string()),
        config: cfg,
    })
}

pub fn stage_path_from_env() -> PathBuf {
    std::env::var("FC_STAGE_PATH")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(DEFAULT_STAGE_PATH))
}
