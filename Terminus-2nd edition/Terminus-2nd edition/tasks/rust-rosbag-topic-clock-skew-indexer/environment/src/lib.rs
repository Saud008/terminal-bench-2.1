#[path = "../kennel_io/vor.rs"]
pub mod kennel_io;
#[path = "../hopf_weave/weave.rs"]
pub mod hopf_weave;
#[path = "../order_gate/order.rs"]
pub mod order_gate;
#[path = "../relay_rank/rank.rs"]
pub mod relay_rank;
#[path = "../ruelle_pq/match.rs"]
pub mod ruelle_pq;
#[path = "../peskin_pq/publish.rs"]
pub mod peskin_pq;
#[path = "../tf_decoy/tf.rs"]
pub mod tf_decoy;
#[path = "../model/skew_types.rs"]
pub mod types;

pub fn bag_root() -> String {
    std::env::var("TB3_BAG_ROOT").unwrap_or_else(|_| "/app/fixtures/bags".to_string())
}

pub fn reference_topic_override() -> Option<String> {
    std::env::var("TB3_REFERENCE_TOPIC").ok()
}

pub fn sync_window_override() -> Option<u64> {
    std::env::var("TB3_SYNC_WINDOW_NS")
        .ok()
        .and_then(|v| v.parse().ok())
}
