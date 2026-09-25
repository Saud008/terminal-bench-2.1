use std::collections::BTreeMap;

use crate::merge::engine::apply_key_prefix;
use crate::types::{KeyRecord, RecordKind, StageFile, VisibleKey, WalBatchRow};

pub fn batch_visible(batch: &WalBatchRow, snapshot_seqno: u64) -> bool {
    batch.committed && batch.seqno <= snapshot_seqno
}

pub fn collect_records(stage: &StageFile, selected: &[String]) -> Vec<KeyRecord> {
    let mut out = Vec::new();
    let mut batches: Vec<&WalBatchRow> = stage.wal_batches.iter().collect();
    batches.sort_by_key(|b| b.ingest_order);

    for batch in batches {
        if !batch_visible(batch, stage.snapshot_seqno) {
            continue;
        }
        for put in &batch.puts {
            out.push(KeyRecord {
                cf: batch.cf.clone(),
                key: apply_key_prefix(&put.key),
                value: put.value.clone(),
                seqno: put.seqno,
                kind: RecordKind::Put,
            });
        }
        for tomb in &batch.point_tombstones {
            out.push(KeyRecord {
                cf: batch.cf.clone(),
                key: apply_key_prefix(&tomb.key),
                value: String::new(),
                seqno: tomb.seqno,
                kind: RecordKind::PointTombstone,
            });
        }
    }

    for sst in &stage.sst_files {
        if !selected.iter().any(|id| id == &sst.file_id) {
            continue;
        }
        for key in &sst.keys {
            out.push(KeyRecord {
                cf: sst.cf.clone(),
                key: apply_key_prefix(&key.key),
                value: key.value.clone(),
                seqno: key.seqno,
                kind: RecordKind::Put,
            });
        }
        for tomb in &sst.point_tombstones {
            out.push(KeyRecord {
                cf: sst.cf.clone(),
                key: apply_key_prefix(&tomb.key),
                value: String::new(),
                seqno: tomb.seqno,
                kind: RecordKind::PointTombstone,
            });
        }
        for rt in &sst.range_tombstones {
            out.push(KeyRecord {
                cf: sst.cf.clone(),
                key: rt.start.clone(),
                value: rt.end.clone(),
                seqno: rt.seqno,
                kind: RecordKind::RangeTombstone,
            });
        }
    }
    out
}

pub fn group_visible(records: Vec<KeyRecord>, _snapshot_seqno: u64) -> BTreeMap<String, Vec<VisibleKey>> {
    let mut latest: BTreeMap<(String, String), VisibleKey> = BTreeMap::new();
    for rec in records {
        if rec.kind != RecordKind::Put && rec.kind != RecordKind::Merge {
            continue;
        }
        let key = (rec.cf.clone(), rec.key.clone());
        let entry = latest
            .entry(key)
            .or_insert(VisibleKey {
                key: rec.key.clone(),
                value: rec.value.clone(),
                seqno: rec.seqno,
            });
        if rec.seqno >= entry.seqno {
            *entry = VisibleKey {
                key: rec.key,
                value: rec.value,
                seqno: rec.seqno,
            };
        }
    }
    let mut by_cf: BTreeMap<String, Vec<VisibleKey>> = BTreeMap::new();
    for ((cf, _), vis) in latest {
        by_cf.entry(cf).or_default().push(vis);
    }
    for keys in by_cf.values_mut() {
        keys.sort_by(|a, b| a.key.cmp(&b.key));
    }
    by_cf
}
