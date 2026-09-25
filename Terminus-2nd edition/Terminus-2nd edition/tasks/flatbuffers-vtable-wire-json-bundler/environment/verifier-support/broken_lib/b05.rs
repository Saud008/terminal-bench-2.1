use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::fs;

use crate::gp94::{EntityJson, SceneJson};
use crate::kx42_digest as hn55;

const SNAPSHOT_PATH: &str = "/app/state/decode.snapshot.json";

#[derive(Debug, Serialize, Deserialize)]
pub struct StagingEnvelope {
    #[serde(rename = "hn55")]
    pub wire_digest: String,
    pub scene: SceneJson,
}

fn coerce_empty_tags(entity: &mut EntityJson) {
    if entity.tags.is_none() {
        entity.tags = Some(Vec::new());
    }
    if let Some(parent) = entity.parent.as_mut() {
        coerce_empty_tags(parent);
    }
}

pub fn compute_wire_digest(buf: &[u8], revision: u32) -> String {
    hn55::fingerprint(buf, revision)
}

pub fn write_snapshot(scene: &SceneJson, buf: &[u8]) -> Result<()> {
    fs::create_dir_all("/app/state")?;
    let mut scene = scene.clone();
    coerce_empty_tags(&mut scene.root);
    let envelope = StagingEnvelope {
        wire_digest: hn55::fingerprint(buf, scene.revision),
        scene,
    };
    let json = serde_json::to_string_pretty(&envelope)?;
    fs::write(SNAPSHOT_PATH, json)?;
    Ok(())
}

pub fn load_snapshot(_buf: &[u8], _revision: u32) -> Result<SceneJson> {
    let envelope = read_envelope()?;
    Ok(envelope.scene)
}

pub fn read_envelope() -> Result<StagingEnvelope> {
    let raw = fs::read_to_string(SNAPSHOT_PATH)?;
    let envelope: StagingEnvelope = serde_json::from_str(&raw)?;
    Ok(envelope)
}
