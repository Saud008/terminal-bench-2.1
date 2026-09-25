use crate::wx_bundle_read::{read_manifest_dir, ManifestDoc};
use crate::wx_width_table::wx_payload_units;
use crate::wx_roll_journal::{wx_read_journal, StagedRow};
use crate::wx_parent_bind::wx_anchor_fold;
use crate::wx_digest_seal::wx_seal_bytes;
use crate::wx_frame_parse::parse_shard_file;
use serde::Serialize;
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Clone)]
pub struct Violation {
    pub tensor: String,
    pub code: String,
    pub message: String,
}

#[derive(Debug, Serialize)]
pub struct LineageReport {
    pub manifest_id: String,
    pub violations: Vec<Violation>,
    pub totals: Totals,
}

#[derive(Debug, Serialize)]
pub struct Totals {
    pub violation_count: u32,
    pub tensor_count: u32,
}

pub fn wx_finalize_report(
    journal_path: &Path,
    manifest_dir: &Path,
    shard_root: &Path,
    out_path: &Path,
) -> Result<(), String> {
    let staged = wx_read_journal(journal_path)?;
    let docs = read_manifest_dir(manifest_dir)?;
    let mut by_manifest: BTreeMap<String, Vec<StagedRow>> = BTreeMap::new();
    for row in staged {
        by_manifest.entry(row.manifest_id.clone()).or_default().push(row);
    }
    let mut reports = Vec::new();
    for doc in docs {
        let rows = by_manifest.get(&doc.manifest_id).cloned().unwrap_or_default();
        let mut violations = wx_diff_rows(&doc, &rows, shard_root);
        violations.sort_by(|a, b| a.code.cmp(&b.code));
        reports.push(LineageReport {
            manifest_id: doc.manifest_id.clone(),
            violations: violations.clone(),
            totals: Totals {
                violation_count: violations.len() as u32,
                tensor_count: rows.len() as u32,
            },
        });
    }
    let json = serde_json::to_string_pretty(&reports).map_err(|e| e.to_string())?;
    fs::write(out_path, format!("{json}
")).map_err(|e| e.to_string())
}

fn wx_diff_rows(doc: &ManifestDoc, staged: &[StagedRow], shard_root: &Path) -> Vec<Violation> {
    let mut violations = Vec::new();
    if !wx_anchor_fold(doc) {
        violations.push(Violation {
            tensor: "*".into(),
            code: "LINEAGE_HASH".into(),
            message: "base_model_hash does not match expected".into(),
        });
    }
    for row in staged {
        let shard_path = shard_root.join(&row.shard_file);
        let parsed = parse_shard_file(&shard_path).unwrap_or_else(|_| {
            violations.push(Violation {
                tensor: row.tensor.clone(),
                code: "PARSE_FAIL".into(),
                message: "cannot parse shard".into(),
            });
            return parse_shard_file(&shard_path).unwrap();
        });
        let header = match parsed.tensors.get(&row.tensor) {
            Some(h) => h,
            None => {
                violations.push(Violation {
                    tensor: row.tensor.clone(),
                    code: "MISSING_TENSOR".into(),
                    message: "tensor missing from shard header".into(),
                });
                continue;
            }
        };
        let data_len = parsed.payload.len() as u64;
        if header.data_offsets[1] > data_len {
            violations.push(Violation {
                tensor: row.tensor.clone(),
                code: "OFFSET_OVERFLOW".into(),
                message: "tensor end exceeds data section".into(),
            });
        }
        let expected = wx_payload_units(&row.dtype, &row.shape).unwrap_or(0);
        let span = header.data_offsets[1] - header.data_offsets[0];
        if span != expected {
            violations.push(Violation {
                tensor: row.tensor.clone(),
                code: "DTYPE_SHAPE".into(),
                message: "payload span does not match dtype and shape".into(),
            });
        }
        let cs = wx_seal_bytes(&parsed, header.data_offsets[0], header.data_offsets[1]);
        if cs != row.payload_fingerprint {
            violations.push(Violation {
                tensor: row.tensor.clone(),
                code: "DIGEST".into(),
                message: "payload fingerprint mismatch".into(),
            });
        }
    }
    violations
}
