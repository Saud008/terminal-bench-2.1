use std::fs;
use std::path::Path;

use crate::errors::JitterError;
use crate::ledger::LedgerWriter;
use crate::model::{GapRow, Policy, TimelineExport, TimelinePacket, TimelineStats, penalty_ns};
use crate::order;
use crate::staging::read_staging;

pub fn run_export(staging_path: &str, output_path: &str, ledger_root: &str) -> Result<i32, JitterError> {
    let staging = match read_staging(staging_path) {
        Ok(s) => s,
        Err(JitterError::Io(_)) => return Ok(1),
        Err(_) => return Ok(2),
    };
    if staging.packets.is_empty() {
        return Ok(2);
    }
    let policy = Policy::from_env();
    let mut ordered = staging.packets.clone();
    order::tolerance_order(&mut ordered, policy.window_us);

    let ledger = LedgerWriter::new(ledger_root)?;
    let mut seq = ledger.read_seq()?;
    let mut packets = Vec::new();
    let mut trunc_total = 0u64;
    let mut gap_count = 0u64;
    let mut prev_norm = 0u64;
    let mut prev_raw = ordered[0].raw_ts_us;

    for (i, pkt) in ordered.iter().enumerate() {
        let penalty = if i == 0 {
            0
        } else {
            let p = penalty_ns(&ordered[i - 1], policy);
            trunc_total += p;
            p
        };
        let norm_ns = if i == 0 {
            0
        } else {
            let delta_us = (pkt.raw_ts_us as i64) - (prev_raw as i64);
            let step = delta_us.saturating_mul(1000).saturating_add(penalty as i64);
            if step >= 0 {
                prev_norm.saturating_add(step as u64)
            } else {
                prev_norm.saturating_sub((-step) as u64)
            }
        };
        if i > 0 {
            let step = norm_ns.saturating_sub(prev_norm);
            if step > policy.gap_threshold_ns {
                let row = GapRow {
                    seq,
                    after_index: pkt.index,
                    gap_ns: step,
                    prev_norm_ns: prev_norm,
                    next_norm_ns: norm_ns,
                };
                ledger.append_gap(&row)?;
                seq += 1;
                gap_count += 1;
            }
        }
        prev_raw = pkt.raw_ts_us;
        prev_norm = norm_ns;
        packets.push(TimelinePacket {
            index: pkt.index,
            norm_ns,
            incl_len: pkt.incl_len,
            orig_len: pkt.orig_len,
        });
    }
    ledger.write_seq(seq)?;

    let export = TimelineExport {
        packets,
        stats: TimelineStats {
            gap_count,
            trunc_penalty_total_ns: trunc_total,
            packet_count: ordered.len() as u64,
        },
    };
    if let Some(parent) = Path::new(output_path).parent() {
        fs::create_dir_all(parent).map_err(|e| JitterError::Io(e.to_string()))?;
    }
    let json = serde_json::to_string_pretty(&export).map_err(|e| JitterError::Parse(e.to_string()))?;
    fs::write(output_path, json).map_err(|e| JitterError::Io(e.to_string()))?;
    Ok(0)
}
