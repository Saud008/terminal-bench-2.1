use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AxisTransform {
    pub scale: f64,
    pub offset: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AxisCoordinate {
    pub transform: AxisTransform,
    pub length: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArrayAxes {
    pub dims: Vec<String>,
    pub coordinates: BTreeMap<String, AxisCoordinate>,
}

pub type AxesFile = BTreeMap<String, ArrayAxes>;

#[derive(Debug)]
pub struct AxisError;

pub fn load_axes_catalog(path: &Path) -> Result<AxesFile, AxisError> {
    let raw = fs::read_to_string(path).map_err(|_| AxisError)?;
    serde_json::from_str(&raw).map_err(|_| AxisError)
}

pub fn world_coord(index: u64, coord: &AxisCoordinate) -> f64 {
    coord.transform.offset + coord.transform.scale * index as f64
}

pub fn axis_span(coord: &AxisCoordinate) -> (f64, f64) {
    let start = world_coord(0, coord);
    let end = world_coord(coord.length.saturating_sub(1), coord);
    (start.min(end), start.max(end))
}

pub fn shape_matches_axes(shape: &[u64], axes: &ArrayAxes) -> bool {
    if shape.len() != axes.dims.len() {
        return false;
    }
    for (dim_name, shape_len) in axes.dims.iter().zip(shape.iter().rev()) {
        let Some(coord) = axes.coordinates.get(dim_name) else {
            return false;
        };
        if coord.length != *shape_len {
            return false;
        }
    }
    true
}
