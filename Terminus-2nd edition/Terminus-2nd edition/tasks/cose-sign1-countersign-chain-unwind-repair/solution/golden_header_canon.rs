use ciborium::Value;
use std::collections::BTreeMap;

fn encode_label_key(label: i64) -> Result<Vec<u8>, String> {
    let v = Value::Integer(label.into());
    let mut buf = vec![];
    ciborium::ser::into_writer(&v, &mut buf).map_err(|e| e.to_string())?;
    Ok(buf)
}

pub fn protected_label_order(protected: &BTreeMap<i64, Value>) -> Vec<i64> {
    let mut labels: Vec<i64> = protected.keys().copied().collect();
    labels.sort_by(|a, b| {
        let ea = encode_label_key(*a).unwrap_or_default();
        let eb = encode_label_key(*b).unwrap_or_default();
        ea.cmp(&eb)
    });
    labels
}

pub fn encode_protected_map(protected: &BTreeMap<i64, Value>) -> Result<Vec<u8>, String> {
    let order = protected_label_order(protected);
    let mut pairs = vec![];
    for label in order {
        let v = protected.get(&label).cloned().ok_or("missing label")?;
        pairs.push((Value::Integer(label.into()), v));
    }
    let val = Value::Map(pairs);
    let mut buf = vec![];
    ciborium::ser::into_writer(&val, &mut buf).map_err(|e| e.to_string())?;
    Ok(buf)
}
