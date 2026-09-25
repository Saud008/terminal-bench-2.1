use crate::types::ShardFile;

pub fn check_compatibility(shards: &[ShardFile]) -> Result<(), String> {
    if shards.is_empty() {
        return Err("empty shard list".into());
    }
    let first = &shards[0];
    for shard in shards.iter().skip(1) {
        if shard.hash_seed != first.hash_seed
            || shard.width != first.width
            || shard.depth != first.depth
        {
            return Err(format!(
                "incompatible shard {} seed or dimensions",
                shard.shard_id
            ));
        }
        if shard.namespace_salt != first.namespace_salt {
            return Err(format!("incompatible namespace on {}", shard.shard_id));
        }
    }
    Ok(())
}
