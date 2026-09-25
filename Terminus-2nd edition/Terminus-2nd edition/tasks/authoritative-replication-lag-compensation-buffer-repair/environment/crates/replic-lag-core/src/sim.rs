//! Run client/server timeline simulation from a trace file.

use crate::buffer::CompensationBuffer;
use crate::lag::LagEstimator;
use crate::ledger::InputLedger;
use crate::model::{SimReport, TraceEvent};
use crate::rollback::{RollbackWindow, ROLLBACK_MIN_TICKS};
use crate::store::LagStore;
use crate::trace_path::resolve_trace_path;
use std::env;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;

pub fn run_simulation(
    trace_path: &Path,
    db_path: &Path,
    report_path: &Path,
    tick_rate_hz: u64,
) -> Result<SimReport, String> {
    let store = LagStore::open(db_path).map_err(|e| e.to_string())?;
    let tick_rate = if tick_rate_hz == 0 {
        env::var("TB3_TICK_RATE_HZ")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(60)
    } else {
        tick_rate_hz
    };

    let mut lag = LagEstimator::new();
    let mut buffer = CompensationBuffer::new();
    let mut ledger = InputLedger::new();
    let mut rollback = RollbackWindow::new(ROLLBACK_MIN_TICKS);
    let mut read_head = store.get_meta("read_head").map_err(|e| e.to_string())?;
    let mut late_rejected = 0u64;
    let resolved = resolve_trace_path(trace_path);

    let file = fs::File::open(&resolved).map_err(|e| e.to_string())?;
    let reader = BufReader::new(file);

    for line in reader.lines() {
        let line = line.map_err(|e| e.to_string())?;
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let event: TraceEvent = serde_json::from_str(trimmed).map_err(|e| e.to_string())?;

        match event {
            TraceEvent::Rtt { rtt_us, .. } => {
                lag.record_rtt_us(rtt_us);
            }
            TraceEvent::Input {
                input_seq,
                client_tick,
            } => {
                ledger.record_input(input_seq);
                buffer.queue_input(input_seq, client_tick);
            }
            TraceEvent::InputAck { input_seq, .. } => {
                buffer.mark_acked(input_seq);
            }
            TraceEvent::LateFrame { frame_seq } => {
                if frame_seq < read_head {
                    late_rejected += 1;
                    read_head = frame_seq + 1;
                } else {
                    read_head = frame_seq + 1;
                }
            }
            TraceEvent::Reconnect { rollback_ticks } => {
                rollback.on_reconnect(rollback_ticks);
            }
            TraceEvent::SnapshotDelta { .. } | TraceEvent::SnapshotGap { .. } => {}
        }
    }

    let lag_us = lag.estimate_us();
    let buffered_applied = buffer.apply_compensation(lag_us, tick_rate);

    let report = SimReport {
        lag_estimate_us: lag_us,
        lag_method: lag.method_name().to_string(),
        buffered_inputs_applied: buffered_applied,
        duplicate_inputs_skipped: ledger.skipped_duplicates(),
        late_frames_rejected: late_rejected,
        read_head,
        rollback_window_ticks: rollback.ticks(),
        tick_rate_hz: tick_rate,
    };

    store.set_meta("read_head", read_head).map_err(|e| e.to_string())?;

    let parent = report_path.parent().unwrap_or(Path::new("/app/state"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    fs::write(
        report_path,
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;

    Ok(report)
}
