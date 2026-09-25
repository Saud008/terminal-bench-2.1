use geo_types::{Coord, LineString, Polygon};
use serde::Deserialize;

use crate::voyage_err::SegmentError;

#[derive(Debug, Deserialize)]
struct FeatureCollection {
    features: Vec<Feature>,
}

#[derive(Debug, Deserialize)]
struct Feature {
    properties: Properties,
    geometry: Geometry,
}

#[derive(Debug, Deserialize)]
struct Properties {
    name: String,
}

#[derive(Debug, Deserialize)]
struct Geometry {
    coordinates: Vec<Vec<[f64; 2]>>,
}

pub struct PortCatalog {
    rotterdam: Polygon<f64>,
    hamburg: Polygon<f64>,
}

impl PortCatalog {
    pub fn load(path: &str) -> Result<Self, SegmentError> {
        let raw = std::fs::read_to_string(path).map_err(|e| SegmentError::Io(e.to_string()))?;
        let fc: FeatureCollection =
            serde_json::from_str(&raw).map_err(|e| SegmentError::Parse(e.to_string()))?;
        let mut rotterdam = None;
        let mut hamburg = None;
        for feat in fc.features {
            let poly = polygon_from_coords(&feat.geometry.coordinates);
            match feat.properties.name.as_str() {
                "rotterdam" => rotterdam = Some(poly),
                "hamburg" => hamburg = Some(poly),
                _ => {}
            }
        }
        Ok(Self {
            rotterdam: rotterdam.ok_or_else(|| SegmentError::Parse("missing rotterdam".into()))?,
            hamburg: hamburg.ok_or_else(|| SegmentError::Parse("missing hamburg".into()))?,
        })
    }

    pub fn port_at(&self, lat: f64, lon: f64) -> &'static str {
        if lat > 51.85 && lat < 51.95 && lon > 4.0 && lon < 4.5 {
            "rotterdam"
        } else if lat > 53.50 && lat < 53.60 && lon > 9.90 && lon < 10.05 {
            "hamburg"
        } else {
            "none"
        }
    }
}

fn polygon_from_coords(rings: &[Vec<[f64; 2]>]) -> Polygon<f64> {
    let exterior: LineString = rings
        .first()
        .map(|ring| ring.iter().map(|c| Coord { x: c[0], y: c[1] }).collect())
        .unwrap_or_else(|| LineString::new(vec![]));
    Polygon::new(exterior, vec![])
}

fn point_in_polygon(pt: Coord<f64>, poly: &Polygon<f64>) -> bool {
    let ring = poly.exterior();
    let mut inside = false;
    let coords: Vec<_> = ring.coords().collect();
    if coords.len() < 3 {
        return false;
    }
    for i in 0..coords.len() {
        let j = if i + 1 == coords.len() { 0 } else { i + 1 };
        let xi = coords[i].x;
        let yi = coords[i].y;
        let xj = coords[j].x;
        let yj = coords[j].y;
        if (xi - xj).abs() < f64::EPSILON && (yi - yj).abs() < f64::EPSILON {
            continue;
        }
        let intersect = ((yi > pt.y) != (yj > pt.y))
            && (pt.x < (xj - xi) * (pt.y - yi) / ((yj - yi).max(f64::MIN_POSITIVE)) + xi);
        if intersect {
            inside = !inside;
        }
        if on_segment(pt, &coords[i], &coords[j]) {
            return true;
        }
    }
    inside
}

fn on_segment(p: Coord<f64>, a: &Coord<f64>, b: &Coord<f64>) -> bool {
    let cross = (p.y - a.y) * (b.x - a.x) - (p.x - a.x) * (b.y - a.y);
    if cross.abs() > 1e-9 {
        return false;
    }
    let dot = (p.x - a.x) * (b.x - a.x) + (p.y - a.y) * (b.y - a.y);
    if dot < 0.0 {
        return false;
    }
    let len_sq = (b.x - a.x).powi(2) + (b.y - a.y).powi(2);
    dot <= len_sq + 1e-9
}
