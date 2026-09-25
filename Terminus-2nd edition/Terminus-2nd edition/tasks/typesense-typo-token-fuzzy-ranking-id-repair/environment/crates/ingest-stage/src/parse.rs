use ts_types::document::Document;

pub fn parse_line(raw: &str, order: u64) -> Result<Document, String> {
    let obj: serde_json::Value = serde_json::from_str(raw).map_err(|e| e.to_string())?;
    Ok(Document {
        docid: obj["docid"].as_str().ok_or("docid")?.to_string(),
        title: obj["title"].as_str().unwrap_or("").to_string(),
        body: obj["body"].as_str().unwrap_or("").to_string(),
        brand: obj["brand"].as_str().unwrap_or("default").to_string(),
        insertion_order: order,
    })
}
