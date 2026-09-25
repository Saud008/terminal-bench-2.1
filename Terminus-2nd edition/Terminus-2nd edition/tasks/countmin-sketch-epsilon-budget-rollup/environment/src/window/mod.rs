use crate::types::ShardFile;

pub struct OverlapInfo {
    pub overlap_ms: u64,
}

pub fn compute_overlap(shards: &[ShardFile]) -> Result<OverlapInfo, String> {
    if shards.is_empty() {
        return Err("no shards".into());
    }
    let mut start = shards[0].window_start_ms;
    let mut end = shards[0].window_end_ms;
    for shard in shards.iter().skip(1) {
        start = start.min(shard.window_start_ms);
        end = end.max(shard.window_end_ms);
    }
    let overlap_ms = end.saturating_sub(start);
    Ok(OverlapInfo { overlap_ms })
}

pub fn shard_weights(shards: &[ShardFile], overlap_ms: u64) -> std::collections::BTreeMap<String, f64> {
    let mut out = std::collections::BTreeMap::new();
    for shard in shards {
        let window_ms = shard.window_end_ms.saturating_sub(shard.window_start_ms);
        let w = if window_ms == 0 {
            0.0
        } else {
            overlap_ms as f64 / window_ms as f64
        };
        out.insert(shard.shard_id.clone(), w);
    }
    out
}
