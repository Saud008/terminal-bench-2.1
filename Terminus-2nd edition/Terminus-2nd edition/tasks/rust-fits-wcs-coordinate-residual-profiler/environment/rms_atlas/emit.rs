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
    let n = matches.len().max(1) as f64;
    let rms_ra = (matches.iter().map(|m| m.delta_ra_arcsec.powi(2)).sum::<f64>() / n).sqrt();
    let rms_dec = (matches.iter().map(|m| m.delta_dec_arcsec.powi(2)).sum::<f64>() / n).sqrt();
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
