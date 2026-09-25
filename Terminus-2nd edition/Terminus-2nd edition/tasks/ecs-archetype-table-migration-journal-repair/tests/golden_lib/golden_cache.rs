use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

use crate::model::ComponentId;

pub fn cache_key(components: &[ComponentId], generation: u64, world_scope: u64) -> u64 {
    let mut hasher = DefaultHasher::new();
    components.hash(&mut hasher);
    generation.hash(&mut hasher);
    world_scope.hash(&mut hasher);
    hasher.finish()
}
