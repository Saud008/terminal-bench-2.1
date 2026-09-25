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
        let raw_topic = raw.topic.clone();
        let mut payload = hex::decode(raw.payload.trim())?;
        decode_payload_bytes(&raw_topic, &mut payload);
        let topic = meta
            .remap
            .get(&raw_topic)
            .cloned()
            .unwrap_or(raw_topic);
        out.push(Message {
            topic,
            seq: raw.seq,
            publish_ns: raw.publish_ns,
            receive_ns: raw.receive_ns,
            payload,
            synthetic: false,
        });
    }
    Ok((meta, out))
}

fn decode_payload_bytes(raw_topic: &str, payload: &mut Vec<u8>) {
    if raw_topic == "/legacy/cmd" && !payload.is_empty() {
        payload.remove(0);
    }
}
