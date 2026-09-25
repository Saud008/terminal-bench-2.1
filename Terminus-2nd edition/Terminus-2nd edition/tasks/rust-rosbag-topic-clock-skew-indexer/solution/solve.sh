#!/usr/bin/env bash
set -euo pipefail
cd /app
cat > /app/kennel_io/vor.rs <<'EOF'
use crate::types::{ManifestLatch, TopicSpec};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

pub fn latch_manifest(bag_id: &str, path: &Path, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let v: serde_json::Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let reference_topic = v["reference_topic"].as_str().unwrap_or("/clock/anchor").to_string();
    let sync_window_ns = v["sync_window_ns"].as_u64().unwrap_or(5_000_000);
    let mut topic_remap = BTreeMap::new();
    if let Some(obj) = v["topic_remap"].as_object() {
        for (k, val) in obj {
            topic_remap.insert(k.clone(), val.as_str().unwrap_or(k).to_string());
        }
    }
    let mut topics = Vec::new();
    if let Some(arr) = v["topics"].as_array() {
        for t in arr {
            topics.push(TopicSpec {
                name: t["name"].as_str().unwrap_or("").to_string(),
                r#type: t["type"].as_str().unwrap_or("").to_string(),
                expected_rate_hz: t["expected_rate_hz"].as_u64().unwrap_or(0) as u32,
            });
        }
    }
    let prev = fs::read_to_string(format!("{out_dir}/{bag_id}.json"))
        .ok()
        .and_then(|raw| serde_json::from_str::<ManifestLatch>(&raw).ok())
        .map(|m| m.manifest_revision)
        .unwrap_or(0);
    let latch_doc = ManifestLatch {
        bag_id: bag_id.to_string(),
        reference_topic,
        sync_window_ns,
        topic_remap,
        topics,
        manifest_revision: prev + 1,
    };
    let out = format!("{out_dir}/{bag_id}.json");
    fs::write(&out, serde_json::to_string_pretty(&latch_doc).unwrap()).map_err(|e| e.to_string())
}
EOF

cat > /app/hopf_weave/weave.rs <<'EOF'
use crate::relay_rank;
use crate::order_gate;
use crate::types::{ManifestLatch, MsgRow};
use std::fs;
use std::io::Write;
use std::path::Path;

fn remap(raw: &str, meta: &ManifestLatch) -> String {
    meta.topic_remap.get(raw).cloned().unwrap_or_else(|| raw.to_string())
}

pub fn norm_stream(meta: &ManifestLatch, stream_path: &Path, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(stream_path).map_err(|e| e.to_string())?;
    let mut rows: Vec<MsgRow> = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let v: serde_json::Value = serde_json::from_str(line).map_err(|e| e.to_string())?;
        let topic_raw = v["topic"].as_str().unwrap_or("").to_string();
        rows.push(MsgRow {
            topic: remap(&topic_raw, meta),
            seq: v["seq"].as_u64().unwrap_or(0),
            header_stamp_ns: v["header_stamp_ns"].as_u64().unwrap_or(0),
            receive_stamp_ns: v["receive_stamp_ns"].as_u64().unwrap_or(0),
            relay_pass: v["relay_pass"].as_u64().unwrap_or(0) as u32,
        });
    }
    rows = relay_rank::dedupe_rows(rows);
    order_gate::assert_monotonic(&rows)?;
    let out_path = format!("{out_dir}/{}.jsonl", meta.bag_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    writeln!(f, "{{\"bag_id\":\"{}\",\"manifest_revision\":{}}}", meta.bag_id, meta.manifest_revision)
        .map_err(|e| e.to_string())?;
    for row in rows {
        let js = serde_json::to_string(&row).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}
EOF

cat > /app/order_gate/order.rs <<'EOF'
use crate::types::MsgRow;
use std::collections::BTreeMap;

pub fn assert_monotonic(rows: &[MsgRow]) -> Result<(), String> {
    let mut last: BTreeMap<String, u64> = BTreeMap::new();
    for row in rows {
        if let Some(prev) = last.get(&row.topic) {
            if row.header_stamp_ns <= *prev {
                return Err(format!("non-monotonic stamp on {}", row.topic));
            }
        }
        last.insert(row.topic.clone(), row.header_stamp_ns);
    }
    Ok(())
}
EOF

cat > /app/relay_rank/rank.rs <<'EOF'
use crate::types::MsgRow;
use std::collections::BTreeMap;

pub fn dedupe_rows(rows: Vec<MsgRow>) -> Vec<MsgRow> {
    let mut best: BTreeMap<(String, u64), MsgRow> = BTreeMap::new();
    for row in rows {
        let key = (row.topic.clone(), row.seq);
        match best.get(&key) {
            Some(existing) => {
                if row.relay_pass > existing.relay_pass {
                    best.insert(key, row);
                }
            }
            None => {
                best.insert(key, row);
            }
        }
    }
    let mut out: Vec<_> = best.into_values().collect();
    out.sort_by_key(|r| (r.header_stamp_ns, r.topic.clone()));
    out
}
EOF

cat > /app/ruelle_pq/match.rs <<'EOF'
use crate::types::{ManifestLatch, MsgRow, SyncPair};
use std::collections::BTreeMap;
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
    let half = window / 2;
    let ref_rows: Vec<&MsgRow> = rows
        .iter()
        .filter(|r| r.topic == ref_topic)
        .collect();
    let mut pairs: Vec<SyncPair> = Vec::new();
    for rr in ref_rows {
        let anchor = rr.header_stamp_ns;
        let mut best: BTreeMap<String, SyncPair> = BTreeMap::new();
        for other in &rows {
            if other.topic == ref_topic {
                continue;
            }
            let delta = other.header_stamp_ns as i64 - anchor as i64;
            if (delta.abs() as u64) <= half {
                let replace = match best.get(&other.topic) {
                    None => true,
                    Some(cur) => delta.abs() < cur.delta_ns.abs(),
                };
                if replace {
                    best.insert(
                        other.topic.clone(),
                        SyncPair {
                            ref_stamp_ns: anchor,
                            topic: other.topic.clone(),
                            header_stamp_ns: other.header_stamp_ns,
                            delta_ns: delta,
                        },
                    );
                }
            }
        }
        pairs.extend(best.into_values());
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
EOF

python3 <<'PY'
from pathlib import Path
p = Path("/app/peskin_pq/publish.rs")
text = p.read_text()
text = text.replace("slope: -slope", "slope")
text = text.replace("intercept_ns: -intercept", "intercept_ns: intercept")
p.write_text(text)
PY

/usr/local/cargo/bin/cargo build --release --locked
cp /app/target/release/skew-cal /app/bin/skew-cal
