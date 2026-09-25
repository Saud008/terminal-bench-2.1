use crate::bind_manifest;
use crate::entitlement_window;
use crate::marine_closure;
use crate::models::{LedgerHeader, SeasonPack, StagedLanding};
use crate::round_weight;
use crate::taxon_registry;
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Write};

// Bind landing rows into JSONL harvest ledger lines.
pub fn write_jsonl_ledger(token: &str, pack: &SeasonPack) -> Result<(LedgerHeader, Vec<StagedLanding>), String> {
    let mut rows: Vec<StagedLanding> = Vec::new();
    for landing in &pack.landings {
        let resolved = taxon_registry::resolve_species_code(&landing.species_code, &pack.species_aliases);
        let factor = pack
            .conversion_factors
            .get(&resolved)
            .copied()
            .unwrap_or(1.0);
        let live = round_weight::live_kg_from_product(landing.product_weight_kg, factor);
        let mut accepted = true;
        let mut reject_reason = String::new();

        if let Some(permit_spec) = pack.permits.get(&landing.vessel_id) {
            if !entitlement_window::permit_covers_landing(
                &landing.landed_at,
                &permit_spec.valid_from,
                &permit_spec.valid_until,
            ) {
                accepted = false;
                reject_reason = "permit_expired".into();
            } else if !entitlement_window::species_on_permit(&resolved, &permit_spec.species) {
                accepted = false;
                reject_reason = "species_not_permitted".into();
            }
        } else {
            accepted = false;
            reject_reason = "missing_permit".into();
        }

        if accepted {
            for area in &pack.closed_areas {
                if marine_closure::point_blocked_by_closure(
                    landing.lat,
                    landing.lon,
                    &landing.landed_at,
                    area,
                ) {
                    accepted = false;
                    reject_reason = format!("closed_area:{}", area.area_id);
                    break;
                }
            }
        }

        rows.push(StagedLanding {
            landing_id: landing.landing_id.clone(),
            vessel_id: landing.vessel_id.clone(),
            species_raw: landing.species_code.clone(),
            species_resolved: resolved,
            product_weight_kg: landing.product_weight_kg,
            live_weight_kg: live,
            landed_at: landing.landed_at.clone(),
            accepted,
            reject_reason,
        });
    }
    rows.sort_by(|a, b| a.landing_id.cmp(&b.landing_id));

    fs::create_dir_all(crate::VAR_ROOT).map_err(|e| e.to_string())?;
    let mut out = File::create(bind_manifest::ledger_path(token)).map_err(|e| e.to_string())?;
    for row in &rows {
        let line = serde_json::to_string(row).map_err(|e| e.to_string())?;
        writeln!(out, "{line}").map_err(|e| e.to_string())?;
    }

    let body = serde_json::json!({
        "row_count": rows.len(),
        "run_token": token,
        "season": pack.season,
    });
    let ledger_fingerprint = format!("{:x}", Sha256::digest(body.to_string().as_bytes()));
    let header = LedgerHeader {
        run_token: token.to_string(),
        season: pack.season.clone(),
        row_count: rows.len(),
        ledger_fingerprint,
    };
    fs::write(
        bind_manifest::header_path(token),
        serde_json::to_string_pretty(&header).unwrap(),
    )
    .map_err(|e| e.to_string())?;
    Ok((header, rows))
}

pub fn read_jsonl_rows(token: &str) -> Result<Vec<StagedLanding>, String> {
    let file = File::open(bind_manifest::ledger_path(token)).map_err(|e| e.to_string())?;
    let reader = BufReader::new(file);
    let mut rows = Vec::new();
    for line in reader.lines() {
        let line = line.map_err(|e| e.to_string())?;
        if line.trim().is_empty() {
            continue;
        }
        rows.push(serde_json::from_str(&line).map_err(|e| e.to_string())?);
    }
    Ok(rows)
}
