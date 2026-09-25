use crate::rail_model::{
    ConflictLedger, ConflictRow, ConflictSummary, PossessionClaim, ScenarioFile, TopoCacheSnapshot,
    TrainReservation,
};
use crate::adj_walk;
use crate::part_sort;
use crate::rank_filter;
use crate::aspect_rule;
use crate::span_math;
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

pub fn possession_id(seed: &str, scenario: &str, load_seq: u64) -> String {
    let body = format!("{seed}:{scenario}:{load_seq}");
    let digest = Sha256::digest(body.as_bytes());
    format!("poss-{}", hex::encode(&digest[..6]))
}

pub fn build_ledger(
    cfg: &crate::rail_model::Config,
    seed: &str,
    scenario: &str,
) -> Result<ConflictLedger, String> {
    let snap = crate::topo_persist::read_snapshot(&cfg.trackgraph_cache_path)?;
    crate::topo_persist::validate_seed_scenario(&snap, seed, scenario)?;
    let path = crate::scenario_io::scenario_path(scenario);
    let sf = crate::scenario_io::load_scenario(&path)?;
    let load_seq = snap.load_seq;
    let pid = possession_id(seed, scenario, load_seq);

    let (poss, res) = rank_filter::filter_active_claims(
        &snap.zone_map,
        &sf.overrides,
        &sf.possessions,
        &sf.reservations,
    );

    let mut groups: Vec<ConflictRow> = Vec::new();
    let mut possession_pairs = 0u32;

    for i in 0..poss.len() {
        for j in (i + 1)..poss.len() {
            let a = poss[i];
            let b = poss[j];
            if !span_math::intervals_overlap(a.start_min, a.end_min, b.start_min, b.end_min) {
                continue;
            }
            if !adj_walk::protected_overlap(&snap.zone_map, &a.blocks, &b.blocks) {
                continue;
            }
            possession_pairs += 1;
            let (ws, we) = span_math::clip_window(a.start_min, a.end_min, b.start_min, b.end_min)
                .unwrap_or((0, 0));
            let mut parts = vec![a.claim_id.clone(), b.claim_id.clone()];
            parts = part_sort::stable_participants(&parts);
            let mut blocks: BTreeSet<String> = BTreeSet::new();
            for b_id in &a.blocks {
                blocks.insert(b_id.clone());
            }
            for b_id in &b.blocks {
                blocks.insert(b_id.clone());
            }
            groups.push(ConflictRow {
                group_key: part_sort::group_key(&parts),
                participants: parts,
                window_start: ws,
                window_end: we,
                blocks: blocks.into_iter().collect(),
                reasons: vec!["possession_overlap".into()],
            });
        }
    }

    for p in &poss {
        for r in &res {
            if !span_math::intervals_overlap(p.start_min, p.end_min, r.start_min, r.end_min) {
                continue;
            }
            if !adj_walk::protected_overlap(&snap.zone_map, &p.blocks, &r.blocks) {
                continue;
            }
            let (ws, we) =
                span_math::clip_window(p.start_min, p.end_min, r.start_min, r.end_min).unwrap_or((0, 0));
            let mut parts = vec![p.claim_id.clone(), r.train_id.clone()];
            parts = part_sort::stable_participants(&parts);
            let mut blocks: BTreeSet<String> = BTreeSet::new();
            for b_id in &p.blocks {
                blocks.insert(b_id.clone());
            }
            for b_id in &r.blocks {
                blocks.insert(b_id.clone());
            }
            groups.push(ConflictRow {
                group_key: part_sort::group_key(&parts),
                participants: parts,
                window_start: ws,
                window_end: we,
                blocks: blocks.into_iter().collect(),
                reasons: vec!["possession_train".into()],
            });
        }
    }

    let signal_rows = aspect_rule::collect_signal_conflicts(&sf, &snap.zone_map);
    let signal_blocked = signal_rows.len() as u32;
    for (sig_id, train_id, ws, we, blocks) in signal_rows {
        let parts = vec![sig_id, train_id];
        groups.push(ConflictRow {
            group_key: part_sort::group_key(&parts),
            participants: parts,
            window_start: ws,
            window_end: we,
            blocks,
            reasons: vec!["signal_restrict".into()],
        });
    }

    part_sort::sort_groups(&mut groups);

    let override_suppressed = count_suppressed(&sf, &snap);
    let summary = ConflictSummary {
        total_conflicts: groups.len() as u32,
        signal_blocked,
        override_suppressed,
        possession_pairs,
    };

    let mut ledger = ConflictLedger {
        seed: seed.to_string(),
        scenario: scenario.to_string(),
        possession_id: pid,
        conflict_groups: groups,
        summary,
        audit_digest: String::new(),
    };
    ledger.audit_digest = audit_digest(&ledger.summary, &ledger.conflict_groups);
    Ok(ledger)
}

fn count_suppressed(sf: &ScenarioFile, snap: &TopoCacheSnapshot) -> u32 {
    let mut n = 0u32;
    for ov in &sf.overrides {
        if ov.priority != 0 {
            continue;
        }
        for p in &sf.possessions {
            if rank_filter::claim_suppressed(
                &snap.zone_map,
                ov,
                &p.blocks,
                p.start_min,
                p.end_min,
                p.priority,
            ) {
                n += 1;
            }
        }
        for r in &sf.reservations {
            if rank_filter::claim_suppressed(
                &snap.zone_map,
                ov,
                &r.blocks,
                r.start_min,
                r.end_min,
                r.priority,
            ) {
                n += 1;
            }
        }
    }
    n
}

pub fn audit_digest(summary: &ConflictSummary, groups: &[ConflictRow]) -> String {
    let keys: Vec<String> = groups.iter().map(|g| g.group_key.clone()).collect();
    let body = serde_json::json!({
        "total_conflicts": summary.total_conflicts,
        "signal_blocked": summary.signal_blocked,
        "override_suppressed": summary.override_suppressed,
        "part_sort": keys,
    });
    let raw = serde_json::to_string(&body).unwrap_or_default();
    hex::encode(Sha256::digest(raw.as_bytes()))
}

pub fn write_ledger(path: &Path, ledger: &ConflictLedger) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let data = serde_json::to_string_pretty(ledger).map_err(|e| e.to_string())?;
    fs::write(path, format!("{data}\n")).map_err(|e| e.to_string())
}
