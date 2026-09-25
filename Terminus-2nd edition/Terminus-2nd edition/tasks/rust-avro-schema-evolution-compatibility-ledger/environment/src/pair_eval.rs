use crate::avsc_parse::{load_schema, AvroSchema};
use crate::gates::{def_gate, fp_gate, log_gate, ns_gate, uni_gate};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CheckFlags {
    pub namespace_alias_ok: bool,
    pub defaults_ok: bool,
    pub union_order_ok: bool,
    pub logical_types_ok: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PairResult {
    pub subject: String,
    pub writer_path: String,
    pub reader_path: String,
    pub writer_fingerprint: String,
    pub reader_fingerprint: String,
    pub compatible: bool,
    pub violations: Vec<String>,
    pub checks: CheckFlags,
}

pub fn evaluate_pair(
    subject: &str,
    writer_path: &Path,
    reader_path: &Path,
) -> Result<PairResult, String> {
    let writer = load_schema(writer_path).map_err(|_| "writer parse failed".to_string())?;
    let reader = load_schema(reader_path).map_err(|_| "reader parse failed".to_string())?;
    let wf = fp_gate::writer_fingerprint(&writer);
    let rf = fp_gate::reader_fingerprint(&reader);
    let mut violations = Vec::new();

    let namespace_alias_ok = ns_gate::namespace_alias_ok(&writer, &reader);
    if !namespace_alias_ok {
        violations.push("namespace_alias".into());
    }

    let defaults_ok = def_gate::defaults_ok(&writer, &reader);
    if !defaults_ok {
        violations.push("default_rules".into());
    }

    let union_order_ok = uni_gate::union_order_ok(&writer, &reader);
    if !union_order_ok {
        violations.push("union_order".into());
    }

    let logical_types_ok = log_gate::logical_types_ok(&writer, &reader);
    if !logical_types_ok {
        violations.push("logical_types".into());
    }

    let compatible = violations.is_empty();
    Ok(PairResult {
        subject: subject.to_string(),
        writer_path: writer_path.display().to_string(),
        reader_path: reader_path.display().to_string(),
        writer_fingerprint: wf,
        reader_fingerprint: rf,
        compatible,
        violations,
        checks: CheckFlags {
            namespace_alias_ok,
            defaults_ok,
            union_order_ok,
            logical_types_ok,
        },
    })
}
