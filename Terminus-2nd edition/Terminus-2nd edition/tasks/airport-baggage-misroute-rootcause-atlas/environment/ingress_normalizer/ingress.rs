// bag-tag ingest lane for seq-scans — normalize scan streams into scan ledger
use crate::types::{HubLatch, ScanRow};
use std::collections::BTreeMap;
use std::fs;
use std::io::Write;
use std::path::Path;

pub fn dedupe_scans(rows: Vec<ScanRow>) -> Vec<ScanRow> {
    let mut best: BTreeMap<(String, u64), ScanRow> = BTreeMap::new();
    for row in rows {
        let key = (row.bag_tag.clone(), row.scan_seq);
        match best.get(&key) {
            Some(existing) if row.relay_pass <= existing.relay_pass => {}
            _ => {
                best.insert(key, row);
            }
        }
    }
    let mut out: Vec<_> = best.into_values().collect();
    out.sort_by_key(|r| r.scan_minute);
    out
}

pub fn seq_scans(_hub: &HubLatch, stream_path: &Path, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(stream_path).map_err(|e| e.to_string())?;
    let mut rows = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let v: serde_json::Value = serde_json::from_str(line).map_err(|e| e.to_string())?;
        rows.push(ScanRow {
            bag_tag: v["bag_tag"].as_str().unwrap_or("").to_string(),
            scan_seq: v["scan_seq"].as_u64().unwrap_or(0),
            belt_id: v["belt_id"].as_str().unwrap_or("").to_string(),
            station_code: v["station_code"].as_str().unwrap_or("").to_string(),
            scan_minute: v["scan_minute"].as_u64().unwrap_or(0),
            relay_pass: v["relay_pass"].as_u64().unwrap_or(0) as u32,
        });
    }
    rows = dedupe_scans(rows);
    let out_path = format!("{out_dir}/{}.jsonl", _hub.hub_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    writeln!(
        f,
        r#"{{"hub_id":"{}","topology_revision":{}}}"#,
        _hub.hub_id, _hub.topology_revision
    )
    .map_err(|e| e.to_string())?;
    for row in rows {
        let js = serde_json::to_string(&row).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}

pub fn latch_hub(hub_id: &str, topo_path: &Path, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(topo_path).map_err(|e| e.to_string())?;
    let v: serde_json::Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    let prev = fs::read_to_string(format!("{out_dir}/{hub_id}.json"))
        .ok()
        .and_then(|s| serde_json::from_str::<crate::types::HubLatch>(&s).ok())
        .map(|h| h.topology_revision)
        .unwrap_or(0);
    let mut belts = Vec::new();
    if let Some(arr) = v["belts"].as_array() {
        for b in arr {
            belts.push(crate::types::BeltSpec {
                belt_id: b["belt_id"].as_str().unwrap_or("").to_string(),
                priority: b["priority"].as_u64().unwrap_or(0) as u32,
                station_code: b["station_code"].as_str().unwrap_or("").to_string(),
                target_flight_id: b["target_flight_id"].as_str().unwrap_or("").to_string(),
            });
        }
    }
    let mut flights = Vec::new();
    if let Some(arr) = v["flights"].as_array() {
        for fl in arr {
            flights.push(crate::types::FlightSpec {
                flight_id: fl["flight_id"].as_str().unwrap_or("").to_string(),
                dep_minute: fl["dep_minute"].as_u64().unwrap_or(0),
                arr_minute: fl["arr_minute"].as_u64().unwrap_or(0),
            });
        }
    }
    let mut connections = Vec::new();
    if let Some(arr) = v["connections"].as_array() {
        for c in arr {
            connections.push(crate::types::ConnectionSpec {
                inbound_flight: c["inbound_flight"].as_str().unwrap_or("").to_string(),
                outbound_flight: c["outbound_flight"].as_str().unwrap_or("").to_string(),
                min_connect_minutes: c["min_connect_minutes"].as_u64().unwrap_or(0),
            });
        }
    }
    let mut outages = Vec::new();
    if let Some(arr) = v["outages"].as_array() {
        for o in arr {
            outages.push(crate::types::OutageSpec {
                station_code: o["station_code"].as_str().unwrap_or("").to_string(),
                start_minute: o["start_minute"].as_u64().unwrap_or(0),
                end_minute: o["end_minute"].as_u64().unwrap_or(0),
            });
        }
    }
    let latch = crate::types::HubLatch {
        hub_id: hub_id.to_string(),
        topology_revision: prev + 1,
        belts,
        flights,
        connections,
        outages,
    };
    fs::write(
        format!("{out_dir}/{hub_id}.json"),
        serde_json::to_string_pretty(&latch).unwrap(),
    )
    .map_err(|e| e.to_string())
}
