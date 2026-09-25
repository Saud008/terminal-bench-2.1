use crate::types::ChartDoc;

pub fn parse_chart(text: &str) -> Result<ChartDoc, String> {
    let doc: ChartDoc = serde_json::from_str(text).map_err(|e| e.to_string())?;
    Ok(doc)
}

pub fn normalize_id(chart_id: &str) -> String {
    chart_id.to_string()
}
