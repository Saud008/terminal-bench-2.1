use crate::collision::family;
use crate::demux::{barcode, pair_sync, umi};
use crate::lane;
use crate::staging;
use crate::types::{DemuxEntry, LedgerFile};

pub fn run_demux(staging_path: &str, ledger_path: &str) -> Result<(), String> {
    let staging = staging::load_staging(staging_path)?;
    let synced = pair_sync::filter_synced_pairs(&staging.pairs);
    let bias = umi::tb3_seed_shift_bias();

    let mut entries = Vec::new();
    for pair in synced {
        let samples = lane::effective_samples(&staging, &pair.lane_id);
        let Some(sample_id) = barcode::match_sample(&pair.r1_barcode, &samples, staging.mismatch_budget)
        else {
            continue;
        };

        let lane_cfg = staging::lane_by_id(&staging, &pair.lane_id)
            .ok_or_else(|| format!("unknown lane {}", pair.lane_id))?;
        let shift = lane_cfg.seed_shift + bias;

        let r1_canonical = umi::canonical_r1(&pair.r1_umi, shift);
        let r2_canonical = umi::canonical_r2(&pair.r2_umi, shift);
        let canonical_umi = umi::pair_canonical(&r1_canonical, &r2_canonical);

        entries.push(DemuxEntry {
            pair_id: pair.pair_id,
            lane_id: pair.lane_id,
            sample_id,
            r1_canonical,
            r2_canonical,
            canonical_umi,
        });
    }

    entries.sort_by(|a, b| a.pair_id.cmp(&b.pair_id));
    let clusters = family::build_clusters(&entries);

    let prev = staging::load_ledger(ledger_path).ok();
    let demux_seq = prev.as_ref().map(|l| l.demux_seq + 1).unwrap_or(1);

    let ledger = LedgerFile {
        demux_seq,
        ingest_seq: staging.ingest_seq,
        entries,
        clusters,
    };

    staging::save_ledger(ledger_path, &ledger)
}
