use crate::tan_pixsky;
use crate::types::{Config, DetectionRow, MatchRow, WcsCache};
use std::fs;
use std::io::Write;

fn sep_arcsec(ra1: f64, dec1: f64, ra2: f64, dec2: f64) -> f64 {
    let r = std::f64::consts::PI / 180.0;
    let (a1, d1, a2, d2) = (ra1 * r, dec1 * r, ra2 * r, dec2 * r);
    let cos_d = d1.sin() * d2.sin() + d1.cos() * d2.cos() * (a1 - a2).cos();
    let cos_d = cos_d.clamp(-1.0, 1.0);
    cos_d.acos().to_degrees() * 3600.0
}

pub fn crossmatch_run(cfg: &Config, run_id: &str, wcs: &WcsCache) -> Result<(), String> {
    let det_path = format!("{}/{}.jsonl", cfg.detection_buffer_dir, run_id);
    let raw = fs::read_to_string(&det_path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let _hdr = lines.next();
    let mut detections = Vec::new();
    for line in lines {
        detections.push(serde_json::from_str::<DetectionRow>(line).map_err(|e| e.to_string())?);
    }
    let tol = crate::match_arcsec_override().unwrap_or(cfg.match_arcsec_default);
    let tol_deg = tol;
    let out_path = format!("{}/{}.jsonl", cfg.xmatch_buffer_dir, run_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    writeln!(
        f,
        r#"{{"run_id":"{}","tolerance_arcsec":{}}}"#,
        run_id,
        tol
    )
    .map_err(|e| e.to_string())?;
    for det in detections {
        let (pra, pdec) = tan_pixsky::pixel_to_sky(wcs, det.x_pixel, det.y_pixel);
        let sep = sep_arcsec(pra, pdec, det.ra_deg, det.dec_deg);
        if sep <= tol_deg {
            let dra = (pra - det.ra_deg) * 3600.0;
            let ddec = (pdec - det.dec_deg) * 3600.0;
            let masked = det.mask_bit != 0 || det.catalog_mask != 0;
            let row = MatchRow {
                source_id: det.source_id.clone(),
                separation_arcsec: sep,
                delta_ra_arcsec: dra,
                delta_dec_arcsec: ddec,
                masked,
            };
            let js = serde_json::to_string(&row).map_err(|e| e.to_string())?;
            writeln!(f, "{js}").map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}
