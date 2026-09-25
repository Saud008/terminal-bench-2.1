use crate::c7_u9norm;
use crate::types::{ClinkerWindow, Config, FuelBatch};
use std::fs;
use std::io::Write;
use std::path::Path;

pub fn bind_fuel_clinker(
    cfg: &Config,
    run_id: &str,
    fuel_path: &Path,
    clinker_path: &Path,
    kiln_id: &str,
) -> Result<(), String> {
    let fuel_raw = fs::read_to_string(fuel_path).map_err(|e| e.to_string())?;
    let mut fuels = Vec::new();
    for line in fuel_raw.lines().skip(1) {
        let p: Vec<&str> = line.split(',').collect();
        let mass: f64 = p[2].parse().map_err(|_| "bad mass")?;
        let cv: f64 = p[3].parse().map_err(|_| "bad cv")?;
        let energy = c7_u9norm::kcal_mass_to_mj(mass, cv, cfg.kcal_to_mj);
        fuels.push(FuelBatch {
            batch_id: p[0].to_string(),
            fuel_name: p[1].to_string(),
            mass_kg: mass,
            cv_kcal_kg: cv,
            start_ts: p[4].parse().map_err(|_| "bad start")?,
            end_ts: p[5].parse().map_err(|_| "bad end")?,
            energy_mj: energy,
        });
    }
    let clinker_raw = fs::read_to_string(clinker_path).map_err(|e| e.to_string())?;
    let mut clinker = Vec::new();
    for line in clinker_raw.lines().skip(1) {
        let p: Vec<&str> = line.split(',').collect();
        clinker.push(ClinkerWindow {
            window_id: p[0].to_string(),
            batch_id: p[1].to_string(),
            clinker_t: p[2].parse().map_err(|_| "bad t")?,
            start_ts: p[3].parse().map_err(|_| "bad start")?,
            end_ts: p[4].parse().map_err(|_| "bad end")?,
        });
    }
    let out = format!("{}/{}.json", cfg.fuel_buffer_dir, run_id);
    let body = serde_json::json!({
        "run_id": run_id,
        "kiln_id": kiln_id,
        "fuel_batches": fuels,
        "clinker_windows": clinker,
    });
    fs::write(&out, serde_json::to_string_pretty(&body).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    Ok(())
}
