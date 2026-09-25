//! Reference helpers for flatc-compatible JSON rendering.
//!
//! These utilities document export conventions. The authoritative stdout path
//! is `stdout_render::render_stdout` orchestrated by `rw14.rs` after staging
//! reload. `export::render_stdout` is a legacy helper and not on the hot path.

use serde_json::Value;

use crate::gp94::SceneJson;

/// Serialize a scene without reordering tag vectors or synthesizing absent fields.
pub fn scene_value_preserve_order(scene: &SceneJson) -> Value {
    serde_json::to_value(scene).unwrap_or(Value::Null)
}

/// Compact JSON text matching flatc element order (reference only).
pub fn render_reference_json(scene: &SceneJson) -> String {
    serde_json::to_string(&scene_value_preserve_order(scene)).unwrap_or_default()
}
