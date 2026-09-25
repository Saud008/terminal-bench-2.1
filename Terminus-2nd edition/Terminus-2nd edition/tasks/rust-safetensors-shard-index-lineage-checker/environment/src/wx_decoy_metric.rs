pub fn wrap_shard_metric(shard: &str, bytes: u64) -> String {
    format!("shard_metric:{shard}={bytes}")
}
