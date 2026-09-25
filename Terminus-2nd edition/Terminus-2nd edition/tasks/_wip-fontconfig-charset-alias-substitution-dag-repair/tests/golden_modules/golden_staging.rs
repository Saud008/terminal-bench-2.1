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
    let current = fs::read_to_string(COMPILE_SEQ_PATH)
        .ok()
        .and_then(|s| s.trim().parse::<u64>().ok())
        .unwrap_or(0);
    let next = current + 1;
    fs::create_dir_all("/app/state").map_err(|e| FcError::Io(e.to_string()))?;
    fs::write(COMPILE_SEQ_PATH, format!("{next}\n")).map_err(|e| FcError::Io(e.to_string()))?;
    Ok(next)
}

pub fn bump_compile_seq(seq: u64) -> Result<()> {
    fs::create_dir_all("/app/state").map_err(|e| FcError::Io(e.to_string()))?;
    fs::write(COMPILE_SEQ_PATH, format!("{seq}\n")).map_err(|e| FcError::Io(e.to_string()))
}

pub fn graph_hash(cfg: &FontConfig, base: &Path, inject: Option<&Path>) -> String {
    let inject_key = inject
        .map(|p| p.display().to_string())
        .unwrap_or_default();
    let canonical = serde_json::to_string(cfg).unwrap_or_default();
    let payload = format!("{}\n{inject_key}\n{canonical}", base.display());
    let mut h: u64 = 5381;
    for b in payload.bytes() {
        h = h.wrapping_mul(33).wrapping_add(u64::from(b));
    }
    format!("{h:016x}")
}

pub fn build_stage(
    cfg: FontConfig,
    base: &Path,
    inject: Option<&Path>,
) -> Result<CompiledStage> {
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
