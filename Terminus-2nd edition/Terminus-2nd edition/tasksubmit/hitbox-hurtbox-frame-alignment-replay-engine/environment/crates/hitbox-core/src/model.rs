use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Vec3 {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Hurtbox {
    pub center: [f64; 3],
    pub half_extents: [f64; 3],
    pub active_start_frame: u32,
    pub active_end_frame: u32,
    pub invuln_frames: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Hitbox {
    pub bone: String,
    pub local_offset: [f64; 3],
    pub half_extents: [f64; 3],
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Entity {
    pub entity_id: String,
    pub team: String,
    pub hurtbox: Hurtbox,
    pub hitboxes: Vec<Hitbox>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EntitiesFile {
    pub entities: Vec<Entity>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct KeyframeRecord {
    pub entity_id: String,
    pub bone: String,
    pub frame: u32,
    pub pos: [f64; 3],
    pub rot: [f64; 4],
    pub instance_id: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct HitEvent {
    pub tick: u32,
    pub frame: u32,
    pub timestamp_ms: u64,
    pub attacker_id: String,
    pub defender_id: String,
    pub instance_id: u32,
    pub bone: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct ReplayEvent {
    pub tick: u32,
    pub frame: u32,
    pub timestamp_ms: u64,
    pub entity_id: String,
    pub bone: String,
    pub event_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CollisionReport {
    pub layout_version: u32,
    pub tick_rate: u32,
    pub anim_fps: u32,
    pub hits: Vec<HitEvent>,
    pub events: Vec<ReplayEvent>,
}
