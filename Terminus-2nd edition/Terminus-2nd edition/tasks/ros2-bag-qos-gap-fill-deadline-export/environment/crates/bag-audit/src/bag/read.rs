use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use serde::Deserialize;

use crate::model::{BagMetadata, Message};

#[derive(Debug, Deserialize)]
struct RawLine {
    topic: String,
    seq: u64,
    publish_ns: u64,
    receive_ns: u64,
    payload: String,
}

pub fn load_bag(dir: &Path) -> Result<(BagMetadata, Vec<Message>)> {
    let meta_path = dir.join("metadata.json");
    let meta: BagMetadata =
        serde_json::from_str(&fs::read_to_string(&meta_path).context("read metadata")?)?;
    let mut out = Vec::new();
    for line in fs::read_to_string(dir.join("messages.jsonl"))?.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let raw: RawLine = serde_json::from_str(line)?;
        let payload = hex::decode(raw.payload.trim())?;
        let mut msg = Message {
            topic: raw.topic.clone(),
            seq: raw.seq,
            publish_ns: raw.publish_ns,
            receive_ns: raw.receive_ns,
            payload,
            synthetic: false,
        };
        if let Some(canonical) = meta.remap.get(&raw.topic) {
            msg.topic = canonical.clone();
        }
        decode_payload_record(&mut msg);
        out.push(msg);
    }
    Ok((meta, out))
}

fn decode_payload_record(msg: &mut Message) {
    if msg.topic == "/legacy/cmd" && !msg.payload.is_empty() {
        msg.payload.remove(0);
    }
}
