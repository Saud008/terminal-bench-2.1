use std::collections::BTreeMap;

use crate::error::Result;
use crate::model::{
    ApplyExport, ApplyStats, AuditRow, ChangeRecord, ChangeType, ExportEntry, ModifyKind,
};

pub fn apply_records(seed: &str, records: &[ChangeRecord]) -> Result<(ApplyExport, Vec<AuditRow>)> {
    let mut directory: BTreeMap<String, BTreeMap<String, Vec<String>>> = BTreeMap::new();
    let mut audit_rows = Vec::new();
    let mut seq = 0u32;
    let mut applied = 0u32;
    let mut skipped = 0u32;

    for record in records {
        match record.changetype {
            ChangeType::Add => {
                let attrs = normalize_attrs(&record.attributes);
                directory.insert(record.dn.clone(), attrs);
                seq += 1;
                audit_rows.push(AuditRow {
                    seq,
                    dn: record.dn.clone(),
                    changetype: "add".into(),
                    detail: "add".into(),
                });
                applied += 1;
            }
            ChangeType::Delete => {
                directory.remove(&record.dn);
                seq += 1;
                audit_rows.push(AuditRow {
                    seq,
                    dn: record.dn.clone(),
                    changetype: "delete".into(),
                    detail: "delete".into(),
                });
                applied += 1;
            }
            ChangeType::Modify => {
                let Some(entry) = directory.get_mut(&record.dn) else {
                    skipped += 1;
                    continue;
                };
                for op in &record.modify_ops {
                    apply_modify_op(entry, op);
                }
                seq += 1;
                audit_rows.push(AuditRow {
                    seq,
                    dn: record.dn.clone(),
                    changetype: "modify".into(),
                    detail: format!("modify:{}", record.modify_ops.len()),
                });
                applied += 1;
            }
        }
    }

    let export = ApplyExport {
        seed: seed.to_string(),
        stats: ApplyStats {
            records_total: records.len() as u32,
            records_applied: applied,
            records_skipped: skipped,
        },
        entries: directory
            .iter()
            .map(|(dn, attrs)| ExportEntry {
                dn: dn.clone(),
                attributes: sort_attr_values(attrs),
            })
            .collect(),
    };
    Ok((export, audit_rows))
}

fn normalize_attrs(attrs: &BTreeMap<String, Vec<String>>) -> BTreeMap<String, Vec<String>> {
    let mut out: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for (key, values) in attrs {
        out.entry(key.to_ascii_lowercase())
            .or_default()
            .extend(values.iter().cloned());
    }
    sort_attr_values(&out)
}

fn sort_attr_values(attrs: &BTreeMap<String, Vec<String>>) -> BTreeMap<String, Vec<String>> {
    let mut out = BTreeMap::new();
    for (key, values) in attrs {
        let mut sorted = values.clone();
        sorted.sort();
        out.insert(key.clone(), sorted);
    }
    out
}

fn apply_modify_op(entry: &mut BTreeMap<String, Vec<String>>, op: &crate::model::ModifyOp) {
    let attr = op.attr.to_ascii_lowercase();
    match op.kind {
        ModifyKind::Add => {
            let slot = entry.entry(attr).or_default();
            for value in &op.values {
                if !slot.contains(value) {
                    slot.push(value.clone());
                }
            }
        }
        ModifyKind::Replace => {
            entry.insert(attr, op.values.clone());
        }
        ModifyKind::Delete => {
            if op.values.is_empty() {
                entry.remove(&attr);
            } else {
                if let Some(slot) = entry.get_mut(&attr) {
                    slot.retain(|existing| !op.values.contains(existing));
                    if slot.is_empty() {
                        entry.remove(&attr);
                    }
                }
            }
        }
    }
}
