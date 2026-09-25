use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct BagMetadata {
    pub topics: std::collections::HashMap<String, TopicProfile>,
    #[serde(default)]
    pub remap: std::collections::HashMap<String, String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct TopicProfile {
    pub deadline_ms: u64,
    #[serde(default = "default_clock")]
    pub deadline_clock: String,
}

fn default_clock() -> String {
    "publish".to_string()
}

#[derive(Debug, Clone)]
pub struct Message {
    pub topic: String,
    pub seq: u64,
    pub publish_ns: u64,
    pub receive_ns: u64,
    pub payload: Vec<u8>,
    pub synthetic: bool,
}
