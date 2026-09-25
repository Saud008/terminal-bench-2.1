use serde_json::Value;
use std::fs;
use std::path::Path;

pub fn bundle_load(scenario_root: &Path, scenario: &str, run_id: &str, work: &Path) -> Result<(), String> {
    let base = scenario_root.join(scenario);
    let meta: Value = serde_json::from_str(
        &fs::read_to_string(base.join("scenario.json")).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    let mut indices = Vec::new();
    let idx_dir = base.join("indices");
    if idx_dir.exists() {
        let mut paths: Vec<_> = fs::read_dir(&idx_dir)
            .map_err(|e| e.to_string())?
            .filter_map(|e| e.ok())
            .map(|e| e.path())
            .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("json"))
            .collect();
        paths.sort();
        for p in paths {
            let sid = p.file_stem().and_then(|s| s.to_str()).unwrap_or("idx").to_string();
            let raw = fs::read_to_string(&p).map_err(|e| e.to_string())?;
            indices.push(serde_json::json!({"source_id": sid, "rows": serde_json::from_str::<Value>(&raw).map_err(|e| e.to_string())?}));
        }
    }
    let body = serde_json::json!({
        "scenario": scenario,
        "run_id": run_id,
        "meta": meta,
        "indices": indices,
    });
    fs::write(work.join(format!("{run_id}-load.json")), serde_json::to_string_pretty(&body).unwrap())
        .map_err(|e| e.to_string())?;
    Ok(())
}
