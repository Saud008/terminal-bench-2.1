//! Legacy shelf sorter decoy — not on the pack/probe hot path.
#![allow(dead_code)]

pub fn legacy_shelf_key(glyph_id: &str, frame: u32) -> String {
    format!("legacy:{glyph_id}:{frame}")
}
