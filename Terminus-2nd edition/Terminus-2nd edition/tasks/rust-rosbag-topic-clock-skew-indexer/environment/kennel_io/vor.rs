use crate::types::{ManifestLatch, TopicSpec};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn latch_manifest(bag_id: &str, path: &Path, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let v: serde_json::Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let reference_topic = v["reference_topic"].as_str().unwrap_or("/clock/anchor").to_string();
    let sync_window_ns = v["sync_window_ns"].as_u64().unwrap_or(5_000_000);
    let mut topic_remap = BTreeMap::new();
    if let Some(obj) = v["topic_remap"].as_object() {
        for (k, val) in obj {
            topic_remap.insert(k.clone(), val.as_str().unwrap_or(k).to_string());
        }
    }
    let mut topics = Vec::new();
    if let Some(arr) = v["topics"].as_array() {
        for t in arr {
            topics.push(TopicSpec {
                name: t["name"].as_str().unwrap_or("").to_string(),
                r#type: t["type"].as_str().unwrap_or("").to_string(),
                expected_rate_hz: t["expected_rate_hz"].as_u64().unwrap_or(0) as u32,
            });
        }
    }
    let latch_doc = ManifestLatch {
        bag_id: bag_id.to_string(),
        reference_topic,
        sync_window_ns,
        topic_remap: BTreeMap::new(),
        topics,
        manifest_revision: 1,
    };
    let out = format!("{out_dir}/{bag_id}.json");
    fs::write(&out, serde_json::to_string_pretty(&latch_doc).unwrap()).map_err(|e| e.to_string())
}
