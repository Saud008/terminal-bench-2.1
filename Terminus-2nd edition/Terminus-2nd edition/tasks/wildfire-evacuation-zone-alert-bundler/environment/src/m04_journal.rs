use crate::m01_geom;
use crate::m06_mesh;
use crate::m03_slot;
use crate::m05_prec;
use crate::hazard_schema::{AssignmentRow, BindBundle, WeaveLedger, ZoneAlertRow};
use sha2::{Digest, Sha256};

pub fn weave_run(run_id: &str, bundle: &BindBundle) -> WeaveLedger {
    let mut remaining = m03_slot::init_remaining(&bundle.shelters);
    let mut assignments = Vec::new();
    let mut zone_alerts = Vec::new();

    for zone in &bundle.zones {
        let mut best_ratio = 0.0f64;
        for fire in &bundle.fires {
            let ratio = m01_geom::overlap_ratio(&zone.polygon, &fire.perimeter);
            if ratio > best_ratio {
                best_ratio = ratio;
            }
        }
        let severity = m05_prec::classify_severity(best_ratio, &bundle.policy);
        if severity == "NONE" {
            continue;
        }
        let centroid = m01_geom::centroid(&zone.polygon);
        let mut best: Option<(String, f64)> = None;
        for shelter in &bundle.shelters {
            if let Some(km) = m06_mesh::shortest_path_km(&bundle.roads, &centroid, &shelter.location) {
                let replace = match &best {
                    None => true,
                    Some((_, bk)) => km < *bk,
                };
                if replace {
                    best = Some((shelter.shelter_id.clone(), km));
                }
            }
        }
        if let Some((shelter_id, routed_km)) = best {
            if m03_slot::assign_shelter(&bundle.shelters, &shelter_id, zone.population, &mut remaining) {
                let message = bundle
                    .templates
                    .get(&zone.zone_id)
                    .cloned()
                    .unwrap_or_else(|| format!("Evacuate zone {}", zone.zone_id));
                assignments.push(AssignmentRow {
                    zone_id: zone.zone_id.clone(),
                    shelter_id: shelter_id.clone(),
                    routed_km,
                    evacuees: zone.population,
                });
                zone_alerts.push(ZoneAlertRow {
                    zone_id: zone.zone_id.clone(),
                    severity,
                    shelter_id,
                    message,
                    overlap_ratio: best_ratio,
                });
            }
        }
    }

    assignments.sort_by(|a, b| a.zone_id.cmp(&b.zone_id));
    zone_alerts.sort_by(|a, b| a.zone_id.cmp(&b.zone_id));
    let body = serde_json::json!({
        "assignments": assignments,
        "run_id": run_id,
        "scenario": bundle.scenario,
        "zone_alerts": zone_alerts,
    });
    let weave_digest = format!("{:x}", Sha256::digest(body.to_string().as_bytes()));
    WeaveLedger {
        run_id: run_id.to_string(),
        scenario: bundle.scenario.clone(),
        assignments,
        zone_alerts,
        policy: bundle.policy.clone(),
        weave_digest,
    }
}
