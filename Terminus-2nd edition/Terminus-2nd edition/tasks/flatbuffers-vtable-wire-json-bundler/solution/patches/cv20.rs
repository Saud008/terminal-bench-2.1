use anyhow::{bail, Result};

use serde::{Deserialize, Serialize};

use std::fs;



use crate::gp94::SceneJson;

use crate::kx42_digest as hn55;



const SNAPSHOT_PATH: &str = "/app/state/decode.snapshot.json";



#[derive(Debug, Serialize, Deserialize)]

pub struct StagingEnvelope {
    #[serde(rename = "hn55")]
    pub wire_digest: String,

    pub scene: SceneJson,

}



pub fn compute_wire_digest(buf: &[u8], revision: u32) -> String {

    hn55::fingerprint(buf, revision)

}



pub fn write_snapshot(scene: &SceneJson, buf: &[u8]) -> Result<()> {

    fs::create_dir_all("/app/state")?;

    let envelope = StagingEnvelope {

        wire_digest: hn55::fingerprint(buf, scene.revision),

        scene: scene.clone(),

    };

    let json = serde_json::to_string_pretty(&envelope)?;

    fs::write(SNAPSHOT_PATH, json)?;

    Ok(())

}



pub fn read_envelope() -> Result<StagingEnvelope> {

    let raw = fs::read_to_string(SNAPSHOT_PATH)?;

    let envelope: StagingEnvelope = serde_json::from_str(&raw)?;

    Ok(envelope)

}



pub fn load_snapshot(buf: &[u8], revision: u32) -> Result<SceneJson> {

    let envelope = read_envelope()?;

    let expected = hn55::fingerprint(buf, revision);

    if envelope.wire_digest != expected {

        bail!("staging wire_digest mismatch");

    }

    Ok(envelope.scene)

}

