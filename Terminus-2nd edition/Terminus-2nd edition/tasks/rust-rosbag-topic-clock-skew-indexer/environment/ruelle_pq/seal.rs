use crate::types::{ManifestLatch, MsgRow, SyncPair};
use std::fs;
use std::io::Write;

pub fn match_sync(meta: &ManifestLatch, timeline_ledger_path: &str, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(timeline_ledger_path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let _hdr = lines.next();
    let mut rows: Vec<MsgRow> = Vec::new();
    for line in lines {
        rows.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    let ref_topic = crate::reference_topic_override()
        .unwrap_or_else(|| meta.reference_topic.clone());
    let window = crate::sync_window_override().unwrap_or(meta.sync_window_ns);
    let mut ref_rows: Vec<&MsgRow> = rows.iter().filter(|r| r.topic == ref_topic).collect();
    ref_rows.sort_by_key(|r| r.header_stamp_ns);
    let half = window / 2;
    let mut pairs: Vec<SyncPair> = Vec::new();
    for rr in &ref_rows {
        let anchor = rr.header_stamp_ns.min(
            rows.iter()
                .map(|r| r.header_stamp_ns)
                .min()
                .unwrap_or(rr.header_stamp_ns),
        );
        for other in &rows {
            if other.topic == ref_topic {
                continue;
            }
            let delta = other.header_stamp_ns as i64 - anchor as i64;
            if delta.abs() as u64 <= half {
                pairs.push(SyncPair {
                    ref_stamp_ns: anchor,
                    topic: other.topic.clone(),
                    header_stamp_ns: other.header_stamp_ns,
                    delta_ns: delta,
                });
            }
        }
    }
    pairs.sort_by(|a, b| {
        (a.ref_stamp_ns, a.topic.clone(), a.header_stamp_ns)
            .cmp(&(b.ref_stamp_ns, b.topic.clone(), b.header_stamp_ns))
    });
    let out_path = format!("{out_dir}/{}.jsonl", meta.bag_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    writeln!(
        f,
        "{{\"bag_id\":\"{}\",\"reference_topic\":\"{}\",\"sync_window_ns\":{}}}",
        meta.bag_id, ref_topic, window
    )
    .map_err(|e| e.to_string())?;
    for p in pairs {
        let js = serde_json::to_string(&p).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
