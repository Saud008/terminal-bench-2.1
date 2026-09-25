use anyhow::Result;

use crate::gp94::SceneJson;
use crate::st38::decode_scene;
use crate::kx42::root_table;

pub fn decode_buffer(buf: &[u8]) -> Result<SceneJson> {
    let scene_table = root_table(buf)?;
    decode_scene(buf, scene_table)
}
