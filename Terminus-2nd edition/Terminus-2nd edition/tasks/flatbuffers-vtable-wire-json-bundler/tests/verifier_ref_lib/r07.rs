use anyhow::Result;
use serde_json::Value;

use crate::gp94::SceneJson;

pub fn scene_to_json(scene: &SceneJson) -> Result<Value> {
    Ok(serde_json::to_value(scene)?)
}

pub fn render_stdout(scene: &SceneJson) -> Result<String> {
    let value = scene_to_json(scene)?;
    Ok(serde_json::to_string(&value)?)
}
