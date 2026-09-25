use crate::relay_rank;
use crate::order_gate;
use crate::types::{ManifestLatch, MsgRow};
use std::fs;
use std::io::Write;
use std::path::Path;

pub fn norm_stream(meta: &ManifestLatch, stream_path: &Path, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(stream_path).map_err(|e| e.to_string())?;
    let mut rows: Vec<MsgRow> = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let v: serde_json::Value = serde_json::from_str(line).map_err(|e| e.to_string())?;
        rows.push(MsgRow {
            topic: v["topic"].as_str().unwrap_or("").to_string(),
            seq: v["seq"].as_u64().unwrap_or(0),
            header_stamp_ns: v["receive_stamp_ns"].as_u64().unwrap_or(0),
            receive_stamp_ns: v["receive_stamp_ns"].as_u64().unwrap_or(0),
            relay_pass: v["relay_pass"].as_u64().unwrap_or(0) as u32,
        });
    }
    rows = relay_rank::dedupe_rows(rows);
    order_gate::assert_monotonic(&rows)?;
    let out_path = format!("{out_dir}/{}.jsonl", meta.bag_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    writeln!(
        f,
        "{{\"bag_id\":\"{}\",\"manifest_revision\":{}}}",
        meta.bag_id,
        meta.manifest_revision
    )
        .map_err(|e| e.to_string())?;
    for row in rows {
        let js = serde_json::to_string(&row).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
