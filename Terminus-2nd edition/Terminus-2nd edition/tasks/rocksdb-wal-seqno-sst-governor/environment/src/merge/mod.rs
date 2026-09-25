pub mod engine;
pub mod operator;

use std::collections::BTreeMap;

use crate::compaction::tombstone;
use crate::types::{GovernorReport, SstFileRow, StageFile, VisibleKey, WalBatchRow};
use crate::wal::visibility;

pub fn build_governor_report(stage: &StageFile, pass: u32) -> GovernorReport {
    let selected = crate::compaction::planner::select_sst_files(&stage.sst_files, stage.watermark_seqno);
    let records = visibility::collect_records(stage, &selected);
    let masked = tombstone::apply_tombstones(records);
    let merged = operator::apply_merge_operands(masked, &stage.sst_files, &selected);
    let visible_keys = visibility::group_visible(merged, stage.snapshot_seqno);
    let reclaimed = crate::export::reclaim::sum_selected_bytes(&stage.sst_files, &selected);
    GovernorReport {
        snapshot_seqno: stage.snapshot_seqno,
        watermark_seqno: stage.watermark_seqno,
        selected_sst: selected,
        visible_keys,
        reclaimed_bytes: reclaimed,
        compact_pass: pass,
    }
}

pub fn selected_sst_rows<'a>(stage: &'a StageFile, selected: &[String]) -> Vec<&'a SstFileRow> {
    stage
        .sst_files
        .iter()
        .filter(|f| selected.iter().any(|id| id == &f.file_id))
        .collect()
}

pub fn wal_batches_sorted(batches: &[WalBatchRow]) -> Vec<&WalBatchRow> {
    let mut rows: Vec<&WalBatchRow> = batches.iter().collect();
    rows.sort_by_key(|b| b.ingest_order);
    rows
}

pub fn keys_by_cf(map: &BTreeMap<String, Vec<VisibleKey>>) -> usize {
    map.values().map(|v| v.len()).sum()
}
