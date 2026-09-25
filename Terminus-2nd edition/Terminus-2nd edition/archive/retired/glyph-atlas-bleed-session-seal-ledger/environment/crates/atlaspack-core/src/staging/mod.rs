//! Staging snapshot helpers for playtest seal audits (not the pack compositor).
#![allow(dead_code)]

use serde_json::{json, Value};

pub fn staging_snapshot(seed: u64, set_name: &str, sprite_count: usize) -> Value {
    json!({
        "stage": "atlas-staging",
        "seed": seed,
        "set": set_name,
        "sprite_count": sprite_count,
    })
}
