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
