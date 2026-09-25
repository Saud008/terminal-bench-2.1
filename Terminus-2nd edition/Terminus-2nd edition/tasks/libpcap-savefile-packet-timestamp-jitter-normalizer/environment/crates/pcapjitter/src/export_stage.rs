use std::fs;
use std::path::Path;

use crate::errors::JitterError;
use crate::ledger::LedgerWriter;
use crate::model::{Policy, TimelineExport, TimelinePacket, TimelineStats};
use crate::staging::read_staging;
use crate::timeline;
use crate::wrap;

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
    wrap::arrange_packets(&mut ordered);

    let mut packets = Vec::new();
    let trunc_total = 0u64;
    let mut gap_count = 0u64;
    let mut prev_norm = 0u64;
    let mut prev_raw = ordered[0].raw_ts_us;

    for (i, pkt) in ordered.iter().enumerate() {
        let norm_ns = if i == 0 {
            0
        } else {
            let delta_us = pkt.raw_ts_us.saturating_sub(prev_raw);
            let delta_ns = timeline::raw_to_norm_ns(delta_us as u32, 0);
            prev_norm.saturating_add(delta_ns)
        };
        if i > 0 {
            let delta_ns = norm_ns.saturating_sub(prev_norm);
            if delta_ns > policy.gap_threshold_ns {
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

    let _ledger = LedgerWriter::new(ledger_root)?;
    Ok(0)
}
