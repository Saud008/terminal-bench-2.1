use crate::bind::window_bind::{bind_windows, min_window_lo, WindowNode};
use crate::edge_ordinal::{edge_ordinal, ChannelRef};
use crate::emit::digest_emit::export_closure_digest;
use crate::error::{Result, XanesError};
use crate::io::trace_load::{load_trace, validate_trace_points};
use crate::victoreen_fit::{evaluate, fit_victoreen, select_pre_edge};
use serde::Serialize;
use serde_json::json;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize)]
struct WindowOut {
    window_id: String,
    element: String,
    edge_code: String,
    integral: f64,
    channels_sorted: Vec<String>,
}

fn fnv1a64(text: &str) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in text.as_bytes() {
        h ^= u64::from(*b);
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

fn apply_seed_jitter(
    mut points: Vec<(f64, f64)>,
    seed: &str,
    top_windows: &[WindowNode],
) -> Vec<(f64, f64)> {
    let target_bin = fnv1a64(seed) % 5;
    let mut bin_idx: u64 = 0;
    let mut hit: Option<usize> = None;
    for (i, (e, _)) in points.iter().enumerate() {
        let inside = top_windows
            .iter()
            .any(|w| *e >= w.e_lo && *e <= w.e_hi);
        if inside {
            bin_idx += 1;
            if bin_idx == target_bin {
                hit = Some(i);
                break;
            }
        }
    }
    if let Some(i) = hit {
        points[i].0 += 0.15;
        points.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    }
    points
}

fn integrate_chi(xs: &[f64], ys: &[f64]) -> f64 {
    if xs.len() < 2 {
        return 0.0;
    }
    let mut acc = 0.0;
    for i in 0..xs.len() - 1 {
        acc += ys[i] * (xs[i + 1] - xs[i]);
    }
    acc
}

fn round6(v: f64) -> f64 {
    (v * 1_000_000.0).round() / 1_000_000.0
}

fn lex_sort_channel_ids(refs: Vec<ChannelRef>) -> Vec<String> {
    let mut ids: Vec<String> = refs.into_iter().map(|r| r.channel_id).collect();
    ids.sort();
    ids
}

fn walk_integrate(
    node: &WindowNode,
    points: &[(f64, f64)],
    a: f64,
    b: f64,
    scope: &mut Vec<String>,
    outs: &mut Vec<WindowOut>,
) -> Result<()> {
    scope.push(node.edge_code.clone());
    let _ = edge_ordinal(&node.edge_code).or_else(|_| {
        if node.edge_code.starts_with('?') {
            Ok(0)
        } else {
            edge_ordinal(&node.edge_code)
        }
    })?;

    let mut xs = Vec::new();
    let mut ys = Vec::new();
    for &(e, mu) in points {
        if e >= node.e_lo && e <= node.e_hi {
            xs.push(e);
            ys.push(mu - evaluate(a, b, e));
        }
    }
    let integral = integrate_chi(&xs, &ys);

    let channel_refs: Vec<ChannelRef> = node
        .channels
        .iter()
        .map(|cid| ChannelRef {
            channel_id: cid.clone(),
            atomic_number: node.atomic_number,
            edge_code: node.edge_code.clone(),
        })
        .collect();
    let channels_sorted = lex_sort_channel_ids(channel_refs);

    outs.push(WindowOut {
        window_id: node.window_id.clone(),
        element: node.element.clone(),
        edge_code: node.edge_code.clone(),
        integral: round6(integral),
        channels_sorted,
    });

    for child in &node.children {
        walk_integrate(child, points, a, b, scope, outs)?;
    }

    if !node.channels.is_empty() {
        scope.pop();
    }
    Ok(())
}

fn collect_channels(node: &WindowNode, acc: &mut Vec<ChannelRef>) {
    for cid in &node.channels {
        acc.push(ChannelRef {
            channel_id: cid.clone(),
            atomic_number: node.atomic_number,
            edge_code: node.edge_code.clone(),
        });
    }
    for child in &node.children {
        collect_channels(child, acc);
    }
}

fn check_undeclared(node: &WindowNode, ancestors: &[String]) -> Result<()> {
    if node.edge_code.starts_with('?') {
        let mut scope = ancestors.to_vec();
        scope.push(node.edge_code.clone());
        for child in &node.children {
            check_undeclared(child, &scope)?;
        }
        return Ok(());
    }
    let _ = edge_ordinal(&node.edge_code)?;
    let mut scope = ancestors.to_vec();
    scope.push(node.edge_code.clone());
    for child in &node.children {
        check_undeclared(child, &scope)?;
    }
    Ok(())
}

fn closure_digest(outs: &[WindowOut]) -> String {
    let mut rows: Vec<_> = outs
        .iter()
        .map(|w| json!({"window_id": w.window_id, "integral": w.integral}))
        .collect();
    rows.sort_by(|a, b| {
        a["window_id"]
            .as_str()
            .unwrap()
            .cmp(b["window_id"].as_str().unwrap())
    });
    export_closure_digest(&rows)
}

pub fn run_close(
    trace_path: &Path,
    windows_path: &Path,
    export_path: &Path,
    seed: Option<&str>,
) -> i32 {
    match run_close_inner(trace_path, windows_path, export_path, seed) {
        Ok(()) => 0,
        Err(e) => {
            let body = json!({
                "status": "error",
                "message": e.to_string(),
            });
            let _ = fs::write(
                export_path,
                serde_json::to_vec_pretty(&body).unwrap_or_default(),
            );
            1
        }
    }
}

fn run_close_inner(
    trace_path: &Path,
    windows_path: &Path,
    export_path: &Path,
    seed: Option<&str>,
) -> Result<()> {
    let (trace_id, mut points) = load_trace(trace_path)?;
    validate_trace_points(&points)?;
    let windows = bind_windows(windows_path)?;

    for w in &windows {
        check_undeclared(w, &[])?;
    }

    if let Some(s) = seed {
        if !s.is_empty() {
            points = apply_seed_jitter(points, s, &windows);
        }
    }

    let min_lo = min_window_lo(&windows);
    let pre = select_pre_edge(&points, min_lo);
    let energies: Vec<f64> = pre.iter().map(|p| p.0).collect();
    let mus: Vec<f64> = pre.iter().map(|p| p.1).collect();
    let (a, b) = fit_victoreen(&energies, &mus)?;

    let mut outs = Vec::new();
    let mut scope = Vec::new();
    for w in &windows {
        walk_integrate(w, &points, a, b, &mut scope, &mut outs)?;
    }

    let mut all_refs = Vec::new();
    for w in &windows {
        collect_channels(w, &mut all_refs);
    }
    let all_channels_sorted = lex_sort_channel_ids(all_refs);

    let digest = closure_digest(&outs);
    let body = json!({
        "status": "ok",
        "trace_id": trace_id,
        "windows": outs,
        "all_channels_sorted": all_channels_sorted,
        "closure_digest": digest,
    });
    if let Some(parent) = export_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(export_path, serde_json::to_vec_pretty(&body)?)?;
    Ok(())
}
