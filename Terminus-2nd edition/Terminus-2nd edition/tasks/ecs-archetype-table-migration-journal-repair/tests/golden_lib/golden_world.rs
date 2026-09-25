use std::collections::{BTreeMap, BTreeSet};

use crate::model::{
    ArchetypeOut, ComponentData, ComponentId, ComponentSpec, EntityId, EntityOut, EntitySpec, JournalOp,
    MigrateExport, WorldSpec,
};

use super::archetype::{archetype_hash, hash_hex};
use super::component::{build_component_map, registration_order};
use super::sparse::SparseSet;

#[derive(Debug, Clone)]
struct CompInst {
    data: String,
    align: u32,
}

#[derive(Debug, Clone)]
struct EntityRecord {
    components: BTreeMap<ComponentId, CompInst>,
}

#[derive(Debug)]
pub struct World {
    pub seed: String,
    pub generation: u64,
    pub component_map: BTreeMap<String, ComponentId>,
    pub specs: BTreeMap<String, ComponentSpec>,
    entities: BTreeMap<EntityId, EntityRecord>,
    sparse: SparseSet,
    tombstones: BTreeSet<EntityId>,
}

impl World {
    pub fn from_spec(spec: &WorldSpec, seed: &str) -> Self {
        let order = registration_order(&spec.component_names, seed);
        let component_map = build_component_map(&order);
        let mut world = Self::empty(spec, seed, component_map);
        for ent in &spec.entities {
            world.insert_entity(ent);
        }
        world
    }

    pub fn migrate_export(spec: &WorldSpec, seed: &str, journal_first: bool) -> MigrateExport {
        let order = registration_order(&spec.component_names, seed);
        let component_map = build_component_map(&order);
        let mut world = Self::empty(spec, seed, component_map);
        if journal_first {
            world.apply_journal(&spec.journal);
            for ent in &spec.entities {
                world.insert_entity(ent);
            }
        } else {
            for ent in &spec.entities {
                world.insert_entity(ent);
            }
            world.apply_journal(&spec.journal);
        }
        world.export()
    }

    fn empty(spec: &WorldSpec, seed: &str, component_map: BTreeMap<String, ComponentId>) -> Self {
        Self {
            seed: seed.to_string(),
            generation: 0,
            component_map,
            specs: spec.components.clone(),
            entities: BTreeMap::new(),
            sparse: SparseSet::new(),
            tombstones: BTreeSet::new(),
        }
    }

    fn default_align(&self, name: &str) -> u32 {
        self.specs.get(name).map(|s| s.align).unwrap_or(1)
    }

    fn parse_component(&self, name: &str, value: &ComponentData) -> Option<(ComponentId, CompInst)> {
        let id = *self.component_map.get(name)?;
        let align = value.align_override().unwrap_or_else(|| self.default_align(name));
        Some((
            id,
            CompInst {
                data: value.data().to_string(),
                align,
            },
        ))
    }

    fn insert_entity(&mut self, ent: &EntitySpec) {
        if self.tombstones.contains(&ent.id) {
            return;
        }
        self.sparse.insert(ent.id);
        let mut comps = BTreeMap::new();
        for (name, value) in &ent.components {
            if let Some((id, inst)) = self.parse_component(name, value) {
                comps.insert(id, inst);
            }
        }
        self.entities.insert(ent.id, EntityRecord { components: comps });
        self.generation += 1;
    }

    pub fn apply_journal(&mut self, journal: &[JournalOp]) {
        for op in journal {
            match op {
                JournalOp::AddComponent {
                    entity,
                    component,
                    data,
                    align,
                } => {
                    if self.tombstones.contains(entity) {
                        continue;
                    }
                    if let Some(cid) = self.component_map.get(component).copied() {
                        let default_a = self.default_align(component);
                        if let Some(rec) = self.entities.get_mut(entity) {
                            let a = align.unwrap_or(default_a);
                            rec.components.insert(
                                cid,
                                CompInst {
                                    data: data.clone(),
                                    align: a,
                                },
                            );
                            self.generation += 1;
                        }
                    }
                }
                JournalOp::RemoveComponent { entity, component } => {
                    if let Some(cid) = self.component_map.get(component).copied() {
                        if let Some(rec) = self.entities.get_mut(entity) {
                            rec.components.remove(&cid);
                            self.generation += 1;
                        }
                    }
                }
                JournalOp::RemoveEntity { entity } => {
                    self.entities.remove(entity);
                    self.sparse.remove(*entity);
                    self.generation += 1;
                }
                JournalOp::Tombstone { entity } => {
                    self.tombstones.insert(*entity);
                    self.generation += 1;
                }
                JournalOp::Spawn { entity, components } => {
                    let spec = EntitySpec {
                        id: *entity,
                        components: components.clone(),
                    };
                    self.insert_entity(&spec);
                }
            }
        }
    }

    fn archetype_rows(&self, comps: &BTreeMap<ComponentId, CompInst>) -> Vec<(ComponentId, u32)> {
        let mut rows: Vec<(ComponentId, u32)> = comps.iter().map(|(id, c)| (*id, c.align)).collect();
        rows.sort_by_key(|r| r.0);
        rows
    }

    pub fn export(&self) -> MigrateExport {
        let mut arch_counts: BTreeMap<u64, (Vec<(ComponentId, u32)>, u32)> = BTreeMap::new();
        for rec in self.entities.values() {
            let rows = self.archetype_rows(&rec.components);
            let h = archetype_hash(&rows);
            arch_counts
                .entry(h)
                .and_modify(|(_, c)| *c += 1)
                .or_insert((rows.clone(), 1));
        }
        let mut archetypes = Vec::new();
        for (hash, (rows, count)) in arch_counts {
            archetypes.push(ArchetypeOut {
                hash: format!("{:016x}", hash),
                component_ids: rows.iter().map(|r| r.0).collect(),
                alignments: rows.iter().map(|r| r.1).collect(),
                count,
            });
        }
        archetypes.sort_by(|a, b| a.hash.cmp(&b.hash));

        let mut entities = Vec::new();
        for (id, rec) in &self.entities {
            let rows = self.archetype_rows(&rec.components);
            entities.push(EntityOut {
                id: *id,
                archetype_hash: hash_hex(&rows),
                slot_generation: self.sparse.generation_of(*id),
                components: rec
                    .components
                    .iter()
                    .map(|(cid, c)| (*cid, c.data.clone()))
                    .collect(),
            });
        }
        entities.sort_by_key(|e| e.id);

        MigrateExport {
            seed: self.seed.clone(),
            generation: self.generation,
            component_map: self.component_map.clone(),
            archetypes,
            entities,
        }
    }

    pub fn query_entities(&self, query: &[ComponentId]) -> Vec<EntityId> {
        let mut want: Vec<ComponentId> = query.to_vec();
        want.sort();
        self.entities
            .iter()
            .filter(|(id, rec)| {
                if self.tombstones.contains(id) {
                    return false;
                }
                let mut have: Vec<ComponentId> = rec.components.keys().copied().collect();
                have.sort();
                want.iter().all(|c| have.contains(c))
            })
            .map(|(id, _)| *id)
            .collect()
    }

    pub fn generation(&self) -> u64 {
        self.generation
    }
}
