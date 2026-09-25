#[path = "../protocol/geodesy_models.rs"]
mod types;
#[path = "../station_bundle/read_campaign.rs"]
mod station_bundle;
#[path = "../geoid_shift/vector.rs"]
mod geoid_shift;
#[path = "../micro_quant/scale.rs"]
mod micro_quant;
#[path = "../antimeridian_cut/segment.rs"]
mod antimeridian_cut;
#[path = "../overlap_veto/pair.rs"]
mod overlap_veto;
#[path = "../campaign_lattice/write_ledger.rs"]
mod campaign_lattice;
#[path = "../geohull_rows/row_order.rs"]
mod geohull_rows;
#[path = "../seal_digest/hexline.rs"]
mod seal_digest;
#[path = "../atlas_write/sheet.rs"]
mod atlas_write;
#[path = "../decoy/flux_index_stub.rs"]
mod decoy;

pub use station_bundle::*;
pub use atlas_write::*;
pub use geohull_rows::*;
pub use overlap_veto::*;
pub use seal_digest::*;
pub use campaign_lattice::*;
pub use micro_quant::*;
pub use geoid_shift::*;
pub use types::*;
pub use antimeridian_cut::*;

use std::env;
use std::fs;
use std::path::Path;

pub fn load_config() -> Config {
    let raw = fs::read_to_string("/app/config/stationclos.json").expect("config");
    let mut cfg: Config = serde_json::from_str(&raw).expect("config json");
    if let Ok(v) = env::var("TB3_MICRO_SCALE") {
        if let Ok(n) = v.parse::<i64>() {
            if n > 0 {
                cfg.microdegree_scale = n;
            }
        }
    }
    cfg
}

pub fn materialize_hulls(campaign_id: &str, bundle_name: &str) -> Result<(), String> {
    let cfg = load_config();
    let bundle_path = Path::new(&cfg.bundle_dir).join(format!("{bundle_name}.json"));
    let bundle = load_bundle(&bundle_path)?;

    let mut expanded: Vec<(String, Vec<[f64; 2]>)> = Vec::new();
    for st in &bundle.stations {
        let residual = apply_residual(&st.vertices, &cfg.datum_offset);
        let parts = partition_wrap(&st.station_id, &residual);
        expanded.extend(parts);
    }

    let mut stations: Vec<LatticeStation> = Vec::new();
    for (sid, verts) in expanded {
        let quantized: Vec<[f64; 2]> = verts
            .iter()
            .map(|v| [quantize_coord(v[0], cfg.microdegree_scale), quantize_coord(v[1], cfg.microdegree_scale)])
            .collect();
        let (min_x, min_y, max_x, max_y) = bbox_of(&quantized);
        let area = area_u64(min_x, min_y, max_x, max_y, cfg.microdegree_scale);
        stations.push(LatticeStation {
            station_id: sid,
            residual_vertices: verts,
            quantized_vertices: quantized.clone(),
            min_x,
            min_y,
            max_x,
            max_y,
            residual_area_u64: area,
            vertex_count: quantized.len(),
        });
    }

    if let Some((a, b)) = first_conflict(&stations) {
        let _ = clear_lattice(&cfg.lattice_dir, campaign_id);
        return Err(format!("residual conflict between {a} and {b}"));
    }

    let prior = read_lattice(&cfg.lattice_dir, campaign_id).ok();
    let gen = prior.map(|p| p.materialize_generation + 1).unwrap_or(1);
    let art = LatticeArtifact {
        materialize_generation: gen,
        campaign_id: campaign_id.to_string(),
        bundle: bundle_name.to_string(),
        microdegree_scale: cfg.microdegree_scale,
        stations,
    };
    write_lattice(&cfg.lattice_dir, &art)?;
    let _ = decoy::unused_rtree_hint();
    Ok(())
}

pub fn certify_campaign(campaign_id: &str, output: &Path) -> Result<(), String> {
    let cfg = load_config();
    let art = read_lattice(&cfg.lattice_dir, campaign_id)?;
    let ranked = rank_stations(&art.stations);
    let digest = closure_digest(&ranked);
    let atlas = build_atlas(campaign_id, &ranked, &digest);
    let parent = output.parent().unwrap_or(Path::new("."));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let body = serde_json::to_string_pretty(&atlas).map_err(|e| e.to_string())?;
    fs::write(output, body + "\n").map_err(|e| e.to_string())?;
    Ok(())
}

fn bbox_of(verts: &[[f64; 2]]) -> (f64, f64, f64, f64) {
    let mut min_x = f64::INFINITY;
    let mut min_y = f64::INFINITY;
    let mut max_x = f64::NEG_INFINITY;
    let mut max_y = f64::NEG_INFINITY;
    for v in verts {
        min_x = min_x.min(v[0]);
        min_y = min_y.min(v[1]);
        max_x = max_x.max(v[0]);
        max_y = max_y.max(v[1]);
    }
    (min_x, min_y, max_x, max_y)
}

fn area_u64(min_x: f64, min_y: f64, max_x: f64, max_y: f64, scale: i64) -> u64 {
    let dx = max_x - min_x;
    let dy = max_y - min_y;
    if dx <= 0.0 || dy <= 0.0 {
        return 0;
    }
    let sx = (dx * scale as f64).round() as i64;
    let sy = (dy * scale as f64).round() as i64;
    if sx <= 0 || sy <= 0 {
        0
    } else {
        (sx as u64).saturating_mul(sy as u64)
    }
}
