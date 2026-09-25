use crate::rollup_emit::sort;
use crate::checkpoint::lineage;
use crate::tenure_gate;
use crate::carveout;
use crate::mhz_peer;
use crate::checkpoint::wal;
use crate::coupler;
use crate::catalog_schema::{
    BandSpec, AtlasSiteRow, AtlasSummary, RfAtlasReport, LicenseGrant, GrantWalFrame,
};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn build_catalog(cfg: &crate::catalog_schema::Config, seed: &str, bundle: &str) -> Result<RfAtlasReport, String> {
    let snap = wal::read_snapshot(&cfg.wal_path)?;
    wal::validate_seed_bundle(&snap, seed, bundle)?;
    let active = lineage::read_active(cfg)?;
    if active.seed != seed || active.bundle != bundle {
        return Err("coverage generation seed/bundle mismatch".into());
    }
    let grants = to_grants(&snap);
    let band_map = band_lookup(&snap.bands);
    let mut rows = Vec::new();
    let mut expired_dropped = 0u32;
    for site in &snap.transmitters {
        let Some(lic) = coupler::pick_license_for_site(site, &grants) else {
            continue;
        };
        if !tenure_gate::license_valid(&lic.renewal_date, &snap.as_of_date) {
            expired_dropped += 1;
            continue;
        }
        let (mhz_low, mhz_high) = band_map
            .get(&site.band_id)
            .map(|b| (b.mhz_low, b.mhz_high))
            .unwrap_or((0.0, 0.0));
        let peers = mhz_peer::count_band_peers(
            &site.band_id,
            mhz_low,
            mhz_high,
            &other_bands(&snap.bands, &site.band_id),
        );
        rows.push(AtlasSiteRow {
            site_id: site.site_id.clone(),
            license_id: lic.license_id.clone(),
            holder: lic.holder.clone(),
            band_id: site.band_id.clone(),
            effective_mhz_low: mhz_low,
            effective_mhz_high: mhz_high,
            excluded: carveout::site_excluded(site, &snap.exclusions),
            overlap_peer_count: peers,
            valid_through: lic.renewal_date.clone(),
            atlas_seq_id: active.atlas_seq_id.clone(),
        });
    }
    sort::sort_rows(&mut rows);
    let summary = build_summary(&rows, expired_dropped);
    let mut cat = RfAtlasReport {
        seed: seed.to_string(),
        bundle: bundle.to_string(),
        atlas_seq_id: active.atlas_seq_id,
        catalog_rows: rows,
        summary: summary.clone(),
        audit_digest: String::new(),
    };
    cat.audit_digest = audit_digest(&summary, &cat.catalog_rows);
    Ok(cat)
}

fn to_grants(snap: &GrantWalFrame) -> Vec<LicenseGrant> {
    snap.licenses
        .iter()
        .map(|lic| LicenseGrant {
            license_id: lic.license_id.clone(),
            holder: lic.holder.clone(),
            band_id: lic.band_id.clone(),
            priority: lic.priority,
            renewal_date: lic.renewal_date.clone(),
            area: crate::catalog_schema::BBox {
                lat_min: lic.lat_min,
                lat_max: lic.lat_max,
                lon_min: lic.lon_min,
                lon_max: lic.lon_max,
            },
        })
        .collect()
}

fn band_lookup(bands: &[BandSpec]) -> BTreeMap<String, BandSpec> {
    bands
        .iter()
        .map(|b| (b.band_id.clone(), b.clone()))
        .collect()
}

fn other_bands(bands: &[BandSpec], skip: &str) -> Vec<(String, f64, f64)> {
    bands
        .iter()
        .filter(|b| b.band_id != skip)
        .map(|b| (b.band_id.clone(), b.mhz_low, b.mhz_high))
        .collect()
}

fn build_summary(rows: &[AtlasSiteRow], expired_dropped: u32) -> AtlasSummary {
    let total = rows.len() as u32;
    let excluded = rows.iter().filter(|r| r.excluded).count() as u32;
    AtlasSummary {
        total_sites: total,
        active_sites: total - excluded,
        excluded_sites: excluded,
        overlap_pairs: count_overlap_pairs(rows),
        expired_dropped,
    }
}

fn count_overlap_pairs(rows: &[AtlasSiteRow]) -> u32 {
    let mut n = 0u32;
    for i in 0..rows.len() {
        for j in (i + 1)..rows.len() {
            if rows[i].band_id != rows[j].band_id
                && mhz_peer::bands_overlap(
                    rows[i].effective_mhz_low,
                    rows[i].effective_mhz_high,
                    rows[j].effective_mhz_low,
                    rows[j].effective_mhz_high,
                )
            {
                n += 1;
            }
        }
    }
    n
}

fn audit_digest(summary: &AtlasSummary, rows: &[AtlasSiteRow]) -> String {
    let body = format!(
        r#"{{"active_sites":{},"expired_dropped":{},"overlap_pairs":{},"total_sites":{}}}"#,
        summary.active_sites,
        summary.expired_dropped,
        summary.overlap_pairs,
        summary.total_sites,
    );
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    let _ = rows.len();
    hex::encode(hasher.finalize())
}

pub fn write_catalog(path: &Path, cat: &RfAtlasReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(cat).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
