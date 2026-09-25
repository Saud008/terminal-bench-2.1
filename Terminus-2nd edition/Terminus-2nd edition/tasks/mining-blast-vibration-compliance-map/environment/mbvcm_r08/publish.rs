use crate::gain_curve;
use crate::jurisdiction;
use crate::parcel_mesh;
use crate::passport;
use crate::ppv_field;
use crate::run_buffer;
use crate::types::{Config, ExceedanceAtlas, ExceedanceRow, ExceedanceSummary};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn build_atlas(cfg: &Config, seed: &str, survey: &str) -> Result<ExceedanceAtlas, String> {
    let buf = run_buffer::read_buffer(&cfg.buffer_path)?;
    run_buffer::validate_seed_survey(&buf, seed, survey)?;
    let active = passport::read_active(cfg)?;
    if active.seed != seed || active.survey != survey {
        return Err("audit passport seed/survey mismatch".into());
    }
    let record = &buf.record;
    let mut sensors: BTreeMap<String, _> = BTreeMap::new();
    for s in &record.sensors {
        sensors.insert(s.sensor_id.clone(), s);
    }
    let mut properties: BTreeMap<String, _> = BTreeMap::new();
    for p in &record.properties {
        properties.insert(p.property_id.clone(), p);
    }
    let mut blasts: BTreeMap<String, _> = BTreeMap::new();
    for b in &record.blasts {
        blasts.insert(b.blast_id.clone(), b);
    }
    let mut rows = Vec::new();
    for reading in &record.readings {
        let blast = blasts.get(&reading.blast_id).ok_or("missing blast")?;
        let sensor = sensors.get(&reading.sensor_id).ok_or("missing sensor")?;
        let parcel = properties.get(&sensor.property_id).ok_or("missing property")?;
        let distance_m = parcel_mesh::compliance_distance(
            blast.easting_m,
            blast.northing_m,
            parcel,
            sensor.easting_m,
            sensor.northing_m,
        );
        let attenuated = ppv_field::attenuate(
            blast.source_ppv_mm_s,
            distance_m,
            record.reference_distance_m,
            record.attenuation_exponent,
        );
        let corrected = gain_curve::apply_calibration(
            reading.raw_ppv_mm_s,
            sensor.zero_offset_mm_s,
            sensor.gain_multiplier,
        );
        let combined = ((corrected.min(attenuated)) * 10000.0).round() / 10000.0;
        let threshold = jurisdiction::pick_threshold(
            &parcel.structure_class,
            &blast.fired_at,
            &record.limits,
            record.timezone_offset_hours,
        );
        let exceedance = ((combined - threshold).max(0.0) * 10000.0).round() / 10000.0;
        rows.push(ExceedanceRow {
            blast_id: reading.blast_id.clone(),
            property_id: sensor.property_id.clone(),
            sensor_id: reading.sensor_id.clone(),
            distance_m: (distance_m * 1000.0).round() / 1000.0,
            attenuated_ppv_mm_s: combined,
            threshold_mm_s: threshold,
            exceedance_mm_s: exceedance,
            exceeded: exceedance > 0.0,
        });
    }
    rows.sort_by(|a, b| a.blast_id.cmp(&b.blast_id));
    let exceedance_count = rows.iter().filter(|r| r.exceeded).count() as u32;
    let max_exceedance = rows
        .iter()
        .map(|r| r.exceedance_mm_s)
        .fold(0.0_f64, f64::max);
    let summary = ExceedanceSummary {
        reading_pairs: rows.len() as u32,
        exceedance_count,
        max_exceedance_mm_s: max_exceedance,
    };
    let mut atlas = ExceedanceAtlas {
        seed: seed.to_string(),
        survey: survey.to_string(),
        audit_run_id: active.audit_run_id,
        exceedance_rows: rows,
        summary,
        atlas_digest: String::new(),
    };
    atlas.atlas_digest = atlas_digest(&atlas.summary);
    Ok(atlas)
}

fn atlas_digest(summary: &ExceedanceSummary) -> String {
    let body = format!(
        "{{\"exceedance_count\":{},\"max_exceedance_mm_s\":{},\"reading_pairs\":{}}}",
        summary.exceedance_count, summary.max_exceedance_mm_s, summary.reading_pairs
    );
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())
}

pub fn write_atlas(path: &Path, atlas: &ExceedanceAtlas) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(atlas).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
