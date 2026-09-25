use crate::junction_ledger;
use crate::types::{BindStage, LossEvent, CaptureCache, RouteSegment, SegmentBind};
use std::fs;
use std::path::Path;

fn contains(seg: &RouteSegment, distance_m: f64) -> bool {
    seg.start_m <= distance_m && distance_m < seg.end_m
}

pub fn correlate_span(
    plan: &CaptureCache,
    events_path: &str,
    segments_path: &Path,
    inventory_path: &Path,
    out_dir: &str,
) -> Result<(), String> {
    let raw = fs::read_to_string(events_path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let hdr: serde_json::Value = serde_json::from_str(lines.next().unwrap_or("{}")).map_err(|e| e.to_string())?;
    let suppressed = hdr["suppressed_duplicate_count"].as_u64().unwrap_or(0) as u32;
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
    let mut planned_by_seg: std::collections::BTreeMap<String, f64> = std::collections::BTreeMap::new();
    for seg in &segments {
        planned_by_seg.insert(seg.segment_id.clone(), 0.0);
    }
    for sp in &plan.splices {
        for seg in &segments {
            if contains(seg, sp.distance_m) {
                *planned_by_seg.get_mut(&seg.segment_id).unwrap() += sp.planned_loss_db;
            }
        }
    }
    let mut binds: Vec<SegmentBind> = Vec::new();
    for seg in &segments {
        let mut measured = 0.0;
        let mut count = 0u32;
        for ev in &events {
            if contains(seg, ev.distance_m) {
                measured += ev.measured_loss_db;
                count += 1;
            }
        }
        let conn = inventory.get(&seg.connector_start).copied().unwrap_or(0.0);
        let total = ((measured + conn) * 1000.0).round() / 1000.0;
        let planned = planned_by_seg.get(&seg.segment_id).copied().unwrap_or(0.0);
        binds.push(SegmentBind {
            segment_id: seg.segment_id.clone(),
            measured_loss_db: (measured * 1000.0).round() / 1000.0,
            connector_loss_db: conn,
            total_loss_db: total,
            accepted: total <= planned + conn + 0.01,
            bound_event_count: count,
        });
    }
    binds.sort_by(|a, b| a.segment_id.cmp(&b.segment_id));
    let stage = BindStage {
        run_id: plan.run_id.clone(),
        segments: binds,
        suppressed_duplicate_count: suppressed,
    };
    let out = format!("{out_dir}/{}.json", plan.run_id);
    fs::write(&out, serde_json::to_string_pretty(&stage).unwrap()).map_err(|e| e.to_string())
}
