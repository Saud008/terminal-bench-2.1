use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::sync::{Mutex, OnceLock};

use crate::model::{QueryBatchExport, QueryExport, WorldSpec};
use crate::query::cache::cache_key;
use crate::storage::World;

type CacheMap = HashMap<u64, (u64, Vec<u32>)>;

fn cache_store() -> &'static Mutex<CacheMap> {
    static CACHE: OnceLock<Mutex<CacheMap>> = OnceLock::new();
    CACHE.get_or_init(|| Mutex::new(HashMap::new()))
}

fn world_scope(spec: &WorldSpec) -> u64 {
    let mut hasher = DefaultHasher::new();
    spec.component_names.hash(&mut hasher);
    for ent in &spec.entities {
        ent.id.hash(&mut hasher);
    }
    for op in &spec.journal {
        format!("{op:?}").hash(&mut hasher);
    }
    hasher.finish()
}

pub fn run_query(spec: &WorldSpec, seed: &str, components: &[u16]) -> QueryExport {
    let migrated = World::migrate_export(spec, seed, false);
    let gen = migrated.generation;
    let scope = world_scope(spec);
    let key = cache_key(components, gen, scope);

    if let Ok(cache) = cache_store().lock() {
        if let Some((cached_gen, entities)) = cache.get(&key) {
            if *cached_gen == gen {
                return QueryExport {
                    seed: seed.to_string(),
                    generation: gen,
                    query: components.to_vec(),
                    entities: entities.clone(),
                    cache_hit: true,
                };
            }
        }
    }

    let mut world = World::from_spec(spec, seed);
    world.apply_journal(&spec.journal);
    let mut entities = world.query_entities(components);
    entities.sort();

    cache_store()
        .lock()
        .expect("cache lock")
        .insert(key, (gen, entities.clone()));

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
