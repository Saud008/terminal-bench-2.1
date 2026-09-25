// misroute atlas export lane — emit rootcause JSON from route lattice rows
use crate::belt_matrix;
use crate::gap_evaluator;
use crate::suppress_filter;
use crate::cause_rank;
use crate::types::{AtlasDoc, Config, HubLatch, RouteRow, ScanRow};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::io::Write;
use std::path::Path;

pub fn route_belts(hub: &HubLatch, ledger_path: &str, out_dir: &str) -> Result<(), String> {
    let raw = fs::read_to_string(ledger_path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let _hdr = lines.next();
    let mut scans: Vec<ScanRow> = Vec::new();
    for line in lines {
        scans.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    let mut rows: Vec<RouteRow> = Vec::new();
    for scan in scans {
        let belt = belt_matrix::pick_belt(hub, &scan);
        let target = belt.as_ref().map(|b| b.target_flight_id.clone()).unwrap_or_default();
        let suppressed = suppress_filter::scan_suppressed(hub, &scan.station_code, scan.scan_minute);
        let mut connection_ok = true;
        if let Some(conn) = gap_evaluator::find_connection(hub, &target) {
            connection_ok = gap_evaluator::connection_feasible(
                hub,
                &conn.inbound_flight,
                &conn.outbound_flight,
            );
        }
        let mut row = RouteRow {
            bag_tag: scan.bag_tag,
            scan_seq: scan.scan_seq,
            belt_id: scan.belt_id,
            station_code: scan.station_code,
            scan_minute: scan.scan_minute,
            target_flight_id: target,
            connection_ok,
            outage_suppressed: suppressed,
            misroute_cause: String::new(),
        };
        row.misroute_cause = cause_rank::classify_row(&row);
        rows.push(row);
    }
    let out_path = format!("{out_dir}/{}.jsonl", hub.hub_id);
    let mut f = fs::File::create(&out_path).map_err(|e| e.to_string())?;
    writeln!(
        f,
        r#"{{"hub_id":"{}","topology_revision":{}}}"#,
        hub.hub_id, hub.topology_revision
    )
    .map_err(|e| e.to_string())?;
    for row in rows {
        let js = serde_json::to_string(&row).map_err(|e| e.to_string())?;
        writeln!(f, "{js}").map_err(|e| e.to_string())?;
    }
    Ok(())
}

pub fn write_atlas(
    _cfg: &Config,
    hub: &HubLatch,
    lattice_path: &str,
    output: &Path,
) -> Result<(), String> {
    let raw = fs::read_to_string(lattice_path).map_err(|e| e.to_string())?;
    let mut lines = raw.lines();
    let _hdr = lines.next();
    let mut rows: Vec<RouteRow> = Vec::new();
    for line in lines {
        rows.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    let mut hist: BTreeMap<String, u32> = BTreeMap::new();
    let mut misroute_count = 0u32;
    let mut suppressed_count = 0u32;
    for row in &rows {
        *hist.entry(row.misroute_cause.clone()).or_insert(0) += 1;
        if row.outage_suppressed {
            suppressed_count += 1;
        }
        if row.misroute_cause != "ROUTED_OK" {
            misroute_count += 1;
        }
    }
    let digest = audit_digest(&rows);
    let doc = AtlasDoc {
        hub_id: hub.hub_id.clone(),
        topology_revision: hub.topology_revision,
        route_row_count: rows.len() as u32,
        misroute_count,
        suppressed_count,
        cause_histogram: hist,
        audit_digest: digest,
    };
    fs::write(output, serde_json::to_string_pretty(&doc).unwrap()).map_err(|e| e.to_string())
}

fn audit_digest(rows: &[RouteRow]) -> String {
    let mut h = Sha256::new();
    for row in rows {
        h.update(format!(
            "{}|{}|{}|{}|{}",
            row.bag_tag, row.scan_seq, row.misroute_cause, row.target_flight_id, row.scan_minute
        ));
    }
    hex::encode(h.finalize())
}
