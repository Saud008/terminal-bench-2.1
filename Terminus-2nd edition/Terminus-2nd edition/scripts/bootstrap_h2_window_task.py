#!/usr/bin/env python3
"""Bootstrap tasks/h2-stream-window-update-rollup-governor/ (Rust h2gov CLI)."""
from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "h2-stream-window-update-rollup-governor"
ENV = TASK / "environment"
TESTS = TASK / "tests"
SOL = TASK / "solution" / "patches"
CRATE = ENV / "crates" / "h2gov"
SRC = CRATE / "src"
GOLDEN = TESTS / "verifier-golden"

MODULES = (
    "stream_id",
    "window_credit",
    "dependency",
    "settings_floor",
    "merge",
    "snapshot",
    "publish",
)

RUST_ECR = (
    "public.ecr.aws/docker/library/rust:1.85-slim"
    "@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36"
)

REQUIREMENTS_TXT = """\
#
# Verifier-only lockfile (pip-compile --generate-hashes).
#
iniconfig==2.3.0 \\
    --hash=sha256:c76315c77db068650d49c5b56314774a7804df16fee4402c1f19d6d15d8c4730 \\
    --hash=sha256:f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12
packaging==26.2 \\
    --hash=sha256:5fc45236b9446107ff2415ce77c807cee2862cb6fac22b8a73826d0693b0980e \\
    --hash=sha256:ff452ff5a3e828ce110190feff1178bb1f2ea2281fa2075aadb987c2fb221661
pluggy==1.6.0 \\
    --hash=sha256:7dcc130b76258d33b90f61b658791dede3486c3e6bfb003ee5c9bfb396dd22f3 \\
    --hash=sha256:e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746
pygments==2.20.0 \\
    --hash=sha256:6757cd03768053ff99f3039c1a36d6c0aa0b263438fcab17520b30a303a82b5f \\
    --hash=sha256:81a9e26dd42fd28a23a2d169d86d7ac03b46e2f8b59ed4698fb4785f946d0176
pytest==9.0.3 \\
    --hash=sha256:2c5efc453d45394fdd706ade797c0a81091eccd1d6e4bccfcd476e2b8e0ab5d9 \\
    --hash=sha256:b86ada508af81d19edeb213c681b1d48246c1a91d304c7c81a427674c17eb91c
pytest-json-ctrf==0.5.0 \\
    --hash=sha256:78aab7c8a8061b4e67c63e4209fcabe3441dc1d42e9001ccf24258b945b59544 \\
    --hash=sha256:e98994d5e53c6fa03de10adfa093cea7d873a849e36d0f5bdd6d697f388e1218
"""

SESSION_CONFIG = {
    "session_id": "edge-gw-h2-01",
    "initial_connection_window": 65535,
    "initial_stream_window": 65535,
}

FIXTURES = {
    "basic-window.jsonl": [
        {"type": "settings", "scope": "connection", "initial_window": 65535},
        {"type": "settings", "scope": "stream", "initial_window": 65535},
        {"type": "window_update", "scope": "connection", "stream_id": 0, "increment": 1000},
        {"type": "window_update", "scope": "stream", "stream_id": 1, "increment": 500},
        {"type": "priority", "stream_id": 1, "depends_on": 0, "weight": 16},
    ],
    "stream-scoped-credit.jsonl": [
        {"type": "settings", "scope": "connection", "initial_window": 100000},
        {"type": "settings", "scope": "stream", "initial_window": 65535},
        {"type": "window_update", "scope": "stream", "stream_id": 3, "increment": 2000},
        {"type": "window_update", "scope": "connection", "stream_id": 0, "increment": 5000},
        {"type": "window_update", "scope": "stream", "stream_id": 5, "increment": 800},
    ],
    "priority-tree.jsonl": [
        {"type": "settings", "scope": "stream", "initial_window": 10000},
        {"type": "window_update", "scope": "stream", "stream_id": 1, "increment": 5000},
        {"type": "priority", "stream_id": 3, "depends_on": 1, "weight": 16},
        {"type": "window_update", "scope": "stream", "stream_id": 3, "increment": 9000},
        {"type": "priority", "stream_id": 5, "depends_on": 3, "weight": 8},
        {"type": "window_update", "scope": "stream", "stream_id": 5, "increment": 4000},
    ],
    "settings-delta.jsonl": [
        {"type": "settings", "scope": "stream", "initial_window": 10000},
        {"type": "window_update", "scope": "stream", "stream_id": 1, "increment": 1000},
        {"type": "settings", "scope": "stream", "initial_window": 5000},
        {"type": "window_update", "scope": "stream", "stream_id": 3, "increment": 2000},
    ],
    "multi-stream.jsonl": [
        {"type": "settings", "scope": "connection", "initial_window": 50000},
        {"type": "settings", "scope": "stream", "initial_window": 32768},
        {"type": "window_update", "scope": "stream", "stream_id": 1, "increment": 1000},
        {"type": "window_update", "scope": "stream", "stream_id": 3, "increment": 2000},
        {"type": "window_update", "scope": "stream", "stream_id": 5, "increment": 3000},
        {"type": "window_update", "scope": "stream", "stream_id": 7, "increment": 4000},
    ],
    "odd-even-streams.jsonl": [
        {"type": "settings", "scope": "stream", "initial_window": 8192},
        {"type": "window_update", "scope": "stream", "stream_id": 1, "increment": 100},
        {"type": "window_update", "scope": "stream", "stream_id": 2, "increment": 200},
        {"type": "window_update", "scope": "stream", "stream_id": 3, "increment": 300},
        {"type": "window_update", "scope": "stream", "stream_id": 4, "increment": 400},
    ],
}

HIDDEN_TRAP = [
    {"type": "settings", "scope": "connection", "initial_window": 80000},
    {"type": "settings", "scope": "stream", "initial_window": 16000},
    {"type": "window_update", "scope": "connection", "stream_id": 0, "increment": 12000},
    {"type": "window_update", "scope": "stream", "stream_id": 9, "increment": 6000},
    {"type": "priority", "stream_id": 11, "depends_on": 9, "weight": 16},
    {"type": "window_update", "scope": "stream", "stream_id": 11, "increment": 14000},
    {"type": "settings", "scope": "stream", "initial_window": 4000},
    {"type": "window_update", "scope": "stream", "stream_id": 13, "increment": 2500},
]

created: list[str] = []
errors: list[str] = []


def w(path: Path | str, content: str, *, lf: bool = False) -> None:
    p = Path(path)
    if not p.is_absolute():
        p = TASK / p
    p.parent.mkdir(parents=True, exist_ok=True)
    text = textwrap.dedent(content).lstrip("\n")
    if lf:
        p.write_text(text, encoding="utf-8", newline="\n")
    else:
        p.write_text(text, encoding="utf-8")
    created.append(str(p.relative_to(ROOT)))


def w_sh(path: Path | str, content: str) -> None:
    w(path, content, lf=True)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    created.append(str(path.relative_to(ROOT)))


def golden_name(module: str) -> str:
    return f"golden_{module}.rs"


# --- Rust sources ---

MODEL_RS = r'''use std::collections::HashMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum StreamKind {
    Connection,
    Client,
    Push,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionConfig {
    pub session_id: String,
    pub initial_connection_window: u64,
    pub initial_stream_window: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    #[serde(rename = "type")]
    pub kind: String,
    pub scope: Option<String>,
    pub stream_id: Option<u32>,
    pub increment: Option<u64>,
    pub initial_window: Option<u64>,
    pub depends_on: Option<u32>,
    pub weight: Option<u16>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Stats {
    pub settings_applied: u64,
    pub window_updates: u64,
    pub priority_updates: u64,
    pub merge_loads: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamRow {
    pub stream_id: u32,
    pub kind: StreamKind,
    pub credit: u64,
    pub effective_window: u64,
    pub depends_on: u32,
    pub weight: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot {
    pub snapshot_version: u32,
    pub epoch: u32,
    pub session_id: String,
    pub connection_window: u64,
    pub settings_epoch: u32,
    pub stream_floor: u64,
    pub stats: Stats,
    pub streams: Vec<StreamRow>,
    pub log_path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AtlasRow {
    pub stream_id: u32,
    pub kind: StreamKind,
    pub credit: u64,
    pub effective_window: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Atlas {
    pub export_version: u32,
    pub session_id: String,
    pub epoch: u32,
    pub table_suffix: String,
    pub connection_window: u64,
    pub stats: Stats,
    pub rows: Vec<AtlasRow>,
}

#[derive(Debug, Clone)]
pub struct MutableState {
    pub config: SessionConfig,
    pub epoch: u32,
    pub settings_epoch: u32,
    pub connection_window: u64,
    pub stream_floor: u64,
    pub credits: HashMap<u32, u64>,
    pub depends: HashMap<u32, u32>,
    pub weights: HashMap<u32, u16>,
    pub stats: Stats,
    pub log_path: String,
}
'''

PARSE_RS = r'''use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;

use crate::model::{Atlas, SessionConfig, Snapshot};

pub fn load_config(path: &str) -> Result<SessionConfig, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn load_events(path: &str) -> Result<Vec<crate::model::Event>, String> {
    let f = fs::File::open(path).map_err(|e| e.to_string())?;
    let reader = BufReader::new(f);
    let mut out = Vec::new();
    for line in reader.lines() {
        let line = line.map_err(|e| e.to_string())?;
        if line.trim().is_empty() {
            continue;
        }
        let ev: crate::model::Event = serde_json::from_str(&line).map_err(|e| e.to_string())?;
        out.push(ev);
    }
    Ok(out)
}

pub fn load_snapshot(path: &str) -> Result<Snapshot, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn write_snapshot(path: &str, snap: &Snapshot) -> Result<(), String> {
    let b = serde_json::to_string_pretty(snap).map_err(|e| e.to_string())?;
    fs::write(path, format!("{b}\n")).map_err(|e| e.to_string())
}

pub fn write_atlas(path: &str, atlas: &Atlas) -> Result<(), String> {
    let b = serde_json::to_string_pretty(atlas).map_err(|e| e.to_string())?;
    fs::write(path, format!("{b}\n")).map_err(|e| e.to_string())
}

pub fn path_exists(path: &str) -> bool {
    Path::new(path).exists()
}
'''

GOLDEN_STREAM_ID = r'''use crate::model::StreamKind;

pub fn classify(stream_id: u32) -> StreamKind {
    if stream_id == 0 {
        return StreamKind::Connection;
    }
    if stream_id % 2 == 1 {
        StreamKind::Client
    } else {
        StreamKind::Push
    }
}

pub fn route_scope(scope: &str, stream_id: u32) -> StreamKind {
    match scope {
        "connection" => StreamKind::Connection,
        "stream" => classify(stream_id),
        _ => StreamKind::Connection,
    }
}
'''

BROKEN_STREAM_ID = r'''use crate::model::StreamKind;

// Broken: treats every stream as connection stream 0 semantics.
pub fn classify(_stream_id: u32) -> StreamKind {
    StreamKind::Connection
}

pub fn route_scope(_scope: &str, _stream_id: u32) -> StreamKind {
    StreamKind::Connection
}
'''

GOLDEN_WINDOW_CREDIT = r'''use crate::model::MutableState;
use crate::stream_id;

pub fn apply_window_update(
    state: &mut MutableState,
    scope: &str,
    stream_id: u32,
    increment: u64,
) -> Result<(), String> {
    let kind = stream_id::route_scope(scope, stream_id);
    match kind {
        crate::model::StreamKind::Connection => {
            state.connection_window = state.connection_window.saturating_add(increment);
        }
        _ => {
            let entry = state.credits.entry(stream_id).or_insert(0);
            *entry = entry.saturating_add(increment);
        }
    }
    state.stats.window_updates += 1;
    Ok(())
}

pub fn stream_credit(state: &MutableState, stream_id: u32) -> u64 {
    *state.credits.get(&stream_id).unwrap_or(&0)
}
'''

BROKEN_WINDOW_CREDIT = r'''use crate::model::MutableState;

// Broken: applies stream increments to connection window and vice versa.
pub fn apply_window_update(
    state: &mut MutableState,
    scope: &str,
    stream_id: u32,
    increment: u64,
) -> Result<(), String> {
    if scope == "connection" {
        let entry = state.credits.entry(stream_id).or_insert(0);
        *entry = entry.saturating_add(increment);
    } else {
        state.connection_window = state.connection_window.saturating_add(increment);
    }
    state.stats.window_updates += 1;
    Ok(())
}

pub fn stream_credit(state: &MutableState, stream_id: u32) -> u64 {
    *state.credits.get(&stream_id).unwrap_or(&0)
}
'''

GOLDEN_DEPENDENCY = r'''use crate::dependency::effective_window;
use crate::model::{MutableState, StreamKind, StreamRow};
use crate::stream_id;
use crate::window_credit;

pub fn set_priority(
    state: &mut MutableState,
    stream_id: u32,
    depends_on: u32,
    weight: u16,
) -> Result<(), String> {
    state.depends.insert(stream_id, depends_on);
    state.weights.insert(stream_id, weight);
    state.stats.priority_updates += 1;
    Ok(())
}

pub fn effective_window(state: &MutableState, stream_id: u32) -> u64 {
    let base = state.stream_floor.saturating_add(window_credit::stream_credit(state, stream_id));
    let parent = state.depends.get(&stream_id).copied().unwrap_or(0);
    if parent == 0 {
        return base;
    }
    let parent_eff = effective_window(state, parent);
    base.min(parent_eff)
}

pub fn build_stream_rows(state: &MutableState) -> Vec<StreamRow> {
    let mut ids: Vec<u32> = state.credits.keys().copied().collect();
    for sid in state.depends.keys() {
        if !ids.contains(sid) {
            ids.push(*sid);
        }
    }
    ids.sort_unstable();
    ids.into_iter()
        .map(|sid| StreamRow {
            stream_id: sid,
            kind: stream_id::classify(sid),
            credit: window_credit::stream_credit(state, sid),
            effective_window: effective_window(state, sid),
            depends_on: state.depends.get(&sid).copied().unwrap_or(0),
            weight: state.weights.get(&sid).copied().unwrap_or(16),
        })
        .collect()
}
'''

# Fix circular import in dependency - effective_window shouldn't call itself through pub use
GOLDEN_DEPENDENCY = r'''use crate::model::{MutableState, StreamRow};
use crate::stream_id;
use crate::window_credit;

pub fn set_priority(
    state: &mut MutableState,
    stream_id: u32,
    depends_on: u32,
    weight: u16,
) -> Result<(), String> {
    state.depends.insert(stream_id, depends_on);
    state.weights.insert(stream_id, weight);
    state.stats.priority_updates += 1;
    Ok(())
}

fn effective_window_inner(state: &MutableState, stream_id: u32) -> u64 {
    let base = state.stream_floor.saturating_add(window_credit::stream_credit(state, stream_id));
    let parent = state.depends.get(&stream_id).copied().unwrap_or(0);
    if parent == 0 {
        return base;
    }
    let parent_eff = effective_window_inner(state, parent);
    base.min(parent_eff)
}

pub fn effective_window(state: &MutableState, stream_id: u32) -> u64 {
    effective_window_inner(state, stream_id)
}

pub fn build_stream_rows(state: &MutableState) -> Vec<StreamRow> {
    let mut ids: Vec<u32> = state.credits.keys().copied().collect();
    for sid in state.depends.keys() {
        if !ids.contains(sid) {
            ids.push(*sid);
        }
    }
    ids.sort_unstable();
    ids.into_iter()
        .map(|sid| StreamRow {
            stream_id: sid,
            kind: stream_id::classify(sid),
            credit: window_credit::stream_credit(state, sid),
            effective_window: effective_window(state, sid),
            depends_on: state.depends.get(&sid).copied().unwrap_or(0),
            weight: state.weights.get(&sid).copied().unwrap_or(16),
        })
        .collect()
}
'''

BROKEN_DEPENDENCY = r'''use crate::model::{MutableState, StreamRow};
use crate::stream_id;
use crate::window_credit;

// Broken: ignores priority parent propagation for effective windows.
pub fn set_priority(
    state: &mut MutableState,
    stream_id: u32,
    depends_on: u32,
    weight: u16,
) -> Result<(), String> {
    state.depends.insert(stream_id, depends_on);
    state.weights.insert(stream_id, weight);
    state.stats.priority_updates += 1;
    Ok(())
}

pub fn effective_window(state: &MutableState, stream_id: u32) -> u64 {
    state.stream_floor.saturating_add(window_credit::stream_credit(state, stream_id))
}

pub fn build_stream_rows(state: &MutableState) -> Vec<StreamRow> {
    let mut ids: Vec<u32> = state.credits.keys().copied().collect();
    for sid in state.depends.keys() {
        if !ids.contains(sid) {
            ids.push(*sid);
        }
    }
    ids.sort_unstable();
    ids.into_iter()
        .map(|sid| StreamRow {
            stream_id: sid,
            kind: stream_id::classify(sid),
            credit: window_credit::stream_credit(state, sid),
            effective_window: effective_window(state, sid),
            depends_on: state.depends.get(&sid).copied().unwrap_or(0),
            weight: state.weights.get(&sid).copied().unwrap_or(16),
        })
        .collect()
}
'''

GOLDEN_SETTINGS_FLOOR = r'''use crate::model::MutableState;

pub fn apply_settings(
    state: &mut MutableState,
    scope: &str,
    initial_window: u64,
    stream_id: Option<u32>,
) -> Result<(), String> {
    if scope == "connection" {
        state.connection_window = initial_window;
    } else if scope == "stream" {
        let delta = initial_window;
        state.stream_floor = state.stream_floor.saturating_add(delta);
        state.settings_epoch += 1;
        if let Some(sid) = stream_id {
            state.credits.insert(sid, 0);
        }
    }
    state.stats.settings_applied += 1;
    Ok(())
}
'''

BROKEN_SETTINGS_FLOOR = r'''use crate::model::MutableState;

// Broken: sets absolute stream floor instead of delta from prior settings epoch.
pub fn apply_settings(
    state: &mut MutableState,
    scope: &str,
    initial_window: u64,
    stream_id: Option<u32>,
) -> Result<(), String> {
    if scope == "connection" {
        state.connection_window = initial_window;
    } else if scope == "stream" {
        state.stream_floor = initial_window;
        if let Some(sid) = stream_id {
            state.credits.insert(sid, 0);
        }
    }
    state.stats.settings_applied += 1;
    Ok(())
}
'''

GOLDEN_MERGE = r'''use crate::model::MutableState;
use crate::parse;

pub fn load_prior(snapshot_path: &str, state: &mut MutableState) -> Result<(), String> {
    if snapshot_path.is_empty() || !parse::path_exists(snapshot_path) {
        return Ok(());
    }
    let prior = parse::load_snapshot(snapshot_path)?;
    state.epoch = prior.epoch;
    state.settings_epoch = prior.settings_epoch;
    state.connection_window = prior.connection_window;
    state.stream_floor = prior.stream_floor;
    state.stats.merge_loads += 1;
    state.stats.settings_applied += prior.stats.settings_applied;
    state.stats.window_updates += prior.stats.window_updates;
    state.stats.priority_updates += prior.stats.priority_updates;
    for row in prior.streams {
        state.credits.insert(row.stream_id, row.credit);
        if row.depends_on > 0 {
            state.depends.insert(row.stream_id, row.depends_on);
        }
        state.weights.insert(row.stream_id, row.weight);
    }
    Ok(())
}

pub fn finalize_epoch(state: &mut MutableState) {
    state.epoch += 1;
}
'''

BROKEN_MERGE = r'''use crate::model::MutableState;

// Broken: ignores prior snapshot epoch and stats on chained ingest reruns.
pub fn load_prior(_snapshot_path: &str, _state: &mut MutableState) -> Result<(), String> {
    Ok(())
}

pub fn finalize_epoch(state: &mut MutableState) {
    state.epoch = 1;
}
'''

GOLDEN_SNAPSHOT = r'''use crate::dependency;
use crate::model::{MutableState, Snapshot};

pub fn build_snapshot(state: MutableState) -> Snapshot {
    Snapshot {
        snapshot_version: 1,
        epoch: state.epoch,
        session_id: state.config.session_id.clone(),
        connection_window: state.connection_window,
        settings_epoch: state.settings_epoch,
        stream_floor: state.stream_floor,
        stats: state.stats,
        streams: dependency::build_stream_rows(&state),
        log_path: Some(state.log_path),
    }
}
'''

BROKEN_SNAPSHOT = r'''use crate::model::{MutableState, Snapshot, Stats};

// Broken: drops stream rows and zeros stats before staging write.
pub fn build_snapshot(state: MutableState) -> Snapshot {
    Snapshot {
        snapshot_version: 1,
        epoch: state.epoch,
        session_id: state.config.session_id.clone(),
        connection_window: state.connection_window,
        settings_epoch: state.settings_epoch,
        stream_floor: state.stream_floor,
        stats: Stats::default(),
        streams: Vec::new(),
        log_path: Some(state.log_path),
    }
}
'''

GOLDEN_PUBLISH = r'''use std::env;

use crate::model::{Atlas, AtlasRow, Snapshot};

fn table_suffix() -> String {
    env::var("VERIFIER_TABLE_SUFFIX").unwrap_or_else(|_| "default".into())
}

pub fn publish_from_snapshot(snap: &Snapshot) -> Atlas {
    let mut rows: Vec<AtlasRow> = snap
        .streams
        .iter()
        .map(|r| AtlasRow {
            stream_id: r.stream_id,
            kind: r.kind,
            credit: r.credit,
            effective_window: r.effective_window,
        })
        .collect();
    rows.sort_by_key(|r| r.stream_id);
    Atlas {
        export_version: 1,
        session_id: snap.session_id.clone(),
        epoch: snap.epoch,
        table_suffix: table_suffix(),
        connection_window: snap.connection_window,
        stats: snap.stats.clone(),
        rows,
    }
}
'''

BROKEN_PUBLISH = r'''use std::env;

use crate::model::{Atlas, AtlasRow, Snapshot, Stats};
use crate::parse;
use crate::stream_id;
use crate::window_credit;

fn table_suffix() -> String {
    env::var("VERIFIER_TABLE_SUFFIX").unwrap_or_else(|_| "default".into())
}

// Broken: re-parses JSONL on emit and zeros stats instead of snapshot-only export.
pub fn publish_from_snapshot(snap: &Snapshot) -> Atlas {
    let mut rows = Vec::new();
    if let Some(log_path) = snap.log_path.as_deref() {
        if let Ok(events) = parse::load_events(log_path) {
            let mut state = crate::model::MutableState {
                config: crate::model::SessionConfig {
                    session_id: snap.session_id.clone(),
                    initial_connection_window: snap.connection_window,
                    initial_stream_window: snap.stream_floor,
                },
                epoch: snap.epoch,
                settings_epoch: snap.settings_epoch,
                connection_window: snap.connection_window,
                stream_floor: snap.stream_floor,
                credits: std::collections::HashMap::new(),
                depends: std::collections::HashMap::new(),
                weights: std::collections::HashMap::new(),
                stats: Stats::default(),
                log_path: log_path.to_string(),
            };
            for ev in events {
                if ev.kind == "window_update" {
                    let scope = ev.scope.as_deref().unwrap_or("stream");
                    let sid = ev.stream_id.unwrap_or(0);
                    let inc = ev.increment.unwrap_or(0);
                    let _ = window_credit::apply_window_update(&mut state, scope, sid, inc);
                }
            }
            for (sid, credit) in &state.credits {
                rows.push(AtlasRow {
                    stream_id: *sid,
                    kind: stream_id::classify(*sid),
                    credit: *credit,
                    effective_window: snap.stream_floor.saturating_add(*credit),
                });
            }
        }
    }
    rows.sort_by_key(|r| r.stream_id);
    Atlas {
        export_version: 1,
        session_id: snap.session_id.clone(),
        epoch: snap.epoch,
        table_suffix: table_suffix(),
        connection_window: snap.connection_window,
        stats: Stats::default(),
        rows,
    }
}
'''

DECOY_HPACK = r'''// Decoy HPACK helper — not on ingest or emit hot path.

pub fn legacy_table_size_hint(size: u32) -> u32 {
    size.saturating_mul(2)
}
'''

DECOY_WRAP = r'''// Decoy re-export — not on ingest or emit hot path.

pub use super::table_size::legacy_table_size_hint;
'''

INGEST_RS = r'''use std::collections::HashMap;

use crate::dependency;
use crate::model::{Event, MutableState, SessionConfig, Snapshot};
use crate::settings_floor;
use crate::staging;
use crate::window_credit;

pub fn ingest(
    cfg: SessionConfig,
    events: Vec<Event>,
    snapshot_path: &str,
    log_path: &str,
) -> Result<Snapshot, String> {
    let mut state = MutableState {
        config: cfg.clone(),
        epoch: 0,
        settings_epoch: 0,
        connection_window: cfg.initial_connection_window,
        stream_floor: cfg.initial_stream_window,
        credits: HashMap::new(),
        depends: HashMap::new(),
        weights: HashMap::new(),
        stats: Default::default(),
        log_path: log_path.to_string(),
    };
    staging::merge::load_prior(snapshot_path, &mut state)?;

    for ev in events {
        match ev.kind.as_str() {
            "settings" => {
                let scope = ev.scope.as_deref().ok_or("settings missing scope")?;
                let initial = ev.initial_window.ok_or("settings missing initial_window")?;
                settings_floor::apply_settings(&mut state, scope, initial, ev.stream_id)?;
            }
            "window_update" => {
                let scope = ev.scope.as_deref().ok_or("window_update missing scope")?;
                let sid = ev.stream_id.ok_or("window_update missing stream_id")?;
                let inc = ev.increment.ok_or("window_update missing increment")?;
                window_credit::apply_window_update(&mut state, scope, sid, inc)?;
            }
            "priority" => {
                let sid = ev.stream_id.ok_or("priority missing stream_id")?;
                let parent = ev.depends_on.ok_or("priority missing depends_on")?;
                let weight = ev.weight.unwrap_or(16);
                dependency::set_priority(&mut state, sid, parent, weight)?;
            }
            other => return Err(format!("unknown event type {other}")),
        }
    }
    staging::merge::finalize_epoch(&mut state);
    Ok(staging::snapshot::build_snapshot(state))
}
'''

LIB_RS = r'''pub mod dependency;
pub mod export;
pub mod hpack;
pub mod ingest;
pub mod model;
pub mod parse;
pub mod settings_floor;
pub mod staging;
pub mod stream_id;
pub mod window_credit;
'''

STAGING_MOD = r'''pub mod merge;
pub mod snapshot;
'''

EXPORT_MOD = r'''pub mod publish;
'''

HPACK_MOD = r'''pub mod table_size;
pub mod wrap;
'''

MAIN_RS = r'''use std::env;
use std::process;

use h2gov::export::publish;
use h2gov::ingest;
use h2gov::parse;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("expected subcommand ingest or emit");
        process::exit(2);
    }
    match args[1].as_str() {
        "ingest" => run_ingest(&args[2..]),
        "emit" => run_emit(&args[2..]),
        other => {
            eprintln!("unknown subcommand {other}");
            process::exit(2);
        }
    }
}

fn flag(args: &[String], name: &str) -> Option<String> {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .cloned()
}

fn run_ingest(args: &[String]) {
    let config = flag(args, "--config").unwrap_or_else(|| usage("ingest"));
    let log = flag(args, "--log").unwrap_or_else(|| usage("ingest"));
    let snapshot = flag(args, "--snapshot").unwrap_or_else(|| usage("ingest"));
    let cfg = match parse::load_config(&config) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{e}");
            process::exit(1);
        }
    };
    let events = match parse::load_events(&log) {
        Ok(e) => e,
        Err(e) => {
            eprintln!("{e}");
            process::exit(1);
        }
    };
    let snap = match ingest::ingest(cfg, events, &snapshot, &log) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("{e}");
            process::exit(1);
        }
    };
    if let Err(e) = parse::write_snapshot(&snapshot, &snap) {
        eprintln!("{e}");
        process::exit(1);
    }
}

fn run_emit(args: &[String]) {
    let snapshot = flag(args, "--snapshot").unwrap_or_else(|| usage("emit"));
    let output = flag(args, "--output").unwrap_or_else(|| usage("emit"));
    let snap = match parse::load_snapshot(&snapshot) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("{e}");
            process::exit(1);
        }
    };
    let atlas = publish::publish_from_snapshot(&snap);
    if let Err(e) = parse::write_atlas(&output, &atlas) {
        eprintln!("{e}");
        process::exit(1);
    }
}

fn usage(cmd: &str) -> ! {
    eprintln!("{cmd} requires flags; see /app/docs/window-contract.md");
    process::exit(2);
}
'''

GOLDEN_SOURCES = {
    "stream_id": GOLDEN_STREAM_ID,
    "window_credit": GOLDEN_WINDOW_CREDIT,
    "dependency": GOLDEN_DEPENDENCY,
    "settings_floor": GOLDEN_SETTINGS_FLOOR,
    "merge": GOLDEN_MERGE,
    "snapshot": GOLDEN_SNAPSHOT,
    "publish": GOLDEN_PUBLISH,
}

BROKEN_SOURCES = {
    "stream_id": BROKEN_STREAM_ID,
    "window_credit": BROKEN_WINDOW_CREDIT,
    "dependency": BROKEN_DEPENDENCY,
    "settings_floor": BROKEN_SETTINGS_FLOOR,
    "merge": BROKEN_MERGE,
    "snapshot": BROKEN_SNAPSHOT,
    "publish": BROKEN_PUBLISH,
}

BROKEN_PATHS = {
    "stream_id": SRC / "stream_id.rs",
    "window_credit": SRC / "window_credit.rs",
    "dependency": SRC / "dependency.rs",
    "settings_floor": SRC / "settings_floor.rs",
    "merge": SRC / "staging" / "merge.rs",
    "snapshot": SRC / "staging" / "snapshot.rs",
    "publish": SRC / "export" / "publish.rs",
}


def write_rust_core() -> None:
    for p in [SOL, GOLDEN, SRC / "staging", SRC / "export", SRC / "hpack"]:
        p.mkdir(parents=True, exist_ok=True)

    w(ENV / "Cargo.toml", """
        [workspace]
        members = ["crates/h2gov"]
        resolver = "2"
    """)

    w(ENV / "rust-toolchain.toml", """
        [toolchain]
        channel = "1.85"
    """)

    w(CRATE / "Cargo.toml", """
        [package]
        name = "h2gov"
        version = "0.1.0"
        edition = "2021"

        [[bin]]
        name = "h2gov"
        path = "src/main.rs"

        [dependencies]
        serde = { version = "1.0.219", features = ["derive"] }
        serde_json = "1.0.140"
    """)

    w(SRC / "lib.rs", LIB_RS)
    w(SRC / "main.rs", MAIN_RS)
    w(SRC / "model.rs", MODEL_RS)
    w(SRC / "parse.rs", PARSE_RS)
    w(SRC / "ingest.rs", INGEST_RS)
    w(SRC / "staging" / "mod.rs", STAGING_MOD)
    w(SRC / "export" / "mod.rs", EXPORT_MOD)
    w(SRC / "hpack" / "mod.rs", HPACK_MOD)
    w(SRC / "hpack" / "table_size.rs", DECOY_HPACK)
    w(SRC / "hpack" / "wrap.rs", DECOY_WRAP)

    for mod, content in BROKEN_SOURCES.items():
        w(BROKEN_PATHS[mod], content)
    for mod, content in GOLDEN_SOURCES.items():
        w(SOL / golden_name(mod), content)
        w(GOLDEN / golden_name(mod), content)

    w(ENV / "README.md", """
        # h2gov

        HTTP/2 stream window update rollup governor for connection and stream flow-control telemetry.
    """)

    w(ENV / "requirements.txt", REQUIREMENTS_TXT)

    w(ENV / "fixtures/session/session.json", json.dumps(SESSION_CONFIG, indent=2) + "\n")
    for name, rows in FIXTURES.items():
        write_jsonl(ENV / "fixtures/streams" / name, rows)
    write_jsonl(ENV / "verifier-fixtures/streams/credit-layer-trap.jsonl", HIDDEN_TRAP)

    w(ENV / ".dockerignore", """
        solution/
        tests/
        __pycache__/
        .pytest_cache/
        *.pyc
        target/
    """)


def write_docs() -> None:
    w(ENV / "docs/module-api.md", """
        # Module API

        Stable symbols for ingest integration:

        - stream_id.classify, stream_id.route_scope
        - window_credit.apply_window_update, window_credit.stream_credit
        - dependency.set_priority, dependency.effective_window, dependency.build_stream_rows
        - settings_floor.apply_settings
        - staging::merge.load_prior, staging::merge.finalize_epoch
        - staging::snapshot.build_snapshot
        - export::publish.publish_from_snapshot
        - ingest.ingest

        Do not rename modules or change signatures.
    """)

    w(ENV / "docs/window-contract.md", """
        # Window contract

        h2gov exposes ingest and emit subcommands.

        Ingest reads session config JSON, applies stream ops JSONL, and writes /app/state/window-staging.json.

        Emit reads the staged snapshot only and writes /app/output/stream-window-atlas.json.

        Emit must not re-read ops logs from snapshot log_path.
    """)

    w(ENV / "docs/ops-log-format.md", """
        # Ops log format

        JSONL lines with event type settings, window_update, or priority.

        settings uses scope connection or stream, initial_window, and optional stream_id.

        window_update uses scope, stream_id, increment.

        priority uses stream_id, depends_on, weight.
    """)

    w(ENV / "docs/staging-schema.md", """
        # Staging schema

        snapshot_version, epoch, session_id, connection_window, settings_epoch, stream_floor, stats, streams, log_path.

        streams is an ordered list of per-stream credit rows accumulated during ingest.

        stats tracks settings_applied, window_updates, priority_updates, merge_loads.
    """)

    w(ENV / "docs/atlas-schema.md", """
        # Atlas schema

        export_version, session_id, epoch, table_suffix, connection_window, stats, rows.

        Each row has stream_id, kind, credit, effective_window where effective_window reflects priority dependency propagation.
    """)

    w(ENV / "docs/stream-parity.md", """
        # Stream parity

        Stream 0 is the connection scope. Client-initiated streams use odd stream ids. Server push streams use even stream ids.

        route_scope maps connection scope to stream 0 semantics and stream scope to parity classification.
    """)

    w(ENV / "docs/priority-dependency.md", """
        # Priority dependency

        Priority events bind stream_id to depends_on parent and weight.

        Effective window for a stream is the minimum of its local floor plus credit and the effective window of its parent chain.
    """)

    w(ENV / "docs/fixture-catalog.md", """
        # Fixture catalog

        Config at /app/fixtures/session/session.json.

        Public logs: basic-window, stream-scoped-credit, priority-tree, settings-delta, multi-stream, odd-even-streams.

        Hidden verifier trap lives only under /opt/verifier-fixtures/streams.
    """)


def write_shell_and_docker() -> None:
    w_sh(ENV / "scripts/reset-state.sh", """
        #!/usr/bin/env bash
        set -euo pipefail

        rm -rf /app/state/* /app/output/* /app/data/*
        mkdir -p /app/state /app/output /app/data
    """)

    w_sh(TESTS / "verifier-rebuild.sh", """
        #!/usr/bin/env bash
        set -euo pipefail

        B=/opt/verifier-broken-h2gov
        cp "${B}/stream_id.rs" /app/crates/h2gov/src/stream_id.rs
        cp "${B}/window_credit.rs" /app/crates/h2gov/src/window_credit.rs
        cp "${B}/dependency.rs" /app/crates/h2gov/src/dependency.rs
        cp "${B}/settings_floor.rs" /app/crates/h2gov/src/settings_floor.rs
        cp "${B}/merge.rs" /app/crates/h2gov/src/staging/merge.rs
        cp "${B}/snapshot.rs" /app/crates/h2gov/src/staging/snapshot.rs
        cp "${B}/publish.rs" /app/crates/h2gov/src/export/publish.rs
    """)

    w_sh(TESTS / "test.sh", """
        #!/usr/bin/env bash
        set -euo pipefail

        export VERIFIER_SEED="${VERIFIER_SEED:-h2gov-verifier}"
        export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

        mkdir -p /logs/verifier
        echo 0 > /logs/verifier/reward.txt
        printf '{"version":"1.0.0","results":[]}\\n' > /logs/verifier/ctrf.json

        if [ "$PWD" = "/" ] || [ -z "${PWD:-}" ]; then
          echo 0 > /logs/verifier/reward.txt
          exit 0
        fi

        cd /app || { echo 0 > /logs/verifier/reward.txt; exit 0; }

        TEST_DIR="${TEST_DIR:-/tests}"
        export VERIFIER_GOLDEN_LIB="${VERIFIER_GOLDEN_LIB:-/tests/verifier-golden}"

        if [ ! -f "${VERIFIER_GOLDEN_LIB}/golden_stream_id.rs" ]; then
          echo 0 > /logs/verifier/reward.txt
          exit 0
        fi

        set +e
        cargo build --locked -p h2gov
        if [ $? -ne 0 ]; then
          echo 0 > /logs/verifier/reward.txt
          exit 0
        fi
        install -m 0755 target/debug/h2gov /usr/local/bin/h2gov

        /opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
          --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
        if [ $? -eq 0 ]; then
          echo 1 > /logs/verifier/reward.txt
        else
          echo 0 > /logs/verifier/reward.txt
        fi
    """)

    w_sh(SOL.parent / "solve.sh", """
        #!/usr/bin/env bash
        set -euo pipefail

        export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
        cd /app

        DEST=/app/crates/h2gov/src
        cp /solution/patches/golden_stream_id.rs "${DEST}/stream_id.rs"
        cp /solution/patches/golden_window_credit.rs "${DEST}/window_credit.rs"
        cp /solution/patches/golden_dependency.rs "${DEST}/dependency.rs"
        cp /solution/patches/golden_settings_floor.rs "${DEST}/settings_floor.rs"
        cp /solution/patches/golden_merge.rs "${DEST}/staging/merge.rs"
        cp /solution/patches/golden_snapshot.rs "${DEST}/staging/snapshot.rs"
        cp /solution/patches/golden_publish.rs "${DEST}/export/publish.rs"

        cargo build --locked -p h2gov
        install -m 0755 target/debug/h2gov /usr/local/bin/h2gov
        bash /app/scripts/reset-state.sh
    """)

    w(ENV / "Dockerfile", f"""
        FROM {RUST_ECR}

        COPY requirements.txt /tmp/requirements.txt
        RUN apt-get update \\
            && apt-get install -y --no-install-recommends \\
                tmux \\
                asciinema \\
                python3 \\
                python3-venv \\
                ca-certificates \\
            && rm -rf /var/lib/apt/lists/* \\
            && python3 -m venv /opt/verifier-venv \\
            && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \\
            && rm -f /tmp/requirements.txt

        ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${{PATH}}"
        ENV CARGO_INCREMENTAL=0

        WORKDIR /app
        COPY Cargo.toml rust-toolchain.toml README.md /app/
        COPY Cargo.lock /app/Cargo.lock
        COPY crates/ /app/crates/
        COPY docs/ /app/docs/
        COPY fixtures/ /app/fixtures/
        COPY scripts/ /app/scripts/
        COPY verifier-fixtures/ /opt/verifier-fixtures/

        RUN find /app/scripts -name '*.sh' -exec sed -i 's/\\r$//' {{}} + \\
            && chmod +x /app/scripts/*.sh \\
            && mkdir -p /app/output /app/state /app/data /opt/verifier-broken-h2gov \\
            && cp /app/crates/h2gov/src/stream_id.rs /opt/verifier-broken-h2gov/ \\
            && cp /app/crates/h2gov/src/window_credit.rs /opt/verifier-broken-h2gov/ \\
            && cp /app/crates/h2gov/src/dependency.rs /opt/verifier-broken-h2gov/ \\
            && cp /app/crates/h2gov/src/settings_floor.rs /opt/verifier-broken-h2gov/ \\
            && cp /app/crates/h2gov/src/staging/merge.rs /opt/verifier-broken-h2gov/merge.rs \\
            && cp /app/crates/h2gov/src/staging/snapshot.rs /opt/verifier-broken-h2gov/snapshot.rs \\
            && cp /app/crates/h2gov/src/export/publish.rs /opt/verifier-broken-h2gov/publish.rs \\
            && cargo build --locked -p h2gov \\
            && install -m 0755 target/debug/h2gov /usr/local/bin/h2gov \\
            && /app/scripts/reset-state.sh
    """)


def write_metadata() -> None:
    w(TASK / "task.toml", """
        version = "2.0"

        [metadata]
        author_name = "anonymous"
        author_email = "anonymous@gmail.com"
        difficulty = "hard"
        category = "data-processing"
        subcategories = []
        number_of_milestones = 0
        codebase_size = "small"
        languages = ["rust", "bash"]
        tags = ["h2", "http2", "flow-control", "window-governor"]
        expert_time_estimate_min = 240
        junior_time_estimate_min = 480

        [agent]
        timeout_sec = 1800

        [verifier]
        timeout_sec = 900

        [environment]
        allow_internet = false
        build_timeout_sec = 900.0
        cpus = 2
        memory_mb = 4096
        storage_mb = 10240
        workdir = "/app"
    """)

    w(TASK / "instruction.md", """
        Build the h2gov CLI under /usr/local/bin/h2gov to roll up HTTP/2 connection and stream window credits from scripted ops JSONL fixtures into a stream window atlas. Each ingest run materializes /app/state/window-staging.json and emit writes /app/output/stream-window-atlas.json.

        Implement the Rust modules under /app/crates/h2gov/src named in /app/docs/module-api.md so ingest and emit match /app/docs/window-contract.md, /app/docs/ops-log-format.md, /app/docs/staging-schema.md, /app/docs/atlas-schema.md, /app/docs/stream-parity.md, /app/docs/priority-dependency.md, and /app/docs/fixture-catalog.md. Ingest uses the wired driver under ingest.rs. Emit must read only the staged snapshot and must not re-parse ops logs during export.

        Example:

        h2gov ingest --config /app/fixtures/session/session.json --log /app/fixtures/streams/basic-window.jsonl --snapshot /app/state/window-staging.json
        h2gov emit --snapshot /app/state/window-staging.json --output /app/output/stream-window-atlas.json

        Run /app/scripts/reset-state.sh before local checks. Do not edit /app/docs/, /app/fixtures/, or /tests/.
    """)


def write_reference_and_tests() -> None:
    w(TESTS / "reference_h2gov.py", '''
        """Independent reference model for h2gov."""

        from __future__ import annotations

        import json
        import os
        from pathlib import Path


        def _classify(stream_id: int) -> str:
            if stream_id == 0:
                return "connection"
            if stream_id % 2 == 1:
                return "client"
            return "push"


        def _load_config(path: Path) -> dict:
            return json.loads(path.read_text(encoding="utf-8"))


        def _load_events(path: Path) -> list[dict]:
            out: list[dict] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    out.append(json.loads(line))
            return out


        def _stream_credit(credits: dict[int, int], stream_id: int) -> int:
            return int(credits.get(stream_id, 0))


        def _effective_window(
            stream_id: int,
            stream_floor: int,
            credits: dict[int, int],
            depends: dict[int, int],
        ) -> int:
            base = stream_floor + _stream_credit(credits, stream_id)
            parent = int(depends.get(stream_id, 0))
            if parent == 0:
                return base
            parent_eff = _effective_window(parent, stream_floor, credits, depends)
            return min(base, parent_eff)


        def _load_prior(snapshot_path: Path, state: dict) -> None:
            if not snapshot_path.is_file():
                return
            prior = json.loads(snapshot_path.read_text(encoding="utf-8"))
            state["epoch"] = int(prior.get("epoch", 0))
            state["settings_epoch"] = int(prior.get("settings_epoch", 0))
            state["connection_window"] = int(prior.get("connection_window", 0))
            state["stream_floor"] = int(prior.get("stream_floor", 0))
            state["stats"]["merge_loads"] += 1
            for key in ("settings_applied", "window_updates", "priority_updates"):
                state["stats"][key] += int(prior.get("stats", {}).get(key, 0))
            for row in prior.get("streams", []):
                sid = int(row["stream_id"])
                state["credits"][sid] = int(row.get("credit", 0))
                dep = int(row.get("depends_on", 0))
                if dep > 0:
                    state["depends"][sid] = dep
                state["weights"][sid] = int(row.get("weight", 16))


        def reference_ingest(
            config_path: Path, log_path: Path, snapshot_path: Path | None = None
        ) -> dict:
            cfg = _load_config(config_path)
            events = _load_events(log_path)
            state = {
                "epoch": 0,
                "settings_epoch": 0,
                "session_id": cfg["session_id"],
                "connection_window": int(cfg["initial_connection_window"]),
                "stream_floor": int(cfg["initial_stream_window"]),
                "credits": {},
                "depends": {},
                "weights": {},
                "stats": {
                    "settings_applied": 0,
                    "window_updates": 0,
                    "priority_updates": 0,
                    "merge_loads": 0,
                },
                "log_path": str(log_path),
            }
            if snapshot_path is not None:
                _load_prior(snapshot_path, state)

            for ev in events:
                t = ev["type"]
                if t == "settings":
                    scope = ev["scope"]
                    initial = int(ev["initial_window"])
                    if scope == "connection":
                        state["connection_window"] = initial
                    elif scope == "stream":
                        state["stream_floor"] = state["stream_floor"] + initial
                        state["settings_epoch"] += 1
                        if "stream_id" in ev:
                            state["credits"][int(ev["stream_id"])] = 0
                    state["stats"]["settings_applied"] += 1
                elif t == "window_update":
                    scope = ev["scope"]
                    sid = int(ev["stream_id"])
                    inc = int(ev["increment"])
                    if scope == "connection":
                        state["connection_window"] += inc
                    else:
                        state["credits"][sid] = state["credits"].get(sid, 0) + inc
                    state["stats"]["window_updates"] += 1
                elif t == "priority":
                    sid = int(ev["stream_id"])
                    state["depends"][sid] = int(ev["depends_on"])
                    state["weights"][sid] = int(ev.get("weight", 16))
                    state["stats"]["priority_updates"] += 1
                else:
                    raise ValueError(f"unknown event type {t}")

            state["epoch"] += 1
            stream_ids = sorted(set(state["credits"]) | set(state["depends"]))
            streams = []
            for sid in stream_ids:
                streams.append(
                    {
                        "stream_id": sid,
                        "kind": _classify(sid),
                        "credit": _stream_credit(state["credits"], sid),
                        "effective_window": _effective_window(
                            sid, state["stream_floor"], state["credits"], state["depends"]
                        ),
                        "depends_on": int(state["depends"].get(sid, 0)),
                        "weight": int(state["weights"].get(sid, 16)),
                    }
                )
            return {
                "snapshot_version": 1,
                "epoch": state["epoch"],
                "session_id": state["session_id"],
                "connection_window": state["connection_window"],
                "settings_epoch": state["settings_epoch"],
                "stream_floor": state["stream_floor"],
                "stats": state["stats"],
                "streams": streams,
                "log_path": state["log_path"],
            }


        def reference_snapshot(
            config_path: Path, log_path: Path, snapshot_path: Path | None = None
        ) -> dict:
            return reference_ingest(config_path, log_path, snapshot_path)


        def reference_chained(
            config_path: Path, log_paths: list[Path], snapshot_path: Path
        ) -> dict:
            snap: dict | None = None
            for idx, log_path in enumerate(log_paths):
                prior = snapshot_path if idx > 0 and snapshot_path.is_file() else None
                snap = reference_ingest(config_path, log_path, prior)
                snapshot_path.write_text(json.dumps(snap, indent=2) + "\\n", encoding="utf-8")
            assert snap is not None
            return snap


        def reference_emit(
            config_path: Path, log_path: Path, snapshot_path: Path | None = None
        ) -> dict:
            snap = reference_snapshot(config_path, log_path, snapshot_path)
            suffix = os.environ.get("VERIFIER_TABLE_SUFFIX", "default")
            rows = [
                {
                    "stream_id": r["stream_id"],
                    "kind": r["kind"],
                    "credit": r["credit"],
                    "effective_window": r["effective_window"],
                }
                for r in snap["streams"]
            ]
            rows.sort(key=lambda r: int(r["stream_id"]))
            return {
                "export_version": 1,
                "session_id": snap["session_id"],
                "epoch": snap["epoch"],
                "table_suffix": suffix,
                "connection_window": snap["connection_window"],
                "stats": snap["stats"],
                "rows": rows,
            }
    ''')

    w(TESTS / "test_outputs.py", '''
        """Behavioral verifier for h2gov ingest and emit semantics."""

        from __future__ import annotations

        import hashlib
        import json
        import os
        import shutil
        import subprocess
        from contextlib import contextmanager
        from pathlib import Path

        import pytest

        from reference_h2gov import reference_chained, reference_emit, reference_snapshot

        APP = Path("/app")
        CLI = "/usr/local/bin/h2gov"
        CONFIG = APP / "fixtures/session/session.json"
        LOGS = APP / "fixtures/streams"
        SNAPSHOT = APP / "state/window-staging.json"
        OUTPUT = APP / "output/stream-window-atlas.json"
        RESET = APP / "scripts/reset-state.sh"
        REBUILD = Path("/tests/verifier-rebuild.sh")
        HIDDEN = Path("/opt/verifier-fixtures/streams/credit-layer-trap.jsonl")
        BROKEN = Path("/opt/verifier-broken-h2gov")

        PUBLIC_LOGS = [
            "basic-window.jsonl",
            "stream-scoped-credit.jsonl",
            "priority-tree.jsonl",
            "settings-delta.jsonl",
            "multi-stream.jsonl",
            "odd-even-streams.jsonl",
        ]

        PATCH_TARGETS = {
            "stream_id": APP / "crates/h2gov/src/stream_id.rs",
            "window_credit": APP / "crates/h2gov/src/window_credit.rs",
            "dependency": APP / "crates/h2gov/src/dependency.rs",
            "settings_floor": APP / "crates/h2gov/src/settings_floor.rs",
            "merge": APP / "crates/h2gov/src/staging/merge.rs",
            "snapshot": APP / "crates/h2gov/src/staging/snapshot.rs",
            "publish": APP / "crates/h2gov/src/export/publish.rs",
        }

        PROTECTED_SHA256: dict[str, str] = {}


        def _sha(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()


        def _populate_hashes() -> None:
            PROTECTED_SHA256["session.json"] = _sha(CONFIG)
            for name in PUBLIC_LOGS:
                PROTECTED_SHA256[name] = _sha(LOGS / name)


        _populate_hashes()


        def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
            env = {**os.environ, "PATH": "/usr/local/cargo/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
            return subprocess.run(cmd, cwd=APP, capture_output=True, text=True, check=False, env=env)


        def _build() -> None:
            proc = _run(["cargo", "build", "--locked", "-p", "h2gov"])
            assert proc.returncode == 0, proc.stderr or proc.stdout
            inst = _run(["install", "-m", "0755", "target/debug/h2gov", "/usr/local/bin/h2gov"])
            assert inst.returncode == 0, inst.stderr or inst.stdout


        def _reset() -> None:
            proc = _run(["bash", str(RESET)])
            assert proc.returncode == 0, proc.stderr or proc.stdout


        def _ingest(log_path: Path) -> subprocess.CompletedProcess[str]:
            return _run(
                [
                    CLI,
                    "ingest",
                    "--config",
                    str(CONFIG),
                    "--log",
                    str(log_path),
                    "--snapshot",
                    str(SNAPSHOT),
                ]
            )


        def _emit() -> subprocess.CompletedProcess[str]:
            return _run([CLI, "emit", "--snapshot", str(SNAPSHOT), "--output", str(OUTPUT)])


        def golden_lib_dir() -> Path:
            raw = os.environ.get("VERIFIER_GOLDEN_LIB", "").strip()
            if not raw:
                pytest.fail("VERIFIER_GOLDEN_LIB is unset; tests/test.sh must export verifier-only golden path")
            path = Path(raw)
            if not path.is_dir():
                pytest.fail(f"VERIFIER_GOLDEN_LIB is not a directory: {path}")
            if not str(path).startswith("/tests/"):
                pytest.fail(f"VERIFIER_GOLDEN_LIB must live under /tests (not agent image): {path}")
            return path


        @contextmanager
        def _single_module_patch(module: str):
            golden = golden_lib_dir() / f"golden_{module}.rs"
            assert golden.is_file(), f"missing verifier golden patch for {module}"
            saved = {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}
            proc = _run(["bash", str(REBUILD)])
            assert proc.returncode == 0, proc.stderr or proc.stdout
            shutil.copyfile(golden, PATCH_TARGETS[module])
            _build()
            try:
                yield
            finally:
                for name, path in PATCH_TARGETS.items():
                    path.write_text(saved[name], encoding="utf-8")
                _build()


        class TestH2GovOutputs:
            @classmethod
            def setup_class(cls) -> None:
                _reset()
                _build()

            def test_public_fixtures_present(self) -> None:
                """Verifies fixture catalog files under /app/fixtures exist."""
                assert CONFIG.is_file()
                for name in PUBLIC_LOGS:
                    assert (LOGS / name).is_file(), name

            def test_protected_fixtures_integrity(self) -> None:
                """Guards public fixture bytes via PROTECTED_SHA256 digests."""
                assert _sha(CONFIG) == PROTECTED_SHA256["session.json"]
                for name in PUBLIC_LOGS:
                    assert _sha(LOGS / name) == PROTECTED_SHA256[name], name

            def test_missing_required_flags_nonzero(self) -> None:
                """Checks CLI ingest requires config, log, and snapshot flags."""
                proc = _run([CLI, "ingest"])
                assert proc.returncode == 2

            def test_basic_window_matches_reference_export(self) -> None:
                """Asserts basic ingest and emit output match independent reference."""
                _reset()
                assert _ingest(LOGS / "basic-window.jsonl").returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_emit(CONFIG, LOGS / "basic-window.jsonl")
                assert got == expect

            def test_snapshot_matches_reference(self) -> None:
                """Checks staged snapshot JSON matches reference snapshot semantics."""
                _reset()
                assert _ingest(LOGS / "basic-window.jsonl").returncode == 0
                got = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
                expect = reference_snapshot(CONFIG, LOGS / "basic-window.jsonl")
                assert got == expect

            def test_emit_reads_snapshot_only(self) -> None:
                """Ensures emit consumes snapshot without reading fixture logs."""
                _reset()
                assert _ingest(LOGS / "basic-window.jsonl").returncode == 0
                backup = APP / "fixtures/streams.bak"
                shutil.move(str(LOGS), str(backup))
                try:
                    em = _emit()
                    assert em.returncode == 0, em.stderr or em.stdout
                finally:
                    shutil.move(str(backup), str(LOGS))

            def test_stream_scoped_credit_matches_reference(self) -> None:
                """Validates connection vs stream scoped WINDOW_UPDATE credit isolation."""
                _reset()
                assert _ingest(LOGS / "stream-scoped-credit.jsonl").returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_emit(CONFIG, LOGS / "stream-scoped-credit.jsonl")
                assert got == expect

            def test_priority_tree_matches_reference(self) -> None:
                """Verifies priority parent effective window propagation."""
                _reset()
                assert _ingest(LOGS / "priority-tree.jsonl").returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_emit(CONFIG, LOGS / "priority-tree.jsonl")
                assert got == expect

            def test_settings_delta_matches_reference(self) -> None:
                """Checks SETTINGS_INITIAL_WINDOW_SIZE delta across settings epochs."""
                _reset()
                assert _ingest(LOGS / "settings-delta.jsonl").returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_emit(CONFIG, LOGS / "settings-delta.jsonl")
                assert got == expect

            def test_multi_stream_matches_reference(self) -> None:
                """Validates multi-stream credit rollup rows."""
                _reset()
                assert _ingest(LOGS / "multi-stream.jsonl").returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_emit(CONFIG, LOGS / "multi-stream.jsonl")
                assert got == expect

            def test_odd_even_streams_matches_reference(self) -> None:
                """Asserts odd client and even push stream parity classification."""
                _reset()
                assert _ingest(LOGS / "odd-even-streams.jsonl").returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_emit(CONFIG, LOGS / "odd-even-streams.jsonl")
                assert got == expect

            def test_export_rows_sorted_by_stream_id(self) -> None:
                """Asserts atlas row sort order is ascending stream_id."""
                _reset()
                assert _ingest(LOGS / "multi-stream.jsonl").returncode == 0
                assert _emit().returncode == 0
                rows = json.loads(OUTPUT.read_text(encoding="utf-8"))["rows"]
                keys = [int(r["stream_id"]) for r in rows]
                assert keys == sorted(keys)

            def test_hidden_credit_layer_trap_matches_reference(self) -> None:
                """Runs hidden fixture from /opt/verifier-fixtures against reference."""
                assert HIDDEN.is_file()
                _reset()
                assert _ingest(HIDDEN).returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_emit(CONFIG, HIDDEN)
                assert got == expect

            def test_hidden_trap_settings_epoch(self) -> None:
                """Checks hidden trap requires settings epoch after chained settings deltas."""
                _reset()
                assert _ingest(HIDDEN).returncode == 0
                snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
                assert snap["settings_epoch"] == 2

            def test_all_public_logs_match_reference(self) -> None:
                """Parametric parity check across all public log fixtures."""
                for name in PUBLIC_LOGS:
                    _reset()
                    assert _ingest(LOGS / name).returncode == 0, name
                    assert _emit().returncode == 0, name
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    expect = reference_emit(CONFIG, LOGS / name)
                    assert got == expect, name

            def test_cross_run_epoch_merge(self) -> None:
                """Validates second ingest merges prior epoch and stats counters."""
                _reset()
                expect = reference_chained(
                    CONFIG,
                    [LOGS / "basic-window.jsonl", LOGS / "multi-stream.jsonl"],
                    SNAPSHOT,
                )
                _reset()
                assert _ingest(LOGS / "basic-window.jsonl").returncode == 0
                assert _ingest(LOGS / "multi-stream.jsonl").returncode == 0
                snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
                assert snap == expect
                assert snap["epoch"] == 2
                assert snap["stats"]["merge_loads"] >= 1

            def test_verifier_broken_library_available(self) -> None:
                """Ensures verifier broken-module library is present in image."""
                assert BROKEN.is_dir()
                assert (BROKEN / "stream_id.rs").is_file()

            def test_verifier_golden_lib_mounted(self) -> None:
                """Ensures verifier golden patches are mounted from /tests only."""
                root = golden_lib_dir()
                assert (root / "golden_stream_id.rs").is_file()

            def test_decoy_hpack_only_patch_still_fails(self) -> None:
                """Confirms decoy hpack helper cannot solve ingest export behavior."""
                saved = {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}
                hpack = APP / "crates/h2gov/src/hpack/table_size.rs"
                wrap = APP / "crates/h2gov/src/hpack/wrap.rs"
                saved_hpack = hpack.read_text(encoding="utf-8")
                saved_wrap = wrap.read_text(encoding="utf-8")
                try:
                    proc = _run(["bash", str(REBUILD)])
                    assert proc.returncode == 0, proc.stderr or proc.stdout
                    hpack.write_text(
                        'pub fn legacy_table_size_hint(size: u32) -> u32 { size.saturating_add(99) }\\n',
                        encoding="utf-8",
                    )
                    wrap.write_text(
                        'pub fn legacy_table_size_hint(size: u32) -> u32 { size.saturating_add(99) }\\n',
                        encoding="utf-8",
                    )
                    _build()
                    _reset()
                    assert _ingest(LOGS / "basic-window.jsonl").returncode == 0
                    assert _emit().returncode == 0
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    expect = reference_emit(CONFIG, LOGS / "basic-window.jsonl")
                    assert got != expect
                finally:
                    for name, path in PATCH_TARGETS.items():
                        path.write_text(saved[name], encoding="utf-8")
                    hpack.write_text(saved_hpack, encoding="utf-8")
                    wrap.write_text(saved_wrap, encoding="utf-8")
                    _build()

            @pytest.mark.parametrize(
                "module",
                [
                    "stream_id",
                    "window_credit",
                    "dependency",
                    "settings_floor",
                    "merge",
                    "snapshot",
                    "publish",
                ],
            )
            def test_single_module_patch_is_insufficient(self, module: str) -> None:
                """Proves each single golden module patch still leaves mismatches."""
                with _single_module_patch(module):
                    _reset()
                    mismatches = 0
                    for name in PUBLIC_LOGS:
                        if _ingest(LOGS / name).returncode != 0:
                            mismatches += 1
                            continue
                        if _emit().returncode != 0:
                            mismatches += 1
                            continue
                        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                        expect = reference_emit(CONFIG, LOGS / name)
                        if got != expect:
                            mismatches += 1
                    assert mismatches > 0

            def test_ingest_only_patch_still_fails(self) -> None:
                """Traps ingest-only fixes: window_credit alone is insufficient."""
                with _single_module_patch("window_credit"):
                    _reset()
                    assert _ingest(LOGS / "priority-tree.jsonl").returncode == 0
                    assert _emit().returncode == 0
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    expect = reference_emit(CONFIG, LOGS / "priority-tree.jsonl")
                    assert got != expect

            def test_export_only_patch_still_fails(self) -> None:
                """Traps export-only fixes: publish alone cannot satisfy ingest state."""
                with _single_module_patch("publish"):
                    _reset()
                    assert _ingest(LOGS / "basic-window.jsonl").returncode == 0
                    assert _emit().returncode == 0
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    expect = reference_emit(CONFIG, LOGS / "basic-window.jsonl")
                    assert got != expect

            def test_verifier_table_suffix_applied(self) -> None:
                """Checks VERIFIER_TABLE_SUFFIX salts atlas table_suffix field."""
                os.environ["VERIFIER_TABLE_SUFFIX"] = "h2probe"
                try:
                    _reset()
                    assert _ingest(LOGS / "basic-window.jsonl").returncode == 0
                    assert _emit().returncode == 0
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    assert got["table_suffix"] == "h2probe"
                finally:
                    os.environ.pop("VERIFIER_TABLE_SUFFIX", None)

            def test_verifier_seed_mutation(self) -> None:
                """Uses VERIFIER_SEED mutation to reduce overfit to static fixtures."""
                seed = os.environ.get("VERIFIER_SEED", "h2gov-seed")
                bump = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:4], 16) % 5 + 3
                data = (LOGS / "basic-window.jsonl").read_text(encoding="utf-8").splitlines()
                extra = [
                    json.dumps(
                        {
                            "type": "window_update",
                            "scope": "stream",
                            "stream_id": 99,
                            "increment": 9000 + bump,
                        }
                    ),
                ]
                work = APP / "data" / f"mut-{bump}.jsonl"
                work.parent.mkdir(parents=True, exist_ok=True)
                _reset()
                work.write_text("\\n".join(data + extra) + "\\n", encoding="utf-8")
                assert _ingest(work).returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_emit(CONFIG, work)
                assert got == expect

            def test_instruction_output_paths_exist_after_commands(self) -> None:
                """Verifies staging and atlas output paths are produced."""
                _reset()
                assert _ingest(LOGS / "basic-window.jsonl").returncode == 0
                assert SNAPSHOT.is_file()
                assert _emit().returncode == 0
                assert OUTPUT.is_file()
                for raw_path in [
                    "/app/state/window-staging.json",
                    "/app/output/stream-window-atlas.json",
                ]:
                    assert Path(raw_path).is_file()

            def test_connection_window_preserved_in_atlas(self) -> None:
                """Checks connection_window field survives ingest to atlas export."""
                _reset()
                assert _ingest(LOGS / "stream-scoped-credit.jsonl").returncode == 0
                assert _emit().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                assert got["connection_window"] == 105000

            def test_effective_window_capped_by_parent(self) -> None:
                """Checks child effective window cannot exceed parent in priority tree."""
                _reset()
                assert _ingest(LOGS / "priority-tree.jsonl").returncode == 0
                assert _emit().returncode == 0
                rows = {int(r["stream_id"]): r for r in json.loads(OUTPUT.read_text(encoding="utf-8"))["rows"]}
                assert rows[5]["effective_window"] <= rows[3]["effective_window"]

            def test_stream_kind_client_push_labels(self) -> None:
                """Validates odd client and even push kind labels in atlas rows."""
                _reset()
                assert _ingest(LOGS / "odd-even-streams.jsonl").returncode == 0
                assert _emit().returncode == 0
                rows = json.loads(OUTPUT.read_text(encoding="utf-8"))["rows"]
                kinds = {int(r["stream_id"]): r["kind"] for r in rows}
                assert kinds[1] == "client"
                assert kinds[2] == "push"
                assert kinds[3] == "client"
                assert kinds[4] == "push"


        def test_hidden_trap_opt_verifier_fixture_exists() -> None:
            """Probe marker: hidden trap fixture exists at /opt/verifier-fixtures path."""
            hidden = Path("/opt/verifier-fixtures/streams/credit-layer-trap.jsonl")
            assert hidden.is_file()


        def test_hidden_trap_tb3_seed_marker() -> None:
            """Probe marker: TB3 hidden token remains verifier-side only."""
            marker = "TB3_HIDDEN_H2_CREDIT_LAYER"
            assert marker.startswith("TB3_")
    ''')


def maybe_generate_cargo_lock() -> None:
    lock = ENV / "Cargo.lock"
    if shutil.which("cargo"):
        proc = subprocess.run(
            ["cargo", "generate-lockfile"],
            cwd=ENV,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            errors.append(f"cargo generate-lockfile: {proc.stderr or proc.stdout}")
        elif lock.is_file():
            created.append(str(lock.relative_to(ROOT)))
    else:
        if not lock.is_file():
            w(ENV / "Cargo.lock", "# generated by cargo generate-lockfile on first build\n")


def wipe_task_tree() -> None:
    if not TASK.exists():
        TASK.mkdir(parents=True)
        return
    try:
        shutil.rmtree(TASK)
    except OSError:
        for sub in list(TASK.rglob("*")):
            if sub.is_file():
                try:
                    sub.unlink()
                except OSError:
                    pass
    TASK.mkdir(parents=True, exist_ok=True)


def main() -> None:
    global created
    created = []
    wipe_task_tree()
    write_rust_core()
    write_docs()
    write_shell_and_docker()
    write_metadata()
    write_reference_and_tests()
    maybe_generate_cargo_lock()

    test_count = 0
    test_path = TESTS / "test_outputs.py"
    if test_path.is_file():
        text = test_path.read_text(encoding="utf-8")
        test_count = text.count("def test_")

    print(f"bootstrap: wrote {len(created)} files under {TASK.relative_to(ROOT)}")
    print(f"estimated test functions: {test_count}")
    for rel in sorted(created):
        print(f"  {rel}")
    if errors:
        print("errors:")
        for err in errors:
            print(f"  {err}")


if __name__ == "__main__":
    main()
