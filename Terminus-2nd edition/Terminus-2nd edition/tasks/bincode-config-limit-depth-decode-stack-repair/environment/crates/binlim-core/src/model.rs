use serde::Serialize;
use serde_json::json;

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum DecodedValue {
    Null,
    Bool { value: bool },
    U32 { value: u32 },
    String { value: String },
    Vec { items: Vec<DecodedValue> },
    Enum { tag: u32, payload: Box<DecodedValue> },
    DoubleOption { value: DoubleOptionInner },
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(untagged)]
pub enum DoubleOptionInner {
    None,
    SomeNone,
    SomeSome(Box<DecodedValue>),
}

impl DoubleOptionInner {
    pub fn none() -> Self {
        DoubleOptionInner::None
    }

    pub fn some_none() -> Self {
        DoubleOptionInner::SomeNone
    }

    pub fn some_some(v: DecodedValue) -> Self {
        DoubleOptionInner::SomeSome(Box::new(v))
    }
}

impl DecodedValue {
    pub fn to_json(&self) -> serde_json::Value {
        match self {
            DecodedValue::Null => serde_json::Value::Null,
            DecodedValue::Bool { value } => json!({"kind": "bool", "value": value}),
            DecodedValue::U32 { value } => json!({"kind": "u32", "value": value}),
            DecodedValue::String { value } => json!({"kind": "string", "value": value}),
            DecodedValue::Vec { items } => {
                json!({"kind": "vec", "items": items.iter().map(DecodedValue::to_json).collect::<Vec<_>>()})
            }
            DecodedValue::Enum { tag, payload } => {
                json!({"kind": "enum", "tag": tag, "payload": payload.to_json()})
            }
            DecodedValue::DoubleOption { value } => {
                let inner = match value {
                    DoubleOptionInner::None => serde_json::Value::Null,
                    DoubleOptionInner::SomeNone => json!({"inner": null}),
                    DoubleOptionInner::SomeSome(v) => json!({"inner": v.to_json()}),
                };
                json!({"kind": "double_option", "value": inner})
            }
        }
    }
}
