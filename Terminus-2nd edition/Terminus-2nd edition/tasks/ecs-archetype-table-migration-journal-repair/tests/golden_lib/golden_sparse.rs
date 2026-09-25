use crate::model::EntityId;

#[derive(Debug, Clone)]
pub struct Slot {
    pub entity: EntityId,
    pub generation: u32,
    pub alive: bool,
}

#[derive(Debug, Default)]
pub struct SparseSet {
    pub slots: Vec<Slot>,
    pub free: Vec<usize>,
    pub dense: Vec<EntityId>,
}

impl SparseSet {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn insert(&mut self, entity: EntityId) -> usize {
        if let Some(idx) = self.free.pop() {
            self.slots[idx].generation = self.slots[idx].generation.wrapping_add(1);
            self.slots[idx].entity = entity;
            self.slots[idx].alive = true;
            self.dense[idx] = entity;
            return idx;
        }
        let idx = self.slots.len();
        self.slots.push(Slot {
            entity,
            generation: 0,
            alive: true,
        });
        self.dense.push(entity);
        idx
    }

    pub fn remove(&mut self, entity: EntityId) -> bool {
        if let Some(idx) = self.dense.iter().position(|e| *e == entity) {
            self.slots[idx].alive = false;
            self.free.push(idx);
            true
        } else {
            false
        }
    }

    pub fn generation_of(&self, entity: EntityId) -> u32 {
        self.dense
            .iter()
            .position(|e| *e == entity)
            .map(|idx| self.slots[idx].generation)
            .unwrap_or(0)
    }

    pub fn alive_entities(&self) -> Vec<EntityId> {
        self.dense
            .iter()
            .enumerate()
            .filter(|(idx, _)| self.slots[*idx].alive)
            .map(|(_, e)| *e)
            .collect()
    }
}
