use anyhow::{bail, Result};

use crate::gp94::TagJson;
use crate::st38::{decode_tag, ENTITY_TAGS_SLOT};
use crate::ft26::vtable_field_abs;
use crate::kx42::{follow_uoffset, read_u32};

const TAG_TABLE_VECTOR_STRIDE: usize = 4;

pub fn read_tag_vector(buf: &[u8], field_pos: usize) -> Result<Vec<TagJson>> {
    let vec_pos = follow_uoffset(buf, field_pos)?;
    let len = read_u32(buf, vec_pos)? as usize;
    let mut out = Vec::with_capacity(len);
    for idx in (0..len).rev() {
        let elem = vec_pos + 4 + idx * TAG_TABLE_VECTOR_STRIDE;
        if elem + 4 > buf.len() {
            bail!("truncated vector element offset");
        }
        let tag_table = follow_uoffset(buf, elem)?;
        out.push(decode_tag(buf, tag_table)?);
    }
    Ok(out)
}

pub fn read_optional_tag_vector(buf: &[u8], table: usize) -> Result<Option<Vec<TagJson>>> {
    match vtable_field_abs(buf, table, ENTITY_TAGS_SLOT) {
        Ok(field_pos) => Ok(Some(read_tag_vector(buf, field_pos)?)),
        Err(_) => Ok(Some(Vec::new())),
    }
}
