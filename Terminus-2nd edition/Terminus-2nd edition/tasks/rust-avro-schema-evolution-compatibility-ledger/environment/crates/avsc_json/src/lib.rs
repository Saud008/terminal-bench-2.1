use serde_json::Value;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct AvroSchema {
    pub raw: Value,
    pub name: String,
    pub namespace: Option<String>,
    pub aliases: Vec<String>,
}

#[derive(Debug)]
pub struct ParseError;

pub fn load_schema(path: &Path) -> Result<AvroSchema, ParseError> {
    let raw: Value = serde_json::from_str(&fs::read_to_string(path).map_err(|_| ParseError)?)
        .map_err(|_| ParseError)?;
    let (name, namespace, aliases) = extract_meta(&raw);
    Ok(AvroSchema {
        raw,
        name,
        namespace,
        aliases,
    })
}

fn extract_meta(v: &Value) -> (String, Option<String>, Vec<String>) {
    match v {
        Value::Object(map) => {
            let name = map.get("name").and_then(|n| n.as_str()).unwrap_or("Anonymous").to_string();
            let namespace = map.get("namespace").and_then(|n| n.as_str()).map(str::to_string);
            let aliases = map
                .get("aliases")
                .and_then(|a| a.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|x| x.as_str().map(str::to_string))
                        .collect()
                })
                .unwrap_or_default();
            (name, namespace, aliases)
        }
        _ => ("Anonymous".into(), None, vec![]),
    }
}

pub fn full_name(schema: &AvroSchema) -> String {
    match &schema.namespace {
        Some(ns) => format!("{ns}.{}", schema.name),
        None => schema.name.clone(),
    }
}

pub fn field_names(schema: &AvroSchema) -> Vec<String> {
    match &schema.raw {
        Value::Object(map) if map.get("type").and_then(|t| t.as_str()) == Some("record") => map
            .get("fields")
            .and_then(|f| f.as_array())
            .map(|fields| {
                fields
                    .iter()
                    .filter_map(|f| f.get("name").and_then(|n| n.as_str()).map(str::to_string))
                    .collect()
            })
            .unwrap_or_default(),
        _ => vec![],
    }
}

pub fn union_branches(v: &Value) -> Option<Vec<String>> {
    match v {
        Value::Array(arr) => Some(
            arr.iter()
                .map(branch_label)
                .collect(),
        ),
        Value::Object(map) if map.get("type").and_then(|t| t.as_str()) == Some("array") => {
            map.get("items").and_then(union_branches)
        }
        _ => None,
    }
}

fn branch_label(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        Value::Object(map) => map
            .get("type")
            .and_then(|t| t.as_str())
            .unwrap_or("complex")
            .to_string(),
        _ => "unknown".into(),
    }
}

pub fn type_label(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        Value::Object(map) => {
            if let Some(lt) = map.get("logicalType").and_then(|x| x.as_str()) {
                format!("logical:{lt}")
            } else {
                map.get("type")
                    .and_then(|t| t.as_str())
                    .unwrap_or("record")
                    .to_string()
            }
        }
        Value::Array(_) => "union".into(),
        _ => "unknown".into(),
    }
}
