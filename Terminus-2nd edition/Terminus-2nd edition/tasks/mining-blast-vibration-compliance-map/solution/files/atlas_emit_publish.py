"""Offline patch script for atlas_emit/publish.rs digest and sort fixes."""

from pathlib import Path

path = Path("/app/atlas_emit/publish.rs")
text = path.read_text(encoding="utf-8")
text = text.replace("corrected.min(attenuated)", "corrected.max(attenuated)")
text = text.replace(
    "rows.sort_by(|a, b| a.blast_id.cmp(&b.blast_id));",
    "rows.sort_by(|a, b| {\n        (a.property_id.as_str(), a.blast_id.as_str(), a.sensor_id.as_str())\n            .cmp(&(b.property_id.as_str(), b.blast_id.as_str(), b.sensor_id.as_str()))\n    });",
)
text = text.replace(
    "atlas.atlas_digest = atlas_digest(&atlas.summary);",
    "atlas.atlas_digest = atlas_digest(&atlas.summary, &atlas.exceedance_rows);",
)
old_fn = "fn atlas_digest(summary: &ExceedanceSummary) -> String {"
if old_fn in text and "fn atlas_digest(summary: &ExceedanceSummary, rows: &[ExceedanceRow])" not in text:
    start = text.index(old_fn)
    end = text.index("}\n\npub fn write_atlas", start) + 1
    new_fn = '''fn atlas_digest(summary: &ExceedanceSummary, rows: &[ExceedanceRow]) -> String {
    use std::collections::BTreeMap;
    let mut values: Vec<f64> = rows
        .iter()
        .map(|r| (r.exceedance_mm_s * 10000.0).round() / 10000.0)
        .collect();
    values.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let mut obj: BTreeMap<&str, serde_json::Value> = BTreeMap::new();
    obj.insert("exceedance_count", serde_json::json!(summary.exceedance_count));
    obj.insert("exceedance_values", serde_json::json!(values));
    obj.insert("max_exceedance_mm_s", serde_json::json!(summary.max_exceedance_mm_s));
    obj.insert("reading_pairs", serde_json::json!(summary.reading_pairs));
    let body = serde_json::to_string(&obj).unwrap_or_default();
    let mut hasher = Sha256::new();
    hasher.update(body.as_bytes());
    hex::encode(hasher.finalize())
}'''
    text = text[:start] + new_fn + text[end:]
path.write_text(text, encoding="utf-8")
