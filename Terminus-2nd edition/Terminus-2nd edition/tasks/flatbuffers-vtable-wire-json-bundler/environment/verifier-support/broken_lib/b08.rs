use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

use crate::gp94::{EntityJson, SceneJson};

fn sort_entity_tags(entity: &mut EntityJson) {
    if let Some(tags) = entity.tags.as_mut() {
        tags.sort_by(|a, b| a.key.cmp(&b.key));
    }
    if let Some(parent) = entity.parent.as_mut() {
        sort_entity_tags(parent);
    }
}

/// Hash of the staged scene JSON for ledger export_digest fields.
pub fn export_scene_digest(scene: &SceneJson) -> String {
    let mut scene = scene.clone();
    sort_entity_tags(&mut scene.root);
    let json = serde_json::to_string(&scene).unwrap_or_default();
    let mut hasher = DefaultHasher::new();
    json.hash(&mut hasher);
    format!("fnv1a64:{:016x}", hasher.finish())
}
