use reader_default::{defaults_compatible, promotion_ok};
use canonical_fp::parsing_fingerprint;
use logical_check::check_logical_constraints;
use fqdn_alias::alias_equivalent;
use avsc_json::{load_schema, AvroSchema};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::path::Path;
use branch_set::union_compatible;

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
    let wf = parsing_fingerprint(&writer);
    let rf = parsing_fingerprint(&reader);
    let mut violations = Vec::new();

    let namespace_alias_ok = alias_equivalent(&writer, &reader) || writer.name == reader.name;
    if !namespace_alias_ok {
        violations.push("namespace_alias".into());
    }

    let defaults_ok = defaults_compatible(&writer, &reader) && field_promotions_ok(&writer, &reader);
    if !defaults_ok {
        violations.push("default_rules".into());
    }

    let union_order_ok = record_union_fields_compatible(&writer, &reader);
    if !union_order_ok {
        violations.push("union_order".into());
    }

    let logical_v = check_logical_constraints(&writer, &reader);
    let logical_types_ok = logical_v.is_empty();
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

fn field_promotions_ok(writer: &AvroSchema, reader: &AvroSchema) -> bool {
    let w = fields_with_types(&writer.raw);
    let r = fields_with_types(&reader.raw);
    for (name, rtyp) in &r {
        if let Some(wtyp) = w.get(name) {
            if !promotion_ok(wtyp, rtyp) {
                return false;
            }
        }
    }
    true
}

fn record_union_fields_compatible(writer: &AvroSchema, reader: &AvroSchema) -> bool {
    let w = fields_with_types(&writer.raw);
    let r = fields_with_types(&reader.raw);
    for (name, wtyp) in &w {
        if let Some(rtyp) = r.get(name) {
            if !union_compatible(wtyp, rtyp) {
                return false;
            }
        }
    }
    true
}

fn fields_with_types(raw: &serde_json::Value) -> BTreeMap<String, serde_json::Value> {
    let mut out = BTreeMap::new();
    if let serde_json::Value::Object(map) = raw {
        if let Some(fields) = map.get("fields").and_then(|f| f.as_array()) {
            for f in fields {
                if let (Some(n), Some(t)) = (f.get("name"), f.get("type")) {
                    out.insert(n.as_str().unwrap_or("").into(), t.clone());
                }
            }
        }
    }
    out
}
