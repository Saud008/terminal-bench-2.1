use crate::avsc_parse::{type_label, AvroSchema};
use serde_json::Value;

pub fn defaults_compatible(writer: &AvroSchema, reader: &AvroSchema) -> bool {
    let w_fields = record_fields(&writer.raw);
    let r_fields = record_fields(&reader.raw);
    for (rname, rdef) in &r_fields {
        if w_fields.contains_key(rname) {
            continue;
        }
        if rdef.get("default").is_none() {
            return false;
        }
    }
    true
}

pub fn promotion_ok(writer_type: &Value, reader_type: &Value) -> bool {
    let wt = type_label(writer_type);
    let rt = type_label(reader_type);
    wt == rt
}

fn record_fields(raw: &Value) -> std::collections::BTreeMap<String, Value> {
    let mut out = std::collections::BTreeMap::new();
    if let Value::Object(map) = raw {
        if map.get("type").and_then(|t| t.as_str()) != Some("record") {
            return out;
        }
        if let Some(fields) = map.get("fields").and_then(|f| f.as_array()) {
            for f in fields {
                if let (Some(name), Some(typ)) = (f.get("name"), f.get("type")) {
                    out.insert(name.as_str().unwrap_or("").to_string(), typ.clone());
                }
            }
        }
    }
    out
}
