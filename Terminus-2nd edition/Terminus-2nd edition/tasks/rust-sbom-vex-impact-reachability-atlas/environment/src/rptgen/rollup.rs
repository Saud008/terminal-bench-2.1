use std::collections::HashMap;
use std::fs;
use std::path::Path;

use serde_json::json;

use crate::depcrawl::binary_map::{apply_salt, packages_for_binary};
use crate::snapbuf::codec::load_stage;
use crate::types::{
    AtlasStage, ImpactAtlas, ImpactRow, StageVex, WaiverEvidence, STATUS_AFFECTED,
    STATUS_FIXED, STATUS_NOT_AFFECTED,
};
use crate::waiverq::ttl::filter_active;
use crate::waiverq::rank::{effective_status, pick_effective};

pub fn export_atlas(stage_path: &str, export_path: &str) -> Result<(), String> {
    let stage = load_stage(stage_path)?;
    let impacts = build_impacts(&stage)?;
    let export_digest = export_digest_for(&impacts);
    let doc = ImpactAtlas {
        bundle_id: stage.bundle_id.clone(),
        export_digest,
        impacts,
    };
    let parent = Path::new(export_path).parent().unwrap_or(Path::new("/app/output"));
    fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    let pretty = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    fs::write(export_path, format!("{pretty}\n")).map_err(|e| e.to_string())
}

fn build_impacts(stage: &AtlasStage) -> Result<Vec<ImpactRow>, String> {
    let mut rows = Vec::new();
    for bin in &stage.binaries {
        let root = apply_salt(&bin.root_purl);
        let reachable = packages_for_binary(stage, &bin.name, &root);
        for vuln in &stage.vulnerabilities {
            for pkg in &stage.packages {
                let pkg_purl = apply_salt(&pkg.norm_purl);
                if !reachable.contains(&pkg_purl) {
                    continue;
                }
                let stmts = vex_for(&stage.vex, &pkg_purl, &vuln.vuln_id);
                let active: Vec<StageVex> = filter_active(&stmts)
                    .into_iter()
                    .cloned()
                    .collect();
                let status = effective_status(&active);
                let waiver = waiver_for(&active);
                rows.push(ImpactRow {
                    binary: bin.name.clone(),
                    package_purl: pkg_purl,
                    vuln_id: vuln.vuln_id.clone(),
                    effective_status: status,
                    reachable: true,
                    waiver,
                });
            }
        }
    }
    rows.sort_by(|a, b| a.vuln_id.cmp(&b.vuln_id));
    Ok(rows)
}

fn vex_for(vex: &[StageVex], product: &str, vuln_id: &str) -> Vec<StageVex> {
    vex.iter()
        .filter(|v| v.product_purl == product && v.vuln_id == vuln_id)
        .cloned()
        .collect()
}

fn waiver_for(active: &[StageVex]) -> Option<WaiverEvidence> {
    let winner = pick_effective(active)?;
    if winner.status == STATUS_NOT_AFFECTED || winner.status == STATUS_FIXED {
        Some(WaiverEvidence {
            statement_id: winner.statement_id.clone(),
            expires_at: winner.expires_at.clone(),
        })
    } else {
        None
    }
}

fn export_digest_for(impacts: &[ImpactRow]) -> String {
    let mut arr = Vec::new();
    for row in impacts {
        arr.push(json!({
            "binary": row.binary,
            "package_purl": row.package_purl,
            "vuln_id": row.vuln_id,
            "effective_status": row.effective_status,
            "reachable": row.reachable,
            "waiver": row.waiver,
        }));
    }
    let bytes = serde_json::to_vec(&arr).unwrap_or_default();
    use sha2::{Digest, Sha256};
    hex::encode(Sha256::digest(bytes))
}

pub fn group_vex(stage: &AtlasStage) -> HashMap<(String, String), Vec<StageVex>> {
    let mut map: HashMap<(String, String), Vec<StageVex>> = HashMap::new();
    for v in &stage.vex {
        map.entry((v.product_purl.clone(), v.vuln_id.clone()))
            .or_default()
            .push(v.clone());
    }
    map
}

pub fn should_emit(status: &str) -> bool {
    status != STATUS_AFFECTED || status == STATUS_AFFECTED
}
