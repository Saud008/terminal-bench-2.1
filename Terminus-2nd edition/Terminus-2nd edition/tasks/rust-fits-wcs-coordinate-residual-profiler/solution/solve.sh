# Oracle solve — task identity rust-fits-wcs-coordinate-residual-profiler token 5a4c8ea9
#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > /app/fcard_lex/parse.rs <<'EOF'
use std::collections::BTreeMap;

pub fn parse_cards(text: &str) -> Result<BTreeMap<String, String>, String> {
    let mut out = BTreeMap::new();
    for line in text.lines() {
        if line.trim().is_empty() || line.starts_with('#') {
            continue;
        }
        if line.len() < 8 {
            continue;
        }
        let key = line.get(0..8).unwrap_or("").trim().to_string();
        let rest = line.get(8..).unwrap_or("").trim_start();
        let mut val = if rest.starts_with('=') {
            rest[1..].trim().to_string()
        } else {
            rest.to_string()
        };
        if val.starts_with('\'') && val.ends_with('\'') {
            val = val[1..val.len() - 1].to_string();
        }
        out.insert(key, val);
    }
    Ok(out)
}
EOF

cat > /app/wmeter_hdr/extract.rs <<'EOF'
use crate::types::WcsCache;
use std::collections::BTreeMap;

fn parse_f64(map: &BTreeMap<String, String>, key: &str) -> Result<f64, String> {
    map.get(key)
        .ok_or_else(|| format!("missing {key}"))
        .and_then(|v| v.parse().map_err(|_| format!("bad float {key}")))
}

pub fn extract_wcs(run_id: &str, cards: &BTreeMap<String, String>) -> Result<WcsCache, String> {
    let epoch = parse_f64(cards, "EPOCH").unwrap_or(2000.0);
    let crval = [
        parse_f64(cards, "CRVAL1")?,
        parse_f64(cards, "CRVAL2")?,
    ];
    let crpix = [parse_f64(cards, "CRPIX1")?, parse_f64(cards, "CRPIX2")?];
    let cd = [
        [parse_f64(cards, "CD1_1")?, parse_f64(cards, "CD1_2")?],
        [parse_f64(cards, "CD2_1")?, parse_f64(cards, "CD2_2")?],
    ];
    let prev = std::fs::read_to_string(format!("/app/state/wcs-cache/{}.json", run_id))
        .ok()
        .and_then(|raw| serde_json::from_str::<WcsCache>(&raw).ok())
        .map(|w| w.wcs_revision)
        .unwrap_or(0);
    Ok(WcsCache {
        run_id: run_id.to_string(),
        header_epoch: epoch,
        ctype: [
            cards.get("CTYPE1").cloned().unwrap_or_else(|| "RA---TAN".into()),
            cards.get("CTYPE2").cloned().unwrap_or_else(|| "DEC--TAN".into()),
        ],
        crval,
        crpix,
        cd,
        wcs_revision: prev + 1,
    })
}
EOF

cat > /app/tan_pixsky/project.rs <<'EOF'
use crate::types::WcsCache;

pub fn pixel_to_sky(wcs: &WcsCache, x: f64, y: f64) -> (f64, f64) {
    let xi = x - wcs.crpix[0];
    let eta = y - wcs.crpix[1];
    let ra = wcs.crval[0] + wcs.cd[0][0] * xi + wcs.cd[0][1] * eta;
    let dec = wcs.crval[1] + wcs.cd[1][0] * xi + wcs.cd[1][1] * eta;
    (ra, dec)
}
EOF

sed -i 's/catalog_mask: 0,/catalog_mask: cat_mask,/' /app/det_rows/stage.rs

cat > /app/gc_match/match_engine.rs <<'EOF'
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
    let out_path = format!("{}/{}.jsonl", cfg.xmatch_buffer_dir, run_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    writeln!(f, r#"{{"run_id":"{}","tolerance_arcsec":{}}}"#, run_id, tol).map_err(|e| e.to_string())?;
    for det in detections {
        let (pra, pdec) = tan_pixsky::pixel_to_sky(wcs, det.x_pixel, det.y_pixel);
        let sep = sep_arcsec(pra, pdec, det.ra_deg, det.dec_deg);
        if sep <= tol {
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
EOF

cat > /app/rms_atlas/emit.rs <<'EOF'
use crate::types::{Config, MatchRow, ResidualAtlas};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn audit_digest(atlas: &ResidualAtlas) -> String {
    let mut ids: Vec<String> = atlas.matches.iter().map(|m| m.source_id.clone()).collect();
    ids.sort();
    let body = serde_json::json!({
        "match_count": atlas.match_count,
        "active_count": atlas.active_count,
        "source_ids": ids,
        "run_id": atlas.run_id,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}

pub fn build_atlas(cfg: &Config, run_id: &str) -> Result<ResidualAtlas, String> {
    let path = format!("{}/{}.jsonl", cfg.xmatch_buffer_dir, run_id);
    let raw = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let _hdr = lines.next();
    let mut matches = Vec::new();
    for line in lines {
        matches.push(serde_json::from_str::<MatchRow>(line).map_err(|e| e.to_string())?);
    }
    matches.sort_by(|a, b| a.source_id.cmp(&b.source_id));
    let active: Vec<_> = matches.iter().filter(|m| !m.masked).collect();
    let n = active.len().max(1) as f64;
    let rms_ra = if active.is_empty() {
        0.0
    } else {
        (active.iter().map(|m| m.delta_ra_arcsec.powi(2)).sum::<f64>() / n).sqrt()
    };
    let rms_dec = if active.is_empty() {
        0.0
    } else {
        (active.iter().map(|m| m.delta_dec_arcsec.powi(2)).sum::<f64>() / n).sqrt()
    };
    let atlas = ResidualAtlas {
        run_id: run_id.to_string(),
        match_count: matches.len() as u32,
        active_count: active.len() as u32,
        rms_ra_arcsec: rms_ra,
        rms_dec_arcsec: rms_dec,
        matches,
        audit_digest: String::new(),
    };
    let digest = audit_digest(&atlas);
    Ok(ResidualAtlas {
        audit_digest: digest,
        ..atlas
    })
}

pub fn write_atlas(cfg: &Config, run_id: &str, output: &Path) -> Result<(), String> {
    let atlas = build_atlas(cfg, run_id)?;
    fs::write(output, serde_json::to_string_pretty(&atlas).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())
}
EOF

/usr/local/cargo/bin/cargo generate-lockfile
/usr/local/cargo/bin/cargo build --release --locked
