use crate::types::ChartDoc;

pub fn parse_chart(text: &str) -> Result<ChartDoc, String> {
    let mut doc: ChartDoc = serde_json::from_str(text).map_err(|e| e.to_string())?;
    doc.chart_id = normalize_id(&doc.chart_id);
    Ok(doc)
}

pub fn normalize_id(chart_id: &str) -> String {
    chart_id.to_ascii_lowercase()
}
