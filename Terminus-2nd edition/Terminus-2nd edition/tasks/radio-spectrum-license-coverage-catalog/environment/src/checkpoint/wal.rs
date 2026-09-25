use crate::catalog_schema::{BundleFile, WalLicenseRow, GrantWalFrame};
use std::fs;
use std::path::Path;

pub fn write_snapshot(
    path: &str,
    seed: &str,
    bundle: &str,
    bf: &BundleFile,
) -> Result<(), String> {
    let prev = read_generation(path);
    let licenses = materialize_licenses(bf);
    let snap = GrantWalFrame {
        load_generation: prev,
        seed: seed.to_string(),
        bundle: bundle.to_string(),
        as_of_date: bf.as_of_date.clone(),
        licenses,
        transmitters: bf.transmitters.clone(),
        exclusions: bf.exclusions.clone(),
        bands: bf.bands.clone(),
    };
    write_json(path, &snap)
}

pub fn read_snapshot(path: &str) -> Result<GrantWalFrame, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn validate_seed_bundle(snap: &GrantWalFrame, seed: &str, bundle: &str) -> Result<(), String> {
    if snap.seed != seed || snap.bundle != bundle {
        return Err("wal seed/bundle mismatch".into());
    }
    Ok(())
}

fn materialize_licenses(bf: &BundleFile) -> Vec<WalLicenseRow> {
    bf.licenses
        .iter()
        .map(|lic| WalLicenseRow {
            license_id: lic.license_id.clone(),
            holder: lic.holder.clone(),
            band_id: lic.band_id.clone(),
            priority: lic.priority,
            renewal_date: lic.renewal_date.clone(),
            lat_min: lic.area.lat_min,
            lat_max: lic.area.lat_max,
            lon_min: lic.area.lon_min,
            lon_max: lic.area.lon_max,
        })
        .collect()
}

fn read_generation(path: &str) -> u64 {
    read_snapshot(path)
        .map(|s| s.load_generation)
        .unwrap_or(0)
}

fn write_json(path: &str, v: &GrantWalFrame) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(v).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
