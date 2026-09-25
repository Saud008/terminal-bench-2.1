use anyhow::Result;

use crate::gp94::{EntityJson, SceneJson};

fn sort_all_tags(entity: &mut EntityJson) {
    if let Some(tags) = entity.tags.as_mut() {
        tags.sort_by(|a, b| a.key.cmp(&b.key));
    }
    if let Some(parent) = entity.parent.as_mut() {
        sort_all_tags(parent);
    }
}

pub fn render_stdout(scene: &SceneJson) -> Result<String> {
    let mut scene = scene.clone();
    sort_all_tags(&mut scene.root);
    Ok(serde_json::to_string(&scene)?)
}
