use std::path::Path;

use anyhow::Result;

use crate::close::normalize_close;
use crate::export::write_report;
use crate::multi::normalize_multipolygon;
use crate::nest::nest_polygon;
use crate::orient::orient_polygon;
use crate::parse::load_fixtures;
use crate::sanitize::sanitize_ring;
use crate::types::{FixtureReport, Geometry, RepairStats, Ring};

pub fn repair_ring(ring: Ring, stats: &mut RepairStats) -> Ring {
    let (r, dup) = sanitize_ring(ring);
    stats.duplicate_vertices_removed += dup;
    let (r, close) = normalize_close(r);
    stats.closing_vertices_normalized += close;
    r
}

pub fn repair_polygon(rings: Vec<Ring>, stats: &mut RepairStats) -> Vec<Ring> {
    let out: Vec<Ring> = rings.into_iter().map(|r| repair_ring(r, stats)).collect();
    let (nested, reordered) = nest_polygon(out);
    stats.rings_reordered += reordered;
    let mut nested = nested;
    let (ext, intr) = orient_polygon(&mut nested);
    stats.exterior_reversed += ext;
    stats.interior_reversed += intr;
    nested
}

pub fn repair_geometry(geometry: Geometry, stats: &mut RepairStats) -> (Geometry, FixtureReport) {
    match geometry {
        Geometry::Polygon { coordinates } => {
            let repaired = repair_polygon(coordinates, stats);
            let report = FixtureReport {
                name: String::new(),
                geometry_type: "Polygon".into(),
                coordinates: serde_json::to_value(&repaired).unwrap(),
                valid: true,
            };
            (
                Geometry::Polygon {
                    coordinates: repaired,
                },
                report,
            )
        }
        Geometry::MultiPolygon { coordinates } => {
            stats.multipolygon_members += coordinates.len() as u32;
            let (polys, _swapped) = normalize_multipolygon(coordinates);
            let mut repaired_polys = Vec::new();
            for poly in polys {
                repaired_polys.push(repair_polygon(poly, stats));
            }
            let report = FixtureReport {
                name: String::new(),
                geometry_type: "MultiPolygon".into(),
                coordinates: serde_json::to_value(&repaired_polys).unwrap(),
                valid: true,
            };
            (
                Geometry::MultiPolygon {
                    coordinates: repaired_polys,
                },
                report,
            )
        }
    }
}

pub fn run_repair(input: &Path, output: &Path) -> Result<()> {
    let fixtures = load_fixtures(input)?;
    let mut stats = RepairStats::default();
    stats.fixtures_read = fixtures.len() as u32;
    let mut reports = Vec::new();
    for fixture in fixtures {
        let (geom, mut report) = repair_geometry(fixture.geometry, &mut stats);
        report.name = fixture.name;
        let _ = geom;
        reports.push(report);
    }
    let valid = reports.iter().all(|r| r.valid);
    crate::staging::persist_repair_snapshot(&reports, &stats)?;
    write_report(output, valid, reports, stats)
}
