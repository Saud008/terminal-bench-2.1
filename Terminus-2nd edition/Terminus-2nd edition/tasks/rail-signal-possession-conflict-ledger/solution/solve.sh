#!/usr/bin/env bash
# Oracle solve — rail-signal-possession-conflict-ledger
set -euo pipefail
cd /app

cat > /app/src/adj_walk.rs <<'ORACLE_EOF'
use crate::rail_model::ScenarioFile;
use std::collections::{BTreeMap, HashMap, HashSet};

pub fn build_zone_map(sf: &ScenarioFile) -> BTreeMap<String, Vec<String>> {
    let blocks: Vec<String> = sf.blocks.iter().map(|b| b.block_id.clone()).collect();
    let mut neighbors: HashMap<String, HashSet<String>> = HashMap::new();
    for b in &blocks {
        neighbors.entry(b.clone()).or_default();
    }
    for edge in &sf.adjacency {
        neighbors
            .entry(edge[0].clone())
            .or_default()
            .insert(edge[1].clone());
        neighbors
            .entry(edge[1].clone())
            .or_default()
            .insert(edge[0].clone());
    }
    let mut out = BTreeMap::new();
    for b in blocks {
        let mut seen = HashSet::new();
        let mut stack = vec![b.clone()];
        while let Some(node) = stack.pop() {
            if !seen.insert(node.clone()) {
                continue;
            }
            if let Some(nbs) = neighbors.get(&node) {
                for nb in nbs {
                    if !seen.contains(nb) {
                        stack.push(nb.clone());
                    }
                }
            }
        }
        let mut zone: Vec<String> = seen.into_iter().collect();
        zone.sort();
        out.insert(b, zone);
    }
    out
}

pub fn protected_overlap(
    closure: &BTreeMap<String, Vec<String>>,
    blocks_a: &[String],
    blocks_b: &[String],
) -> bool {
    let mut set_a = HashSet::new();
    for b in blocks_a {
        if let Some(zone) = closure.get(b) {
            for z in zone {
                set_a.insert(z.clone());
            }
        }
    }
    let mut set_b = HashSet::new();
    for b in blocks_b {
        if let Some(zone) = closure.get(b) {
            for z in zone {
                set_b.insert(z.clone());
            }
        }
    }
    set_a.intersection(&set_b).next().is_some()
}
ORACLE_EOF

cat > /app/src/span_math.rs <<'ORACLE_EOF'
pub fn intervals_overlap(a_start: u64, a_end: u64, b_start: u64, b_end: u64) -> bool {
    a_start < b_end && b_start < a_end
}

pub fn clip_window(a_start: u64, a_end: u64, b_start: u64, b_end: u64) -> Option<(u64, u64)> {
    if !intervals_overlap(a_start, a_end, b_start, b_end) {
        return None;
    }
    let start = a_start.max(b_start);
    let end = a_end.min(b_end);
    Some((start, end))
}
ORACLE_EOF

cat > /app/src/aspect_rule.rs <<'ORACLE_EOF'
use crate::rail_model::{ScenarioFile, SignalRestriction, TrainReservation};
use crate::span_math;
use std::collections::{BTreeMap, HashSet};

fn reservation_zone(closure: &BTreeMap<String, Vec<String>>, res: &TrainReservation) -> HashSet<String> {
    let mut zone = HashSet::new();
    for b in &res.blocks {
        if let Some(z) = closure.get(b) {
            for x in z {
                zone.insert(x.clone());
            }
        }
    }
    zone
}

pub fn signal_blocks_reservation(
    closure: &BTreeMap<String, Vec<String>>,
    sig: &SignalRestriction,
    res: &TrainReservation,
) -> bool {
    if sig.aspect != "restrict" {
        return false;
    }
    let sig_zone: HashSet<String> = closure
        .get(&sig.block_id)
        .map(|z| z.iter().cloned().collect())
        .unwrap_or_else(|| HashSet::from([sig.block_id.clone()]));
    let res_zone = reservation_zone(closure, res);
    !sig_zone.is_disjoint(&res_zone)
}

pub fn collect_signal_conflicts(
    sf: &ScenarioFile,
    closure: &BTreeMap<String, Vec<String>>,
    reservations: &[TrainReservation],
) -> Vec<(String, String, u64, u64, Vec<String>)> {
    let mut out = Vec::new();
    for sig in &sf.signals {
        if sig.aspect != "restrict" {
            continue;
        }
        for res in reservations {
            if !span_math::intervals_overlap(
                sig.start_min,
                sig.end_min,
                res.start_min,
                res.end_min,
            ) {
                continue;
            }
            if !signal_blocks_reservation(closure, sig, res) {
                continue;
            }
            let window = span_math::clip_window(
                sig.start_min,
                sig.end_min,
                res.start_min,
                res.end_min,
            )
            .unwrap_or((0, 0));
            let mut blocks = vec![sig.block_id.clone()];
            blocks.extend(res.blocks.clone());
            blocks.sort();
            blocks.dedup();
            out.push((
                sig.signal_id.clone(),
                res.train_id.clone(),
                window.0,
                window.1,
                blocks,
            ));
        }
    }
    out
}
ORACLE_EOF

cat > /app/src/rank_filter.rs <<'ORACLE_EOF'
use crate::rail_model::{CrisisOverride, PossessionClaim, TrainReservation};
use crate::span_math;
use std::collections::{BTreeMap, HashSet};

fn claim_zone(closure: &BTreeMap<String, Vec<String>>, blocks: &[String]) -> HashSet<String> {
    let mut zone = HashSet::new();
    for b in blocks {
        if let Some(z) = closure.get(b) {
            for x in z {
                zone.insert(x.clone());
            }
        }
    }
    zone
}

pub fn claim_suppressed(
    closure: &BTreeMap<String, Vec<String>>,
    ov: &CrisisOverride,
    blocks: &[String],
    start: u64,
    end: u64,
    priority: u32,
) -> bool {
    if priority == 0 || ov.priority != 0 {
        return false;
    }
    if !span_math::intervals_overlap(start, end, ov.start_min, ov.end_min) {
        return false;
    }
    let ov_zone = claim_zone(closure, &ov.blocks);
    let c_zone = claim_zone(closure, blocks);
    !ov_zone.is_disjoint(&c_zone)
}

pub fn filter_active_claims<'a>(
    closure: &BTreeMap<String, Vec<String>>,
    overrides: &'a [CrisisOverride],
    possessions: &'a [PossessionClaim],
    reservations: &'a [TrainReservation],
) -> (Vec<&'a PossessionClaim>, Vec<&'a TrainReservation>) {
    let mut poss: Vec<&PossessionClaim> = possessions.iter().collect();
    let mut res: Vec<&TrainReservation> = reservations.iter().collect();
    for ov in overrides {
        poss.retain(|p| {
            !claim_suppressed(
                closure,
                ov,
                &p.blocks,
                p.start_min,
                p.end_min,
                p.priority,
            )
        });
        res.retain(|r| {
            !claim_suppressed(
                closure,
                ov,
                &r.blocks,
                r.start_min,
                r.end_min,
                r.priority,
            )
        });
    }
    (poss, res)
}
ORACLE_EOF

sed -i 's/load_seq: prev,/load_seq: prev + 1,/' /app/src/topo_persist.rs

cat > /app/src/part_sort.rs <<'ORACLE_EOF'
use crate::rail_model::ConflictRow;

fn salt() -> String {
    std::env::var("TB3_ZONE_SALT").unwrap_or_default()
}

pub fn group_key(participants: &[String]) -> String {
    let parts = stable_participants(participants);
    parts.join("|")
}

pub fn sort_groups(groups: &mut [ConflictRow]) {
    groups.sort_by(|a, b| a.group_key.cmp(&b.group_key));
}

pub fn stable_participants(ids: &[String]) -> Vec<String> {
    let mut out: Vec<String> = ids.to_vec();
    let s = salt();
    if !s.is_empty() {
        for x in &mut out {
            x.push_str(&s);
        }
    }
    out.sort();
    out
}
ORACLE_EOF

cat > /app/src/ledger_emit.rs <<'ORACLE_EOF'
use crate::rail_model::{
    ConflictLedger, ConflictRow, ConflictSummary, PossessionClaim, ScenarioFile, TopoCacheSnapshot,
    TrainReservation,
};
use crate::part_sort;
use crate::rank_filter;
use crate::aspect_rule;
use crate::span_math;
use crate::adj_walk;
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

pub fn possession_id(seed: &str, scenario: &str, load_seq: u64) -> String {
    let body = format!("{seed}:{scenario}:{load_seq}");
    let digest = Sha256::digest(body.as_bytes());
    format!("poss-{}", hex::encode(&digest[..6]))
}

fn block_km_order(sf: &ScenarioFile, mut ids: Vec<String>) -> Vec<String> {
    ids.sort_by(|a, b| {
        let ka = (sf
            .blocks
            .iter()
            .find(|r| r.block_id == *a)
            .map(|r| r.kilometer)
            .unwrap_or(0.0)
            * 1000.0) as i64;
        let kb = (sf
            .blocks
            .iter()
            .find(|r| r.block_id == *b)
            .map(|r| r.kilometer)
            .unwrap_or(0.0)
            * 1000.0) as i64;
        ka.cmp(&kb).then_with(|| a.cmp(b))
    });
    ids
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
            let parts = part_sort::stable_participants(&[a.claim_id.clone(), b.claim_id.clone()]);
            let mut blocks: BTreeSet<String> = BTreeSet::new();
            for b_id in &a.blocks {
                blocks.insert(b_id.clone());
            }
            for b_id in &b.blocks {
                blocks.insert(b_id.clone());
            }
            let block_list = block_km_order(&sf, blocks.into_iter().collect());
            groups.push(ConflictRow {
                group_key: parts.join("|"),
                participants: parts,
                window_start: ws,
                window_end: we,
                blocks: block_list,
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
            let parts = part_sort::stable_participants(&[p.claim_id.clone(), r.train_id.clone()]);
            let mut blocks: BTreeSet<String> = BTreeSet::new();
            for b_id in &p.blocks {
                blocks.insert(b_id.clone());
            }
            for b_id in &r.blocks {
                blocks.insert(b_id.clone());
            }
            let block_list = block_km_order(&sf, blocks.into_iter().collect());
            groups.push(ConflictRow {
                group_key: parts.join("|"),
                participants: parts,
                window_start: ws,
                window_end: we,
                blocks: block_list,
                reasons: vec!["possession_train".into()],
            });
        }
    }

    let res_owned: Vec<TrainReservation> = res.iter().map(|r| (*r).clone()).collect();
    let signal_rows = aspect_rule::collect_signal_conflicts(&sf, &snap.zone_map, &res_owned);
    let signal_blocked = signal_rows.len() as u32;
    for (sig_id, train_id, ws, we, blocks) in signal_rows {
        let parts = part_sort::stable_participants(&[sig_id, train_id]);
        let block_list = block_km_order(&sf, blocks);
        groups.push(ConflictRow {
            group_key: parts.join("|"),
            participants: parts,
            window_start: ws,
            window_end: we,
            blocks: block_list,
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
    let mut keys: Vec<String> = groups.iter().map(|g| g.group_key.clone()).collect();
    keys.sort();
    let body = serde_json::json!({
        "possession_pairs": summary.possession_pairs,
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
ORACLE_EOF

cargo build --release --locked
cp /app/target/release/railpos /app/bin/railpos

bash /app/scripts/reset-state.sh
/app/bin/railpos compile-trackgraph --seed oracle-smoke --scenario linear-chain
/app/bin/railpos emit-conflicts --seed oracle-smoke --scenario linear-chain --output /app/output/oracle-smoke-linear-chain-conflicts.json
