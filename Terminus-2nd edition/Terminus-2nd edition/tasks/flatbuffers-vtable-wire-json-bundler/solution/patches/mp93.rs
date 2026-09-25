use anyhow::{bail, Result};

use serde::{Deserialize, Serialize};

use std::fs::{self, OpenOptions};

use std::io::Write;



use crate::mp93_digest;

use crate::gp94::SceneJson;

use crate::kx42_snapshot::compute_wire_digest;

use crate::scene_seal;



const LEDGER_PATH: &str = "/app/state/decode.ledger.jsonl";



#[derive(Debug, Serialize, Deserialize)]

struct LedgerEntry {

    seq: u64,
    #[serde(rename = "hn55")]

    wire_digest: String,

    export_digest: String,

    revision: u32,

}



fn read_last_entry() -> Result<Option<LedgerEntry>> {

    if fs::metadata(LEDGER_PATH).is_err() {

        return Ok(None);

    }

    let raw = fs::read_to_string(LEDGER_PATH)?;

    match raw.lines().filter(|line| !line.is_empty()).last() {

        Some(line) => Ok(Some(serde_json::from_str(line)?)),

        None => Ok(None),

    }

}



fn next_seq() -> u64 {

    match read_last_entry() {

        Ok(Some(entry)) => entry.seq + 1,

        _ => 1,

    }

}



pub fn append_ledger(scene: &SceneJson, buf: &[u8]) -> Result<()> {

    fs::create_dir_all("/app/state")?;

    let entry = LedgerEntry {

        seq: next_seq(),

        wire_digest: compute_wire_digest(buf, scene.revision),

        export_digest: export_digest(scene),

        revision: scene.revision,

    };

    let line = serde_json::to_string(&entry)?;

    let mut file = OpenOptions::new()

        .create(true)

        .append(true)

        .open(LEDGER_PATH)?;

    writeln!(file, "{line}")?;

    Ok(())

}



pub fn verify_ledger_head(buf: &[u8], revision: u32) -> Result<()> {

    let head = read_last_entry()?.ok_or_else(|| anyhow::anyhow!("decode ledger empty"))?;

    let expected_wire = compute_wire_digest(buf, revision);

    if head.wire_digest != expected_wire {

        bail!("ledger wire_digest mismatch");

    }

    if head.revision != revision {

        bail!("ledger revision mismatch");

    }

    Ok(())

}



pub fn verify_ledger_envelope(

    wire_digest: &str,

    export_digest: &str,

    revision: u32,

) -> Result<()> {

    let head = read_last_entry()?.ok_or_else(|| anyhow::anyhow!("decode ledger empty"))?;

    if head.wire_digest != wire_digest {

        bail!("ledger wire_digest mismatch");

    }

    if head.export_digest != export_digest {

        bail!("ledger export_digest mismatch");

    }

    if head.revision != revision {

        bail!("ledger revision mismatch");

    }

    Ok(())

}



pub fn export_digest(scene: &SceneJson) -> String {

    scene_seal::export_scene_digest(scene)

}

