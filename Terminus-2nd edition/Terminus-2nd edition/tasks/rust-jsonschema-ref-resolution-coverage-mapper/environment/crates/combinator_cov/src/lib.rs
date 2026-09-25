use js_value::object_get;
use serde_json::Value;
use std::collections::BTreeSet;

#[derive(Debug, Clone, Default)]
pub struct ComboCoverage {
    pub all_of: BTreeSet<String>,
    pub any_of: BTreeSet<String>,
}

pub fn walk_combinators(node: &Value, pointer: &str, instance: &Value, cov: &mut ComboCoverage) {
    if let Some(all) = object_get(node, "allOf").and_then(|v| v.as_array()) {
        for (i, branch) in all.iter().enumerate() {
            let bp = if pointer.is_empty() {
                format!("/allOf/{i}")
            } else {
                format!("{pointer}/allOf/{i}")
            };
            if instance_matches(branch, instance) {
                cov.all_of.insert(bp.clone());
            }
            walk_combinators(branch, &bp, instance, cov);
        }
    }
    if let Some(any) = object_get(node, "anyOf").and_then(|v| v.as_array()) {
        let mut any_hit = false;
        for (i, branch) in any.iter().enumerate() {
            let bp = if pointer.is_empty() {
                format!("/anyOf/{i}")
            } else {
                format!("{pointer}/anyOf/{i}")
            };
            if instance_matches(branch, instance) {
                any_hit = true;
            }
            walk_combinators(branch, &bp, instance, cov);
        }
        if any_hit {
            for i in 0..any.len() {
                let bp = if pointer.is_empty() {
                    format!("/anyOf/{i}")
                } else {
                    format!("{pointer}/anyOf/{i}")
                };
                cov.any_of.insert(bp);
            }
        }
    }
    if let Some(props) = object_get(node, "properties").and_then(|v| v.as_object()) {
        if let Some(inst_obj) = instance.as_object() {
            for (k, subschema) in props {
                if let Some(child_inst) = inst_obj.get(k) {
                    let child_ptr = if pointer.is_empty() {
                        format!("/properties/{k}")
                    } else {
                        format!("{pointer}/properties/{k}")
                    };
                    walk_combinators(subschema, &child_ptr, child_inst, cov);
                }
            }
        }
    }
}

fn instance_matches(schema: &Value, instance: &Value) -> bool {
    if let Some(t) = object_get(schema, "type").and_then(|v| v.as_str()) {
        return type_matches(t, instance);
    }
    if object_get(schema, "const").is_some() {
        return object_get(schema, "const") == Some(instance);
    }
    true
}

fn type_matches(t: &str, instance: &Value) -> bool {
    match t {
        "object" => instance.is_object(),
        "array" => instance.is_array(),
        "string" => instance.is_string(),
        "integer" => instance.as_i64().is_some(),
        "number" => instance.as_f64().is_some() || instance.as_i64().is_some(),
        "boolean" => instance.is_boolean(),
        "null" => instance.is_null(),
        _ => false,
    }
}
