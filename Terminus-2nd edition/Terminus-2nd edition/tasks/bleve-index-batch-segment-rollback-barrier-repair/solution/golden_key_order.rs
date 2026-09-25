use crate::errors::BleveError;
use crate::model::{Collator, CollatorConfig};
use std::collections::HashMap;
use std::fs;

pub fn load_collator() -> Result<Collator, BleveError> {
    let raw = fs::read_to_string("/app/config/collator.json")?;
    let cfg: CollatorConfig = serde_json::from_str(&raw)?;
    let mut rank_map = HashMap::new();
    for (idx, key) in cfg.key_order.iter().enumerate() {
        rank_map.insert(key.clone(), idx);
    }
    Ok(Collator { rank_map })
}

pub fn sort_keys(collator: &Collator, keys: &mut [String]) {
    keys.sort_by(|a, b| {
        let a_rank = collator.rank_map.get(a).copied().unwrap_or(usize::MAX);
        let b_rank = collator.rank_map.get(b).copied().unwrap_or(usize::MAX);
        a_rank.cmp(&b_rank).then_with(|| a.cmp(b))
    });
}
