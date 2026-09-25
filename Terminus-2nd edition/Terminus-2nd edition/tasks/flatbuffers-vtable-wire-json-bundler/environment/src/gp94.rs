use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Vec3Json {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MetricsJson {
    pub distance_m: f32,
    pub flag_count: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TagJson {
    pub key: String,
    pub value: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EntityJson {
    pub id: u32,
    pub name: String,
    pub position: Vec3Json,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tags: Option<Vec<TagJson>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub parent: Option<Box<EntityJson>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metrics: Option<MetricsJson>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SceneJson {
    pub revision: u32,
    pub root: EntityJson,
}
