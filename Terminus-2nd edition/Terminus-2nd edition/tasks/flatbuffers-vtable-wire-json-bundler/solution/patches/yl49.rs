use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

use crate::gp94::SceneJson;

pub fn export_scene_digest(scene: &SceneJson) -> String {
    let json = serde_json::to_string(scene).unwrap_or_default();
    let mut hasher = DefaultHasher::new();
    json.hash(&mut hasher);
    format!("{:016x}", hasher.finish())
}
