use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

use crate::model::{QueryBatchExport, QueryExport, WorldSpec};
use crate::query::cache::cache_key;
use crate::storage::World;

type CacheMap = HashMap<u64, Vec<u32>>;

fn cache_store() -> &'static Mutex<CacheMap> {
    static CACHE: OnceLock<Mutex<CacheMap>> = OnceLock::new();
    CACHE.get_or_init(|| Mutex::new(HashMap::new()))
}

pub fn run_query(spec: &WorldSpec, seed: &str, components: &[u16]) -> QueryExport {
    let migrated = World::migrate_export(spec, seed, false);
    let gen = migrated.generation;
    let key = cache_key(components, gen, 0);

    let cache = cache_store().lock().expect("cache lock");
    if let Some(entities) = cache.get(&key) {
        return QueryExport {
            seed: seed.to_string(),
            generation: gen,
            query: components.to_vec(),
            entities: entities.clone(),
            cache_hit: true,
        };
    }
    drop(cache);

    let mut world = World::from_spec(spec, seed);
    world.apply_journal(&spec.journal);
    let mut entities = world.query_entities(components);
    entities.sort();

    cache_store()
        .lock()
        .expect("cache lock")
        .insert(key, entities.clone());

    QueryExport {
        seed: seed.to_string(),
        generation: gen,
        query: components.to_vec(),
        entities,
        cache_hit: false,
    }
}

pub fn run_query_batch(specs: &[(&WorldSpec, &[u16])], seed: &str) -> QueryBatchExport {
    let results = specs
        .iter()
        .map(|(world_spec, components)| run_query(world_spec, seed, components))
        .collect();
    QueryBatchExport {
        seed: seed.to_string(),
        results,
    }
}
