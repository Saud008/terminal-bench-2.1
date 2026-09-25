use crate::error::{Result, XanesError};
use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct TracePoint {
    pub e_ev: f64,
    pub mu: f64,
}

#[derive(Debug, Deserialize)]
pub struct TraceFile {
    pub trace_id: String,
    pub points: Vec<TracePoint>,
}

/// Load a μ(E) trace JSON from disk into sorted (e_ev, mu) pairs.
pub fn load_trace(path: &Path) -> Result<(String, Vec<(f64, f64)>)> {
    let raw = fs::read_to_string(path)?;
    let trace: TraceFile = serde_json::from_str(&raw)?;
    let mut points: Vec<(f64, f64)> = trace.points.iter().map(|p| (p.e_ev, p.mu)).collect();
    points.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    Ok((trace.trace_id, points))
}

pub fn validate_trace_points(points: &[(f64, f64)]) -> Result<()> {
    if points.is_empty() {
        return Err(XanesError::Msg("load: empty trace".into()));
    }
    Ok(())
}
