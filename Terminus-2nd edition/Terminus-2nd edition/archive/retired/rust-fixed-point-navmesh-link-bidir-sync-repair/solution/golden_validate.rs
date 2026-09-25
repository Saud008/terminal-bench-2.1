use crate::graph::link::has_reverse;
use crate::model::{CellNode, MeshBundle, OffmeshSpec, PortalSpec, ValidateExport};
use crate::seed::synthetic_offmesh;
use std::collections::{HashMap, HashSet, VecDeque};

fn cell_map(mesh: &MeshBundle) -> HashMap<String, CellNode> {
    mesh.cells
        .iter()
        .map(|c| {
            (
                c.id.clone(),
                CellNode {
                    id: c.id.clone(),
                    gx: c.gx,
                    gy: c.gy,
                    walkable: c.walkable,
                    region: c.region,
                },
            )
        })
        .collect()
}

fn linear_dist_q16(a: &CellNode, b: &CellNode) -> i64 {
    let dx = (a.gx - b.gx) as i64;
    let dy = (a.gy - b.gy) as i64;
    let sq = dx * dx + dy * dy;
    let dist = (sq as f64).sqrt();
    (dist * 65536.0).round() as i64
}

fn snap_ok(a: &CellNode, b: &CellNode, snap_radius_q16: i32) -> bool {
    linear_dist_q16(a, b) <= snap_radius_q16 as i64
}

fn check_portal(cells: &HashMap<String, CellNode>, portal: &PortalSpec, errors: &mut Vec<String>) {
    if !portal.require_region_match {
        return;
    }
    let Some(from) = cells.get(&portal.from) else {
        errors.push(format!("portal {} missing from {}", portal.id, portal.from));
        return;
    };
    let Some(to) = cells.get(&portal.to) else {
        errors.push(format!("portal {} missing to {}", portal.id, portal.to));
        return;
    };
    if from.region != to.region {
        errors.push(format!(
            "portal {} region mismatch {} vs {}",
            portal.id, from.region, to.region
        ));
    }
}

fn check_offmesh(cells: &HashMap<String, CellNode>, link: &OffmeshSpec, errors: &mut Vec<String>) {
    let Some(from) = cells.get(&link.from) else {
        errors.push(format!("offmesh {} missing from cell {}", link.id, link.from));
        return;
    };
    let Some(to) = cells.get(&link.to) else {
        errors.push(format!("offmesh {} missing to cell {}", link.id, link.to));
        return;
    };
    if !snap_ok(from, to, link.snap_radius_q16) {
        errors.push(format!("offmesh {} snap radius exceeded", link.id));
    }
}

fn count_islands(mesh: &MeshBundle) -> u32 {
    let walkable: HashSet<(i32, i32)> = mesh
        .cells
        .iter()
        .filter(|c| c.walkable)
        .map(|c| (c.gx, c.gy))
        .collect();
    let mut seen = HashSet::new();
    let mut islands = 0u32;
    let dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)];

    for (gx, gy) in &walkable {
        if seen.contains(&(*gx, *gy)) {
            continue;
        }
        islands += 1;
        let mut q = VecDeque::from([(*gx, *gy)]);
        seen.insert((*gx, *gy));
        while let Some((x, y)) = q.pop_front() {
            for (dx, dy) in dirs {
                let nx = x + dx;
                let ny = y + dy;
                if walkable.contains(&(nx, ny)) && seen.insert((nx, ny)) {
                    q.push_back((nx, ny));
                }
            }
        }
    }
    islands
}

pub fn validate_mesh(mesh: &MeshBundle, seed: u64) -> ValidateExport {
    let cells = cell_map(mesh);
    let mut errors = Vec::new();
    let mut links_checked = 0u32;
    let mut portals_checked = 0u32;

    for portal in &mesh.portals {
        portals_checked += 1;
        check_portal(&cells, portal, &mut errors);
    }

    for link in &mesh.offmesh {
        links_checked += 1;
        check_offmesh(&cells, link, &mut errors);
    }

    if let Some(seed_link) = synthetic_offmesh(seed, mesh) {
        links_checked += 1;
        check_offmesh(&cells, &seed_link, &mut errors);
    }

    let islands = count_islands(mesh);

    ValidateExport {
        mesh_id: mesh.mesh_id.clone(),
        seed,
        ok: errors.is_empty(),
        errors,
        islands,
        links_checked,
        portals_checked,
    }
}

pub fn validate_bidir_links(mesh: &MeshBundle, graph: &crate::model::Graph) -> Vec<String> {
    let mut errors = Vec::new();
    let pairs: Vec<(&str, &str)> = mesh
        .edges
        .iter()
        .map(|e| (e.from.as_str(), e.to.as_str()))
        .chain(
            mesh.portals
                .iter()
                .map(|p| (p.from.as_str(), p.to.as_str())),
        )
        .chain(
            mesh.offmesh
                .iter()
                .map(|o| (o.from.as_str(), o.to.as_str())),
        )
        .collect();

    for (a, b) in pairs {
        if !has_reverse(graph, &a.to_string(), &b.to_string()) {
            errors.push(format!("missing reverse edge {b}->{a}"));
        }
    }
    errors
}
