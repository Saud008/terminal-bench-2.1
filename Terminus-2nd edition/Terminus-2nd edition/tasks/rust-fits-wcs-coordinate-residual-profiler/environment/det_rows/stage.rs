use crate::types::{Config, DetectionRow, WcsCache};
use std::fs;
use std::io::Write;
use std::path::Path;

pub fn buffer_detections(
    cfg: &Config,
    run_id: &str,
    wcs: &WcsCache,
    catalog: &Path,
    detections: &Path,
) -> Result<(), String> {
    let cat_lines: Vec<_> = fs::read_to_string(catalog)
        .map_err(|e| e.to_string())?
        .lines()
        .filter(|l| !l.starts_with("source_id"))
        .map(|s| s.to_string())
        .collect();
    let mut catalog_map = std::collections::BTreeMap::new();
    for line in cat_lines {
        let p: Vec<_> = line.split(',').collect();
        if p.len() < 5 {
            continue;
        }
        catalog_map.insert(
            p[0].to_string(),
            (
                p[1].parse::<f64>().unwrap_or(0.0),
                p[2].parse::<f64>().unwrap_or(0.0),
                p[3].parse::<f64>().unwrap_or(2000.0),
                p[4].parse::<u32>().unwrap_or(0),
            ),
        );
    }
    let out_path = format!("{}/{}.jsonl", cfg.detection_buffer_dir, run_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    writeln!(
        f,
        r#"{{"run_id":"{}","wcs_revision":{}}}"#,
        run_id,
        wcs.wcs_revision
    )
    .map_err(|e| e.to_string())?;
    let det_raw = fs::read_to_string(detections).map_err(|e| e.to_string())?;
    for line in det_raw.lines().skip(1) {
        let p: Vec<_> = line.split(',').collect();
        if p.len() < 5 {
            continue;
        }
        let sid = p[0].to_string();
        let (ra, dec, epoch, cat_mask) = catalog_map.get(&sid).cloned().unwrap_or((0.0, 0.0, 2000.0, 0));
        let row = DetectionRow {
            source_id: sid,
            x_pixel: p[1].parse().unwrap_or(0.0),
            y_pixel: p[2].parse().unwrap_or(0.0),
            flux: p[3].parse().unwrap_or(0.0),
            mask_bit: p[4].parse().unwrap_or(0),
            ra_deg: ra,
            dec_deg: dec,
            epoch_year: epoch,
            catalog_mask: cat_mask,
        };
        let js = serde_json::to_string(&row).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
