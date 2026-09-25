use std::collections::BTreeMap;
use xapi_types::document::Document;

pub fn parse_line(raw: &str, order: u64) -> Result<Document, String> {
    let v: serde_json::Value = serde_json::from_str(raw).map_err(|e| e.to_string())?;
    let docid = v
        .get("docid")
        .and_then(|x| x.as_str())
        .ok_or("missing docid")?
        .to_string();
    let body = v
        .get("body")
        .and_then(|x| x.as_str())
        .ok_or("missing body")?
        .to_string();
    let mut synonyms = BTreeMap::new();
    if let Some(obj) = v.get("synonyms").and_then(|x| x.as_object()) {
        for (k, val) in obj {
            let arr = val
                .as_array()
                .ok_or("synonyms values must be arrays")?
                .iter()
                .filter_map(|x| x.as_str().map(|s| s.to_ascii_lowercase()))
                .collect();
            synonyms.insert(k.to_ascii_lowercase(), arr);
        }
    }
    Ok(Document {
        docid,
        body,
        synonyms,
        insertion_order: order,
    })
}
