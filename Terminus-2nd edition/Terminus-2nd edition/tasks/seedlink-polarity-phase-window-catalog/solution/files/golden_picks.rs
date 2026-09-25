use std::collections::HashSet;
use std::path::Path;

use crate::clip::clip_bit;
use crate::leap::leap_adjust_us;
use crate::message::{PickRow, SnippetMsg};

pub const P_PRE_US: u64 = 2_000_000;
pub const P_POST_US: u64 = 4_000_000;
pub const S_PRE_US: u64 = 3_000_000;
pub const S_POST_US: u64 = 5_000_000;
pub const X_PRE_US: u64 = 1_000_000;
pub const X_POST_US: u64 = 1_000_000;

pub fn phase_label(code: u8) -> &'static str {
    match code {
        0 => "P",
        1 => "S",
        _ => "X",
    }
}

pub fn window_bounds(code: u8) -> (u64, u64) {
    match code {
        0 => (P_PRE_US, P_POST_US),
        1 => (S_PRE_US, S_POST_US),
        _ => (X_PRE_US, X_POST_US),
    }
}

pub fn sample_period_us(rate_mhz: u32) -> u64 {
    (1_000_000_u64 * 1000) / rate_mhz as u64
}

pub fn pick_center_us(msg: &SnippetMsg, pick: &PickRow, leap_epochs: &HashSet<u32>) -> u64 {
    let period = sample_period_us(msg.rate_mhz);
    let base = msg.epoch_sec as u64 * 1_000_000 + pick.sample_idx as u64 * period;
    base + leap_adjust_us(msg.epoch_sec, msg.leap_marker, leap_epochs)
}

pub fn window_sample_range(
    msg: &SnippetMsg,
    pick: &PickRow,
    leap_epochs: &HashSet<u32>,
) -> (usize, usize) {
    let center = pick_center_us(msg, pick, leap_epochs);
    let (pre, post) = window_bounds(pick.phase_code);
    let period = sample_period_us(msg.rate_mhz);
    let start_us = center.saturating_sub(pre);
    let end_us = center + post;
    let epoch_us = msg.epoch_sec as u64 * 1_000_000;
    let first = ((start_us.saturating_sub(epoch_us)) / period) as usize;
    let last = ((end_us.saturating_sub(epoch_us)) / period) as usize;
    let first = first.min(msg.sample_count as usize - 1);
    let last = last.min(msg.sample_count as usize - 1);
    (first, last.max(first))
}

pub fn clipped_fraction(msg: &SnippetMsg, pick: &PickRow, leap_epochs: &HashSet<u32>) -> f64 {
    let (first, last) = window_sample_range(msg, pick, leap_epochs);
    if last < first {
        return 0.0;
    }
    let total = (last - first + 1) as f64;
    let clipped = (first..=last)
        .filter(|idx| clip_bit(&msg.clip_mask, *idx))
        .count() as f64;
    ((clipped / total) * 10_000.0).round() / 10_000.0
}

pub fn peak_amplitude(msg: &SnippetMsg, pick: &PickRow, leap_epochs: &HashSet<u32>) -> i32 {
    let (first, last) = window_sample_range(msg, pick, leap_epochs);
    if first > last {
        return 0;
    }
    *msg.samples[first..=last]
        .iter()
        .max_by_key(|v| v.abs())
        .unwrap_or(&0) as i32
}

pub fn polarity_label(effective: i8, peak: i32) -> String {
    let sign = effective as i32 * peak;
    if sign > 0 {
        "up".to_string()
    } else if sign < 0 {
        "down".to_string()
    } else {
        "unknown".to_string()
    }
}
