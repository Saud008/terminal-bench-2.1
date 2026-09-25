use crate::junction_ledger;
use crate::types::{BindStage, LossEvent, CaptureCache, RouteSegment, SegmentBind};
use std::fs;
use std::path::Path;

pub fn correlate_span(
    plan: &CaptureCache,
    events_path: &str,
    segments_path: &Path,
    inventory_path: &Path,
    out_dir: &str,
) -> Result<(), String> {
    let raw = fs::read_to_string(events_path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let _hdr = lines.next();
    let mut events: Vec<LossEvent> = Vec::new();
    for line in lines {
        events.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    let seg_raw = fs::read_to_string(segments_path).map_err(|e| e.to_string())?;
    let seg_v: serde_json::Value = serde_json::from_str(&seg_raw).map_err(|e| e.to_string())?;
    let mut segments: Vec<RouteSegment> = Vec::new();
    if let Some(arr) = seg_v["segments"].as_array() {
        for s in arr {
            segments.push(RouteSegment {
                segment_id: s["segment_id"].as_str().unwrap_or("").to_string(),
                start_m: s["start_m"].as_f64().unwrap_or(0.0),
                end_m: s["end_m"].as_f64().unwrap_or(0.0),
                connector_start: s["connector_start"].as_str().unwrap_or("").to_string(),
                connector_end: s["connector_end"].as_str().unwrap_or("").to_string(),
            });
        }
    }
    let inventory = junction_ledger::load_inventory(inventory_path)?;
    let mut binds: Vec<SegmentBind> = Vec::new();
    for seg in &segments {
        let mut measured = 0.0;
        let mut count = 0u32;
        for ev in &events {
            if ev.distance_m >= seg.start_m {
                measured += ev.measured_loss_db;
                count += 1;
                break;
            }
        }
        let connector_loss = inventory.get(&seg.connector_start).copied().unwrap_or(0.0);
        let total = measured + connector_loss;
        let planned: f64 = plan.splices.iter().map(|s| s.planned_loss_db).sum();
        binds.push(SegmentBind {
            segment_id: seg.segment_id.clone(),
            measured_loss_db: measured,
            connector_loss_db: connector_loss,
            total_loss_db: total,
            accepted: total <= planned + 1.0,
            bound_event_count: count,
        });
    }
    binds.sort_by(|a, b| a.segment_id.cmp(&b.segment_id));
    let stage = BindStage {
        run_id: plan.run_id.clone(),
        segments: binds,
        suppressed_duplicate_count: 0,
    };
    let out = format!("{out_dir}/{}.json", plan.run_id);
    fs::write(&out, serde_json::to_string_pretty(&stage).unwrap()).map_err(|e| e.to_string())
}
