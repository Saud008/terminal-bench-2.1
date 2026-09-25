use anyhow::{bail, Result};

use crate::gp94::{EntityJson, MetricsJson, SceneJson, TagJson, Vec3Json};
use crate::ul82::read_optional_tag_vector;
use crate::ft26::vtable_field_abs;
use crate::kx42::{follow_uoffset, read_f32, read_u16, read_u32};

pub const ENTITY_TAGS_SLOT: usize = 3;
pub const ENTITY_PARENT_SLOT: usize = 4;
pub const ENTITY_METRICS_SLOT: usize = 5;
pub const ENTITY_POSITION_SLOT: usize = 2;
pub const ENTITY_NAME_SLOT: usize = 1;
pub const ENTITY_ID_SLOT: usize = 0;

pub const SCENE_REVISION_SLOT: usize = 0;
pub const SCENE_ROOT_SLOT: usize = 1;

pub const METRICS_DISTANCE_SLOT: usize = 0;
pub const METRICS_FLAG_SLOT: usize = 1;

pub const TAG_KEY_SLOT: usize = 0;
pub const TAG_VALUE_SLOT: usize = 1;

fn read_string_field(buf: &[u8], table: usize, slot: usize) -> Result<String> {
    let field = vtable_field_abs(buf, table, slot)?;
    read_string(buf, field)
}

fn read_vec3_inline(buf: &[u8], table: usize) -> Result<Vec3Json> {
    let field = vtable_field_abs(buf, table, ENTITY_POSITION_SLOT)?;
    Ok(Vec3Json {
        x: read_f32(buf, field + 4)?,
        y: read_f32(buf, field)?,
        z: read_f32(buf, field + 8)?,
    })
}

pub fn decode_tag(buf: &[u8], table: usize) -> Result<TagJson> {
    Ok(TagJson {
        key: read_string_field(buf, table, TAG_KEY_SLOT)?,
        value: read_string_field(buf, table, TAG_VALUE_SLOT)?,
    })
}

pub fn decode_metrics(buf: &[u8], table: usize) -> Result<MetricsJson> {
    let distance_m = match vtable_field_abs(buf, table, METRICS_DISTANCE_SLOT) {
        Ok(pos) => read_f32(buf, pos)?,
        Err(_) => 1.0,
    };
    let flag_count = match vtable_field_abs(buf, table, METRICS_FLAG_SLOT) {
        Ok(pos) => read_u16(buf, pos)?,
        Err(_) => 0,
    };
    Ok(MetricsJson {
        distance_m,
        flag_count,
    })
}

pub fn decode_entity(buf: &[u8], table: usize) -> Result<EntityJson> {
    let id = read_u32(buf, vtable_field_abs(buf, table, ENTITY_ID_SLOT)?)?;
    let name = read_string_field(buf, table, ENTITY_NAME_SLOT)?;
    let position = read_vec3_inline(buf, table)?;
    let tags = read_optional_tag_vector(buf, table)?;

    let parent = if let Ok(field) = vtable_field_abs(buf, table, ENTITY_PARENT_SLOT) {
        let nested = follow_uoffset(buf, field)?;
        Some(Box::new(decode_entity(buf, nested)?))
    } else {
        None
    };

    let metrics = if let Ok(field) = vtable_field_abs(buf, table, ENTITY_METRICS_SLOT) {
        let metrics_table = follow_uoffset(buf, field)?;
        Some(decode_metrics(buf, metrics_table)?)
    } else {
        None
    };

    Ok(EntityJson {
        id,
        name,
        position,
        tags,
        parent,
        metrics,
    })
}

pub fn decode_scene(buf: &[u8], table: usize) -> Result<SceneJson> {
    let revision = read_u32(buf, vtable_field_abs(buf, table, SCENE_REVISION_SLOT)?)?;
    let root_field = vtable_field_abs(buf, table, SCENE_ROOT_SLOT)?;
    let root_table = follow_uoffset(buf, root_field)?;
    let root = decode_entity(buf, root_table)?;
    Ok(SceneJson { revision, root })
}

fn read_string(buf: &[u8], field_pos: usize) -> Result<String> {
    let vec_pos = follow_uoffset(buf, field_pos)?;
    let len = read_u32(buf, vec_pos)? as usize;
    let start = vec_pos + 4;
    if start + len > buf.len() {
        bail!("truncated string");
    }
    Ok(String::from_utf8(buf[start..start + len].to_vec())?)
}
