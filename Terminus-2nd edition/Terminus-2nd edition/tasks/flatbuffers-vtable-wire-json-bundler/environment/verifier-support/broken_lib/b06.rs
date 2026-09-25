use anyhow::Result;
use serde_json::Value;

use crate::gp94::{EntityJson, SceneJson};

fn sort_root_tags(entity: &mut EntityJson) {
    if let Some(tags) = entity.tags.as_mut() {
        tags.sort_by(|a, b| a.key.cmp(&b.key));
    }
}

pub fn scene_to_json(scene: &SceneJson) -> Result<Value> {
    let mut scene = scene.clone();
    sort_root_tags(&mut scene.root);
    Ok(serde_json::to_value(&scene)?)
}

pub fn render_stdout(scene: &SceneJson) -> Result<String> {
    let value = scene_to_json(scene)?;
    Ok(serde_json::to_string(&value)?)
}
