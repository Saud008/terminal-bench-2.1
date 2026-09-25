#!/usr/bin/env bash
set -euo pipefail
cd /app

cat > /app/bline_mf/parse.rs <<'EOF'
use crate::types::ChartDoc;

pub fn parse_chart(text: &str) -> Result<ChartDoc, String> {
    let mut doc: ChartDoc = serde_json::from_str(text).map_err(|e| e.to_string())?;
    doc.chart_id = normalize_id(&doc.chart_id);
    Ok(doc)
}

pub fn normalize_id(chart_id: &str) -> String {
    chart_id.to_ascii_lowercase()
}
EOF

cat > /app/bline_pl/order.rs <<'EOF'
use crate::types::{Config, TempoEvent};
use std::fs;
use std::io::Write;

pub fn stage_tempo(cfg: &Config, run_id: &str, events: &[TempoEvent]) -> Result<(), String> {
    let mut ordered = events.to_vec();
    ordered.sort_by_key(|e| e.tick);
    let out = format!("{}/{}.jsonl", cfg.tempo_stage_dir, run_id);
    let mut f = fs::File::create(&out).map_err(|e| e.to_string())?;
    writeln!(f, "{{\"run_id\":\"{run_id}\",\"row_type\":\"header\"}}").map_err(|e| e.to_string())?;
    for ev in ordered {
        let js = serde_json::to_string(&ev).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
EOF

cat > /app/bline_wc/convert.rs <<'EOF'
use crate::types::TempoEvent;

pub fn tick_to_seconds(tick: u64, ppq: u32, events: &[TempoEvent]) -> f64 {
    if tick == 0 || events.is_empty() {
        return 0.0;
    }
    let mut ordered = events.to_vec();
    ordered.sort_by_key(|e| e.tick);
    let mut sec = 0.0;
    for i in 0..ordered.len() {
        let start = ordered[i].tick;
        if tick <= start {
            break;
        }
        let end = if i + 1 < ordered.len() {
            ordered[i + 1].tick
        } else {
            tick
        };
        let clip = tick.min(end);
        let delta = clip.saturating_sub(start);
        if delta > 0 {
            sec += (delta as f64 / ppq as f64)
                * (ordered[i].microseconds_per_quarter as f64 / 1_000_000.0);
        }
        if tick <= end {
            break;
        }
    }
    sec
}
EOF

cat > /app/bline_tm/meter.rs <<'EOF'
use crate::types::TimeSig;

pub fn ticks_per_beat(ppq: u32, meter: &TimeSig) -> u32 {
    ppq * 4 / meter.denominator
}

pub fn active_meter(tick: u64, meters: &[TimeSig]) -> TimeSig {
    let mut active = meters[0].clone();
    for m in meters {
        if m.tick <= tick {
            active = m.clone();
        }
    }
    active
}
EOF

cat > /app/bline_qn/snap.rs <<'EOF'
use crate::bline_tm;
use crate::types::{ChartManifest, TimeSig};

pub fn quantize_tick(tick: u64, ppq: u32, meters: &[TimeSig], divisor: u32) -> u64 {
    let meter = bline_tm::active_meter(tick, meters);
    let tpb = bline_tm::ticks_per_beat(ppq, &meter);
    let grid = ((tpb / divisor).max(1)) as u64;
    ((tick as f64 / grid as f64).round() as u64) * grid
}

pub fn grid_spacing(ppq: u32, meters: &[TimeSig], divisor: u32, tick: u64) -> u32 {
    let meter = bline_tm::active_meter(tick, meters);
    let tpb = bline_tm::ticks_per_beat(ppq, &meter);
    (tpb / divisor).max(1)
}

pub fn consistency_delta(raw: u64, quantized: u64, grid: u32) -> bool {
    let half = (grid / 2) as u64;
    raw.abs_diff(quantized) <= half
}

pub fn apply_quant(_manifest: &ChartManifest, _divisor: u32) -> Vec<(String, u32, u64, u64)> {
    vec![]
}
EOF

cat > /app/bline_lg/reject.rs <<'EOF'
use crate::types::NoteEvent;

fn interval_overlap(a0: u64, a1: u64, b0: u64, b1: u64) -> bool {
    a0 < b1 && b0 < a1
}

pub fn overlaps(a: &NoteEvent, b: &NoteEvent) -> bool {
    if a.lane != b.lane {
        return false;
    }
    let a_end = a.tick.saturating_add(a.duration);
    let b_end = b.tick.saturating_add(b.duration);
    interval_overlap(a.tick, a_end, b.tick, b_end)
}

pub fn rejected_ids(notes: &[NoteEvent]) -> std::collections::BTreeSet<String> {
    let mut rejected = std::collections::BTreeSet::new();
    for i in 0..notes.len() {
        for j in (i + 1)..notes.len() {
            if overlaps(&notes[i], &notes[j]) {
                let loser = if notes[j].id > notes[i].id {
                    notes[j].id.clone()
                } else {
                    notes[i].id.clone()
                };
                rejected.insert(loser);
            }
        }
    }
    rejected
}
EOF

cat > /app/bline_ex/emit.rs <<'EOF'
use crate::bline_qn;
use crate::types::{BeatGridAudit, Config, NoteStageRow};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub fn audit_digest(audit: &BeatGridAudit) -> String {
    let mut ids: Vec<String> = audit.notes.iter().map(|n| n.id.clone()).collect();
    ids.sort();
    let body = serde_json::json!({
        "accepted_note_count": audit.accepted_note_count,
        "chart_id": audit.chart_id,
        "rejected_overlap_count": audit.rejected_overlap_count,
        "run_id": audit.run_id,
        "source_ids": ids,
    });
    hex::encode(Sha256::digest(body.to_string().as_bytes()))
}

pub fn build_audit(
    cfg: &Config,
    run_id: &str,
    ledger: &crate::types::ChartManifest,
) -> Result<BeatGridAudit, String> {
    let note_path = format!("{}/{}.jsonl", cfg.note_stage_dir, run_id);
    let raw = fs::read_to_string(&note_path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let _hdr = lines.next();
    let mut rows = Vec::new();
    for line in lines {
        rows.push(serde_json::from_str::<NoteStageRow>(line).map_err(|e| e.to_string())?);
    }
    rows.sort_by(|a, b| a.id.cmp(&b.id));
    let rejected = rows.iter().filter(|r| r.rejected_overlap).count() as u32;
    let accepted = rows.len() as u32 - rejected;
    let accepted_rows: Vec<_> = rows.iter().filter(|r| !r.rejected_overlap).collect();
    let mut consistent = 0u32;
    for row in &accepted_rows {
        let grid = bline_qn::grid_spacing(
            ledger.ppq,
            &ledger.time_sigs,
            ledger.quant_divisor,
            row.raw_tick,
        );
        if bline_qn::consistency_delta(row.raw_tick, row.quantized_tick, grid) {
            consistent += 1;
        }
    }
    let score = if accepted_rows.is_empty() {
        1.0
    } else {
        consistent as f64 / accepted_rows.len() as f64
    };
    let audit = BeatGridAudit {
        run_id: run_id.to_string(),
        chart_id: ledger.chart_id.clone(),
        ppq: ledger.ppq,
        tempo_event_count: ledger.tempo_events.len() as u32,
        accepted_note_count: accepted,
        rejected_overlap_count: rejected,
        grid_consistency_score: score,
        notes: rows,
        audit_digest: String::new(),
    };
    let digest = audit_digest(&audit);
    Ok(BeatGridAudit {
        audit_digest: digest,
        ..audit
    })
}

pub fn write_audit(
    cfg: &Config,
    run_id: &str,
    ledger: &crate::types::ChartManifest,
    output: &Path,
) -> Result<(), String> {
    let audit = build_audit(cfg, run_id, ledger)?;
    fs::write(
        output,
        serde_json::to_string_pretty(&audit).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())
}
EOF

/usr/local/cargo/bin/cargo generate-lockfile
/usr/local/cargo/bin/cargo build --release --locked
install -m 0755 /app/target/release/midgrid /app/bin/midgrid

