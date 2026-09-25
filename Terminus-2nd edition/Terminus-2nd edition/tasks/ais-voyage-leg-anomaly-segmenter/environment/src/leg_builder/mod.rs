use std::collections::BTreeMap;

use sha2::{Digest, Sha256};

use crate::port_polygons::PortCatalog;
use crate::maritime_types::{epoch_to_rfc3339, AisRow, AnomalyCounts, Policy, VoyageAtlas, VoyageLeg};

pub fn segment_voyages(
    snap_points: &[AisRow],
    ports: &PortCatalog,
    policy: Policy,
    anomalies: AnomalyCounts,
) -> VoyageAtlas {
    let mut by_mmsi: BTreeMap<u64, Vec<&AisRow>> = BTreeMap::new();
    for p in snap_points {
        by_mmsi.entry(p.mmsi).or_default().push(p);
    }
    let mut voyage_legs = Vec::new();
    for (mmsi, mut track) in by_mmsi {
        track.sort_by(|a, b| a.ts_epoch.cmp(&b.ts_epoch).then(a.seq.cmp(&b.seq)));
        let mut ordinal = 1u64;
        let mut leg_points: Vec<&AisRow> = Vec::new();
        let mut leg_start_draught = 0.0;
        let mut prev_port = "none";
        let mut prev_ts = 0i64;

        let flush = |points: &Vec<&AisRow>, ord: u64, ports_cat: &PortCatalog, legs: &mut Vec<VoyageLeg>| {
            if points.is_empty() {
                return;
            }
            let start = points[0];
            let end = points[points.len() - 1];
            let start_port = ports_cat.port_at(start.lat, start.lon);
            let end_port = ports_cat.port_at(end.lat, end.lon);
            let mut visited: Vec<String> = Vec::new();
            for pt in points {
                let label = ports_cat.port_at(pt.lat, pt.lon).to_string();
                if visited.last().map(|s| s.as_str()) != Some(label.as_str()) {
                    visited.push(label);
                }
            }
            legs.push(VoyageLeg {
                leg_id: format!("{mmsi}-L{ord}"),
                mmsi,
                start_ts: epoch_to_rfc3339(start.ts_epoch),
                end_ts: epoch_to_rfc3339(end.ts_epoch),
                point_count: points.len() as u64,
                start_port: start_port.to_string(),
                end_port: end_port.to_string(),
                ports: visited,
            });
        };

        for (idx, point) in track.iter().enumerate() {
            let port = ports.port_at(point.lat, point.lon);
            let mut split = false;
            if idx == 0 {
                leg_start_draught = point.draught;
                prev_port = port;
                prev_ts = point.ts_epoch;
                leg_points.push(point);
                continue;
            }
            if port != prev_port {
                split = true;
            }
            if (point.draught - leg_start_draught).abs() >= policy.draught_delta_m {
                split = true;
            }
            let gap_hours = (point.ts_epoch - prev_ts) as f64 / 3600.0;
            if gap_hours > policy.max_gap_hours {
                split = true;
            }
            if split {
                flush(&leg_points, ordinal, ports, &mut voyage_legs);
                ordinal += 1;
                leg_points = vec![point];
                leg_start_draught = point.draught;
            } else {
                leg_points.push(point);
            }
            prev_port = port;
            prev_ts = point.ts_epoch;
        }
        flush(&leg_points, ordinal, ports, &mut voyage_legs);
    }
    voyage_legs.sort_by(|a, b| {
        a.mmsi
            .cmp(&b.mmsi)
            .then(leg_ordinal(&a.leg_id).cmp(&leg_ordinal(&b.leg_id)))
    });
    let digest = leg_digest(&voyage_legs);
    VoyageAtlas {
        voyage_legs,
        anomalies,
        leg_chain_digest: digest,
    }
}

pub fn count_out_of_order(snap: &[AisRow]) -> u64 {
    let mut sorted = snap.to_vec();
    sorted.sort_by(|a, b| a.mmsi.cmp(&b.mmsi).then(a.ts_epoch.cmp(&b.ts_epoch)).then(a.seq.cmp(&b.seq)));
    let mut inversions = 0u64;
    for i in 0..snap.len() {
        if snap[i].seq != sorted[i].seq {
            inversions += 1;
        }
    }
    inversions
}

fn leg_ordinal(leg_id: &str) -> u64 {
    leg_id
        .rsplit('-')
        .next()
        .and_then(|s| s.strip_prefix('L'))
        .and_then(|s| s.parse::<u64>().ok())
        .unwrap_or(0)
}

fn leg_digest(legs: &[VoyageLeg]) -> String {
    let joined = legs
        .iter()
        .map(|l| l.leg_id.as_str())
        .collect::<Vec<_>>()
        .join(",");
    format!("{:x}", Sha256::digest(joined.as_bytes()))
}
