use crate::model::{MeshBundle, OffmeshSpec, Q16};
use sha2::{Digest, Sha256};

pub fn seed_tag(seed: u64, mesh_id: &str) -> String {
    let digest = Sha256::digest(format!("{seed}:{mesh_id}").as_bytes());
    format!("{:x}", digest)[..8].to_string()
}

pub fn perturb_cost_q16(base: Q16, seed: u64) -> Q16 {
    let bump = ((seed % 511) as Q16).saturating_mul(128);
    base.saturating_add(bump)
}

pub fn synthetic_offmesh(seed: u64, mesh: &MeshBundle) -> Option<OffmeshSpec> {
    let walkable: Vec<_> = mesh.cells.iter().filter(|c| c.walkable).collect();
    if walkable.len() < 2 {
        return None;
    }
    let digest = Sha256::digest(format!("offmesh:{seed}:{}", mesh.mesh_id).as_bytes());
    let mut pairs: Vec<(&crate::model::CellSpec, &crate::model::CellSpec)> = Vec::new();
    for (i, left) in walkable.iter().enumerate() {
        for right in walkable.iter().skip(i + 1) {
            let dx = (left.gx - right.gx).abs();
            let dy = (left.gy - right.gy).abs();
            if dx + dy == 1 {
                pairs.push((left, right));
            }
        }
    }
    if pairs.is_empty() {
        return None;
    }
    let pick = digest[0] as usize % pairs.len();
    let (from_cell, to_cell) = pairs[pick];
    let cost_q16 = 196608 + ((digest[1] as Q16) % 2048) * 16;
    let snap_radius_q16 = 131072;
    Some(OffmeshSpec {
        id: format!("seed-{}", seed_tag(seed, &mesh.mesh_id)),
        from: from_cell.id.clone(),
        to: to_cell.id.clone(),
        cost_q16,
        snap_radius_q16,
    })
}
