use crate::avsc_parse::{type_label, AvroSchema};
use serde_json::Value;

#[derive(Debug, Clone, Default)]
pub struct LogicalViolation {
    pub field: String,
    pub reason: String,
}

pub fn check_logical_constraints(writer: &AvroSchema, reader: &AvroSchema) -> Vec<LogicalViolation> {
    let mut out = Vec::new();
    let w_fields = fields_map(&writer.raw);
    let r_fields = fields_map(&reader.raw);
    for (fname, rtyp) in &r_fields {
        let Some(wtyp) = w_fields.get(fname) else {
            continue;
        };
        if type_label(wtyp).starts_with("logical:decimal") || type_label(rtyp).starts_with("logical:decimal") {
            if !decimal_ok(wtyp, rtyp) {
                out.push(LogicalViolation {
                    field: fname.clone(),
                    reason: "decimal_precision_scale".into(),
                });
            }
        }
        if logical_name(wtyp) == Some("timestamp-millis") || logical_name(rtyp) == Some("timestamp-millis") {
            if logical_name(wtyp) != logical_name(rtyp) {
                out.push(LogicalViolation {
                    field: fname.clone(),
                    reason: "timestamp_millis_mismatch".into(),
                });
            }
        }
    }
    out
}

fn fields_map(raw: &Value) -> std::collections::BTreeMap<String, Value> {
    let mut out = std::collections::BTreeMap::new();
    if let Value::Object(map) = raw {
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

fn logical_name(v: &Value) -> Option<&str> {
    match v {
        Value::Object(map) => map.get("logicalType").and_then(|x| x.as_str()),
        _ => None,
    }
}

fn decimal_ok(writer: &Value, reader: &Value) -> bool {
    let wp = decimal_precision(writer).unwrap_or(0);
    let rp = decimal_precision(reader).unwrap_or(0);
    wp <= rp
}

fn decimal_precision(v: &Value) -> Option<u32> {
    match v {
        Value::Object(map) => map.get("precision").and_then(|p| p.as_u64()).map(|x| x as u32),
        _ => None,
    }
}
