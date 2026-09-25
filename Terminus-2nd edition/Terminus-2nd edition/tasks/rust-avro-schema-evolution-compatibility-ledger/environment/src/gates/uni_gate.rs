use crate::avsc_parse::AvroSchema;
use crate::uni_branch::union_compatible;
use serde_json::Value;
use std::collections::BTreeMap;

pub fn union_order_ok(writer: &AvroSchema, reader: &AvroSchema) -> bool {
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

fn fields_with_types(raw: &Value) -> BTreeMap<String, Value> {
    let mut out = BTreeMap::new();
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
