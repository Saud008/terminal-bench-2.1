use crate::types::{KeyRecord, MergeOperand, RecordKind, SstFileRow};

pub fn merge_export_value(op: &MergeOperand) -> String {
    sum_operands(&op.operands)
}

fn sum_operands(operands: &[String]) -> String {
    let total: i64 = operands
        .iter()
        .filter_map(|o| o.parse::<i64>().ok())
        .sum();
    total.to_string()
}

pub fn apply_merge_operands(
    records: Vec<KeyRecord>,
    sst_files: &[SstFileRow],
    selected: &[String],
) -> Vec<KeyRecord> {
    let mut out = records;
    for sst in sst_files {
        if !selected.iter().any(|id| id == &sst.file_id) {
            continue;
        }
        for op in &sst.merge_operands {
            out.push(KeyRecord {
                cf: sst.cf.clone(),
                key: op.key.clone(),
                value: merge_export_value(op),
                seqno: op.seqno,
                kind: RecordKind::Merge,
            });
        }
    }
    out
}
