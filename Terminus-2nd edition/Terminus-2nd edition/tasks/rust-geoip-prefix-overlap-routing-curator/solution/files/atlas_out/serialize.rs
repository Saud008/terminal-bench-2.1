use crate::asn_lineage;
use crate::cidr_contain;
use crate::emit_order;
use crate::filter_reserved;
use crate::generation_store;
use crate::feed_tiebreak;
use crate::feed_cache_store;
use crate::types::{Config, OverlapReport, OverlapRow, OverlapSummary, StagedRecord};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn build_report(cfg: &Config, seed: &str, bundle: &str) -> Result<OverlapReport, String> {
    let snap = feed_cache_store::read_snapshot(&cfg.feed_cache_path)?;
    feed_cache_store::validate_seed_bundle(&snap, seed, bundle)?;
    let active = generation_store::read_active(cfg)?;
    if active.seed != seed || active.bundle != bundle {
        return Err("overlap-generation ledger seed/bundle mismatch".into());
    }
    let (filtered, reserved_dropped) =
        filter_reserved::filter_records(snap.records.clone(), |r| &r.cidr);
    let winner_rows = feed_tiebreak::resolve_records(&filtered);
    let mut rows = build_rows(&filtered, &winner_rows);
    emit_order::sort_rows(&mut rows);
    let summary = OverlapSummary {
        total_prefixes: rows.len() as u32,
        overlap_pairs: count_overlap_pairs(&rows),
        asn_conflicts: asn_lineage::count_asn_conflicts(&asn_tuples(&rows)),
        reserved_dropped,
    };
    let mut rep = OverlapReport {
        seed: seed.to_string(),
        bundle: bundle.to_string(),
        reconcile_id: active.reconcile_id,
        overlap_rows: rows,
        summary: summary.clone(),
        audit_digest: String::new(),
    };
    rep.audit_digest = audit_digest(&summary, &rep.overlap_rows);
    Ok(rep)
}

fn build_rows(all: &[StagedRecord], winner_rows: &[StagedRecord]) -> Vec<OverlapRow> {
    let mut by_cidr: BTreeMap<String, Vec<&StagedRecord>> = BTreeMap::new();
    for rec in all {
        by_cidr.entry(rec.cidr.clone()).or_default().push(rec);
    }
    let mut winners: BTreeMap<String, &StagedRecord> = BTreeMap::new();
    for rec in winner_rows {
        winners.insert(rec.cidr.clone(), rec);
    }
    let mut out = Vec::new();
    for (cidr, group) in by_cidr {
        let winner = winners.get(&cidr).copied().unwrap_or(group[0]);
        let lineage_ids: Vec<&str> = group.iter().map(|r| r.lineage_id.as_str()).collect();
        let lineage = asn_lineage::collect_lineage(&lineage_ids);
        let contained_by = find_container(&cidr, &winners);
        out.push(OverlapRow {
            cidr: cidr.clone(),
            country: winner.country.clone(),
            asn: winner.asn,
            winning_feed: winner.feed_id.clone(),
            contained_by,
            asn_lineage: lineage,
            reserved_filtered: false,
        });
    }
    out
}

fn find_container(cidr: &str, winners: &BTreeMap<String, &StagedRecord>) -> Option<String> {
    let mut best: Option<String> = None;
    let mut best_len = 0u8;
    for (other, _) in winners {
        if other != cidr && cidr_contain::contains(other, cidr) {
            let pl = prefix_len(other);
            if best.is_none() || pl > best_len {
                best = Some(other.clone());
                best_len = pl;
            }
        }
    }
    best
}

fn prefix_len(cidr: &str) -> u8 {
    cidr.split('/').nth(1).and_then(|s| s.parse().ok()).unwrap_or(0)
}

fn count_overlap_pairs(rows: &[OverlapRow]) -> u32 {
    let mut n = 0u32;
    for i in 0..rows.len() {
        for j in (i + 1)..rows.len() {
            let a = &rows[i];
            let b = &rows[j];
            if (a.country != b.country || a.asn != b.asn)
                && (cidr_contain::contains(&a.cidr, &b.cidr)
                    || cidr_contain::contains(&b.cidr, &a.cidr))
            {
                n += 1;
            }
        }
    }
    n
}

fn asn_tuples(rows: &[OverlapRow]) -> Vec<(String, u32, Vec<String>)> {
    rows.iter()
        .map(|r| (r.cidr.clone(), r.asn, r.asn_lineage.clone()))
        .collect()
}

fn audit_digest(summary: &OverlapSummary, rows: &[OverlapRow]) -> String {
    let mut chains: Vec<Vec<String>> = rows.iter().map(|r| r.asn_lineage.clone()).collect();
    chains.sort();
    let body = format!(
        "{{\"asn_conflicts\":{},\"asn_lineage_chains\":{},\"overlap_pairs\":{},\"reserved_dropped\":{},\"total_prefixes\":{}}}",
        summary.asn_conflicts,
        serde_json::to_string(&chains).unwrap_or_else(|_| "[]".into()),
        summary.overlap_pairs,
        summary.reserved_dropped,
        summary.total_prefixes
    );
    let digest_body = body;
    let mut hasher = Sha256::new();
    hasher.update(digest_body.as_bytes());
    hex::encode(hasher.finalize())
}

pub fn write_report(path: &Path, rep: &OverlapReport) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(rep).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
