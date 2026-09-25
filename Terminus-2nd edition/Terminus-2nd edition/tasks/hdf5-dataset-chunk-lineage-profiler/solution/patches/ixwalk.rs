use crate::hdclp_types::{chunks_per_dim, IndexEntry};

const MAGIC: &[u8; 4] = b"S5IX";

pub fn parse_index(blob: &[u8], ndims: usize) -> Result<Vec<IndexEntry>, String> {
    if blob.len() < 12 {
        return Err("index too short".into());
    }
    if &blob[0..4] != MAGIC {
        return Err("bad index magic".into());
    }
    let file_ndims = u32::from_le_bytes(blob[4..8].try_into().unwrap()) as usize;
    if file_ndims != ndims {
        return Err(format!("ndims mismatch: file {file_ndims} catalog {ndims}"));
    }
    let count = u32::from_le_bytes(blob[8..12].try_into().unwrap()) as usize;
    let mut off = 12;
    let row_size = ndims * 8 + 4 + 4 + 4;
    let mut out = Vec::with_capacity(count);
    for _ in 0..count {
        if off + row_size > blob.len() {
            return Err("truncated index".into());
        }
        let mut origin = Vec::with_capacity(ndims);
        for i in 0..ndims {
            let v = u64::from_le_bytes(blob[off + i * 8..off + i * 8 + 8].try_into().unwrap());
            origin.push(v);
        }
        off += ndims * 8;
        let filter_chain_id = u32::from_le_bytes(blob[off..off + 4].try_into().unwrap());
        off += 4;
        let payload_bytes = u32::from_le_bytes(blob[off..off + 4].try_into().unwrap());
        off += 4;
        let masked_cells = u32::from_le_bytes(blob[off..off + 4].try_into().unwrap());
        off += 4;
        out.push(IndexEntry {
            origin,
            filter_chain_id,
            payload_bytes,
            masked_cells,
        });
    }
    Ok(out)
}

fn chunk_coords_row_major(linear: u64, counts: &[u64]) -> Vec<u64> {
    let mut rem = linear;
    let mut coords = vec![0u64; counts.len()];
    for axis in (0..counts.len()).rev() {
        let stride = counts[axis];
        coords[axis] = rem % stride;
        rem /= stride;
    }
    coords
}

/// Map linear chunk index to origin coordinates.
pub fn linear_to_origin(linear: u32, dims: &[u64], chunk_dims: &[u64]) -> Vec<u64> {
    let counts = chunks_per_dim(dims, chunk_dims);
    let chunk_coords = chunk_coords_row_major(linear as u64, &counts);
    chunk_coords
        .iter()
        .zip(chunk_dims.iter())
        .map(|(c, cd)| c * cd)
        .collect()
}
