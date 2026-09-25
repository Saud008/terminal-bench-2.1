#!/usr/bin/env python3
"""Bootstrap tasks/pulsar-cursor-mark-delete-ledger/ (Rust cursorreplay CLI)."""
from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "pulsar-cursor-mark-delete-ledger"
ENV = TASK / "environment"
TESTS = TASK / "tests"
SOL = TASK / "solution" / "patches"
CRATE = ENV / "crates" / "cursorreplay"
SRC = CRATE / "src"
GOLDEN = TESTS / "verifier-golden"

MODULES = ("ledger_id", "mark_delete", "barrier", "merge", "staging", "publish")

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

CURSOR_CONFIG = {
    "topic": "persistent://public/default/orders",
    "subscription": "lag-reader",
    "initial_read": {"ledger_id": 1, "entry_id": 0},
    "initial_mark_delete": {"ledger_id": 1, "entry_id": 0},
    "initial_ceiling": {"ledger_id": 1, "entry_id": 256},
}

FIXTURES = {
    "basic-cursor.jsonl": [
        {"type": "ack", "ledger_id": 1, "entry_id": 5},
        {"type": "mark_delete", "ledger_id": 1, "entry_id": 5},
        {"type": "set_ceiling", "ledger_id": 1, "entry_id": 10},
        {"type": "set_read", "ledger_id": 1, "entry_id": 5},
    ],
    "ack-out-of-order.jsonl": [
        {"type": "ack", "ledger_id": 1, "entry_id": 200},
        {"type": "mark_delete", "ledger_id": 1, "entry_id": 200},
        {"type": "ack", "ledger_id": 1, "entry_id": 100},
        {"type": "mark_delete", "ledger_id": 1, "entry_id": 100},
        {"type": "set_ceiling", "ledger_id": 1, "entry_id": 250},
        {"type": "set_read", "ledger_id": 1, "entry_id": 100},
    ],
    "ledger-id-rollover.jsonl": [
        {"type": "ack", "ledger_id": 1, "entry_id": 999},
        {"type": "mark_delete", "ledger_id": 1, "entry_id": 999},
        {"type": "set_ceiling", "ledger_id": 2, "entry_id": 10},
        {"type": "set_read", "ledger_id": 1, "entry_id": 999},
    ],
    "barrier-triangle.jsonl": [
        {"type": "ack", "ledger_id": 1, "entry_id": 5},
        {"type": "mark_delete", "ledger_id": 1, "entry_id": 5},
        {"type": "set_ceiling", "ledger_id": 1, "entry_id": 20},
        {"type": "set_read", "ledger_id": 1, "entry_id": 5},
    ],
    "multi-ack.jsonl": [
        {"type": "ack", "ledger_id": 1, "entry_id": 1},
        {"type": "ack", "ledger_id": 1, "entry_id": 2},
        {"type": "mark_delete", "ledger_id": 1, "entry_id": 2},
        {"type": "set_ceiling", "ledger_id": 1, "entry_id": 12},
        {"type": "set_read", "ledger_id": 1, "entry_id": 2},
    ],
    "short-entry-compare.jsonl": [
        {"type": "ack", "ledger_id": 1, "entry_id": 1},
        {"type": "mark_delete", "ledger_id": 1, "entry_id": 1},
        {"type": "set_ceiling", "ledger_id": 1, "entry_id": 10},
        {"type": "set_read", "ledger_id": 1, "entry_id": 1},
    ],
}

HIDDEN_TRAP = [
    {"type": "ack", "ledger_id": 1, "entry_id": 300},
    {"type": "mark_delete", "ledger_id": 1, "entry_id": 300},
    {"type": "set_ceiling", "ledger_id": 1, "entry_id": 600},
    {"type": "set_read", "ledger_id": 1, "entry_id": 300},
    {"type": "ack", "ledger_id": 1, "entry_id": 40},
    {"type": "mark_delete", "ledger_id": 1, "entry_id": 40},
]

created: list[str] = []
errors: list[str] = []


def w(path: Path | str, content: str) -> None:
    p = Path(path)
    if not p.is_absolute():
        p = TASK / p
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    created.append(str(p.relative_to(ROOT)))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    created.append(str(path.relative_to(ROOT)))


def golden_name(module: str) -> str:
    return f"golden_{module}.rs"


# --- Rust sources ---

MODEL_RS = r'''use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct Position {
    pub ledger_id: u64,
    pub entry_id: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub topic: String,
    pub subscription: String,
    pub initial_read: Position,
    pub initial_mark_delete: Position,
    pub initial_ceiling: Position,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    #[serde(rename = "type")]
    pub kind: String,
    pub ledger_id: Option<u64>,
    pub entry_id: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarkRecord {
    pub ledger_id: u64,
    pub entry_id: u64,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Stats {
    pub acks: u64,
    pub mark_deletes: u64,
    pub read_advances: u64,
    pub ceiling_advances: u64,
    pub merge_loads: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot {
    pub snapshot_version: u32,
    pub epoch: u32,
    pub topic: String,
    pub subscription: String,
    pub read: Position,
    pub mark_delete: Position,
    pub ceiling: Position,
    pub ack_floor: u64,
    pub stats: Stats,
    pub marks: Vec<MarkRecord>,
    pub log_path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerRow {
    pub ledger_id: u64,
    pub entry_id: u64,
    pub lag_entries: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ledger {
    pub export_version: u32,
    pub topic: String,
    pub epoch: u32,
    pub table_suffix: String,
    pub stats: Stats,
    pub rows: Vec<LedgerRow>,
}

#[derive(Debug, Clone)]
pub struct MutableState {
    pub config: Config,
    pub epoch: u32,
    pub read: Position,
    pub mark_delete: Position,
    pub ceiling: Position,
    pub ack_floor: u64,
    pub marks: Vec<MarkRecord>,
    pub stats: Stats,
    pub log_path: String,
}
'''

PARSE_RS = r'''use std::fs;
use std::io::{BufRead, BufReader};
use std::path::Path;

use serde_json;

use crate::model::{Config, Event, Ledger, Snapshot};

pub fn load_config(path: &str) -> Result<Config, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn load_events(path: &str) -> Result<Vec<Event>, String> {
    let f = fs::File::open(path).map_err(|e| e.to_string())?;
    let reader = BufReader::new(f);
    let mut out = Vec::new();
    for line in reader.lines() {
        let line = line.map_err(|e| e.to_string())?;
        if line.trim().is_empty() {
            continue;
        }
        let ev: Event = serde_json::from_str(&line).map_err(|e| e.to_string())?;
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

pub fn write_ledger(path: &str, ledger: &Ledger) -> Result<(), String> {
    let b = serde_json::to_string_pretty(ledger).map_err(|e| e.to_string())?;
    fs::write(path, format!("{b}\n")).map_err(|e| e.to_string())
}

pub fn path_exists(path: &str) -> bool {
    Path::new(path).exists()
}
'''

GOLDEN_LEDGER_ID = r'''use crate::model::Position;

pub fn compare(a: &Position, b: &Position) -> i32 {
    if a.ledger_id < b.ledger_id {
        return -1;
    }
    if a.ledger_id > b.ledger_id {
        return 1;
    }
    if a.entry_id < b.entry_id {
        return -1;
    }
    if a.entry_id > b.entry_id {
        return 1;
    }
    0
}

pub fn less(a: &Position, b: &Position) -> bool {
    compare(a, b) < 0
}

pub fn less_eq(a: &Position, b: &Position) -> bool {
    compare(a, b) <= 0
}
'''

BROKEN_LEDGER_ID = r'''use crate::model::Position;

// Broken: lexical string ordering on ledger_id:entry_id text.
pub fn compare(a: &Position, b: &Position) -> i32 {
    let as_ = format!("{}:{}", a.ledger_id, a.entry_id);
    let bs = format!("{}:{}", b.ledger_id, b.entry_id);
    if as_ < bs {
        return -1;
    }
    if as_ > bs {
        return 1;
    }
    0
}

pub fn less(a: &Position, b: &Position) -> bool {
    compare(a, b) < 0
}

pub fn less_eq(a: &Position, b: &Position) -> bool {
    compare(a, b) <= 0
}
'''

GOLDEN_MARK_DELETE = r'''use crate::ledger_id;
use crate::model::{MarkRecord, MutableState, Position};

pub fn record_ack(state: &mut MutableState, ledger_id: u64, entry_id: u64) {
    state.marks.push(MarkRecord { ledger_id, entry_id });
    state.stats.acks += 1;
    if entry_id > 0 && (state.ack_floor == 0 || entry_id < state.ack_floor) {
        state.ack_floor = entry_id;
    }
}

pub fn apply_mark_delete(state: &mut MutableState, ledger_id: u64, entry_id: u64) {
    let pos = Position { ledger_id, entry_id };
    if ledger_id::less(&state.mark_delete, &pos) {
        state.mark_delete = pos;
    }
    state.stats.mark_deletes += 1;
}
'''

BROKEN_MARK_DELETE = r'''use crate::ledger_id;
use crate::model::{MarkRecord, MutableState, Position};

pub fn record_ack(state: &mut MutableState, ledger_id: u64, entry_id: u64) {
    state.marks.push(MarkRecord { ledger_id, entry_id });
    state.stats.acks += 1;
    if entry_id > 0 && (state.ack_floor == 0 || entry_id < state.ack_floor) {
        state.ack_floor = entry_id;
    }
}

// Broken: stores entry_id + 1 instead of inclusive mark-delete position.
pub fn apply_mark_delete(state: &mut MutableState, ledger_id: u64, entry_id: u64) {
    let pos = Position {
        ledger_id,
        entry_id: entry_id.saturating_add(1),
    };
    if ledger_id::less(&state.mark_delete, &pos) {
        state.mark_delete = pos;
    }
    state.stats.mark_deletes += 1;
}
'''

GOLDEN_BARRIER = r'''use crate::ledger_id;
use crate::model::{MutableState, Position};

pub fn set_read(state: &mut MutableState, ledger_id: u64, entry_id: u64) -> Result<(), String> {
    let target = Position { ledger_id, entry_id };
    if !ledger_id::less_eq(&state.read, &target) || !ledger_id::less_eq(&target, &state.mark_delete) {
        return Err("read cursor violates barrier triangle".into());
    }
    state.read = target;
    state.stats.read_advances += 1;
    Ok(())
}

pub fn set_ceiling(state: &mut MutableState, ledger_id: u64, entry_id: u64) -> Result<(), String> {
    let target = Position { ledger_id, entry_id };
    if !ledger_id::less_eq(&state.read, &target) || !ledger_id::less_eq(&state.mark_delete, &target) {
        return Err("ceiling cursor violates barrier triangle".into());
    }
    state.ceiling = target;
    state.stats.ceiling_advances += 1;
    Ok(())
}
'''

BROKEN_BARRIER = r'''use crate::model::{MutableState, Position};

// Broken: advances read/ceiling without barrier triangle checks.
pub fn set_read(state: &mut MutableState, ledger_id: u64, entry_id: u64) -> Result<(), String> {
    state.read = Position { ledger_id, entry_id };
    state.stats.read_advances += 1;
    Ok(())
}

pub fn set_ceiling(state: &mut MutableState, ledger_id: u64, entry_id: u64) -> Result<(), String> {
    state.ceiling = Position { ledger_id, entry_id };
    state.stats.ceiling_advances += 1;
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
    state.stats.merge_loads += 1;
    state.stats.acks += prior.stats.acks;
    state.stats.mark_deletes += prior.stats.mark_deletes;
    state.stats.read_advances += prior.stats.read_advances;
    state.stats.ceiling_advances += prior.stats.ceiling_advances;
    state.read = prior.read;
    state.mark_delete = prior.mark_delete;
    state.ceiling = prior.ceiling;
    if prior.ack_floor > 0 && (state.ack_floor == 0 || prior.ack_floor < state.ack_floor) {
        state.ack_floor = prior.ack_floor;
    }
    Ok(())
}

pub fn finalize_epoch(state: &mut MutableState) {
    state.epoch += 1;
}
'''

BROKEN_MERGE = r'''use crate::model::MutableState;

// Broken: ignores prior snapshot epoch and counters on replay reruns.
pub fn load_prior(_snapshot_path: &str, _state: &mut MutableState) -> Result<(), String> {
    Ok(())
}

pub fn finalize_epoch(state: &mut MutableState) {
    state.epoch = 1;
}
'''

GOLDEN_STAGING = r'''use crate::model::{MutableState, Snapshot};

pub fn build_snapshot(state: MutableState) -> Snapshot {
    Snapshot {
        snapshot_version: 1,
        epoch: state.epoch,
        topic: state.config.topic.clone(),
        subscription: state.config.subscription.clone(),
        read: state.read,
        mark_delete: state.mark_delete,
        ceiling: state.ceiling,
        ack_floor: state.ack_floor,
        stats: state.stats,
        marks: state.marks.clone(),
        log_path: Some(state.log_path),
    }
}
'''

BROKEN_STAGING = r'''use crate::model::{MutableState, Snapshot, Stats};

// Broken: drops mark rows and zeros stats before staging write.
pub fn build_snapshot(state: MutableState) -> Snapshot {
    Snapshot {
        snapshot_version: 1,
        epoch: state.epoch,
        topic: state.config.topic.clone(),
        subscription: state.config.subscription.clone(),
        read: state.read,
        mark_delete: state.mark_delete,
        ceiling: state.ceiling,
        ack_floor: state.ack_floor,
        stats: Stats::default(),
        marks: Vec::new(),
        log_path: Some(state.log_path),
    }
}
'''

GOLDEN_PUBLISH = r'''use std::env;

use crate::ledger_id;
use crate::model::{Ledger, LedgerRow, Snapshot};

fn table_suffix() -> String {
    env::var("VERIFIER_TABLE_SUFFIX").unwrap_or_else(|_| "default".into())
}

fn lag_entries(ceiling: crate::model::Position, mark: crate::model::Position) -> i64 {
    if ceiling.ledger_id == mark.ledger_id {
        return ceiling.entry_id as i64 - mark.entry_id as i64;
    }
    let span = 0x1_0000_0000_i64;
    (ceiling.ledger_id as i64 - mark.ledger_id as i64) * span
        + ceiling.entry_id as i64
        - mark.entry_id as i64
}

pub fn publish_from_snapshot(snap: &Snapshot) -> Ledger {
    let mut rows: Vec<LedgerRow> = snap
        .marks
        .iter()
        .map(|m| {
            let pos = crate::model::Position {
                ledger_id: m.ledger_id,
                entry_id: m.entry_id,
            };
            LedgerRow {
                ledger_id: m.ledger_id,
                entry_id: m.entry_id,
                lag_entries: lag_entries(snap.ceiling, pos),
            }
        })
        .collect();
    rows.sort_by(|a, b| {
        let pa = crate::model::Position {
            ledger_id: a.ledger_id,
            entry_id: a.entry_id,
        };
        let pb = crate::model::Position {
            ledger_id: b.ledger_id,
            entry_id: b.entry_id,
        };
        ledger_id::compare(&pa, &pb).cmp(&0)
    });
    Ledger {
        export_version: 1,
        topic: snap.topic.clone(),
        epoch: snap.epoch,
        table_suffix: table_suffix(),
        stats: snap.stats.clone(),
        rows,
    }
}
'''

BROKEN_PUBLISH = r'''use std::env;

use crate::ledger_id;
use crate::model::{Ledger, LedgerRow, MarkRecord, Snapshot};
use crate::parse;

fn table_suffix() -> String {
    env::var("VERIFIER_TABLE_SUFFIX").unwrap_or_else(|_| "default".into())
}

fn lag_entries(ceiling: crate::model::Position, mark: crate::model::Position) -> i64 {
    if ceiling.ledger_id == mark.ledger_id {
        return ceiling.entry_id as i64 - mark.entry_id as i64;
    }
    0
}

// Broken: re-parses ops JSONL during export instead of snapshot marks only.
pub fn publish_from_snapshot(snap: &Snapshot) -> Ledger {
    let mut marks = snap.marks.clone();
    if let Some(log_path) = snap.log_path.as_deref() {
        if let Ok(events) = parse::load_events(log_path) {
            marks.clear();
            for ev in events {
                if ev.kind == "ack" {
                    marks.push(MarkRecord {
                        ledger_id: ev.ledger_id.unwrap_or(0),
                        entry_id: ev.entry_id.unwrap_or(0),
                    });
                }
            }
        }
    }
    let mut rows: Vec<LedgerRow> = marks
        .iter()
        .map(|m| {
            let pos = crate::model::Position {
                ledger_id: m.ledger_id,
                entry_id: m.entry_id,
            };
            LedgerRow {
                ledger_id: m.ledger_id,
                entry_id: m.entry_id,
                lag_entries: lag_entries(snap.ceiling, pos),
            }
        })
        .collect();
    rows.sort_by(|a, b| {
        let pa = crate::model::Position {
            ledger_id: a.ledger_id,
            entry_id: a.entry_id,
        };
        let pb = crate::model::Position {
            ledger_id: b.ledger_id,
            entry_id: b.entry_id,
        };
        ledger_id::compare(&pa, &pb).cmp(&0)
    });
    Ledger {
        export_version: 1,
        topic: snap.topic.clone(),
        epoch: snap.epoch,
        table_suffix: table_suffix(),
        stats: snap.stats.clone(),
        rows,
    }
}
'''

DECOY_WRAP = r'''// Decoy helper — not on replay or publish hot path.

pub fn wrap_legacy_topic_alias(topic: &str) -> String {
    format!("legacy::{topic}")
}
'''

REPLAY_RS = r'''pub mod wrap;

use crate::barrier;
use crate::mark_delete;
use crate::merge;
use crate::model::{Config, Event, MutableState, Snapshot};
use crate::staging;

pub fn replay(
    cfg: Config,
    events: Vec<Event>,
    snapshot_path: &str,
    log_path: &str,
) -> Result<Snapshot, String> {
    let mut state = MutableState {
        config: cfg.clone(),
        epoch: 0,
        read: cfg.initial_read,
        mark_delete: cfg.initial_mark_delete,
        ceiling: cfg.initial_ceiling,
        ack_floor: 0,
        marks: Vec::new(),
        stats: Default::default(),
        log_path: log_path.to_string(),
    };
    merge::load_prior(snapshot_path, &mut state)?;

    for ev in events {
        match ev.kind.as_str() {
            "ack" => {
                let ledger_id = ev.ledger_id.ok_or("ack missing ledger_id")?;
                let entry_id = ev.entry_id.ok_or("ack missing entry_id")?;
                mark_delete::record_ack(&mut state, ledger_id, entry_id);
            }
            "mark_delete" => {
                let ledger_id = ev.ledger_id.ok_or("mark_delete missing ledger_id")?;
                let entry_id = ev.entry_id.ok_or("mark_delete missing entry_id")?;
                mark_delete::apply_mark_delete(&mut state, ledger_id, entry_id);
            }
            "set_read" => {
                let ledger_id = ev.ledger_id.ok_or("set_read missing ledger_id")?;
                let entry_id = ev.entry_id.ok_or("set_read missing entry_id")?;
                barrier::set_read(&mut state, ledger_id, entry_id)?;
            }
            "set_ceiling" => {
                let ledger_id = ev.ledger_id.ok_or("set_ceiling missing ledger_id")?;
                let entry_id = ev.entry_id.ok_or("set_ceiling missing entry_id")?;
                barrier::set_ceiling(&mut state, ledger_id, entry_id)?;
            }
            other => return Err(format!("unknown event type {other}")),
        }
    }
    merge::finalize_epoch(&mut state);
    Ok(staging::build_snapshot(state))
}
'''

LIB_RS = r'''pub mod barrier;
pub mod ledger_id;
pub mod mark_delete;
pub mod merge;
pub mod model;
pub mod parse;
pub mod publish;
pub mod replay;
pub mod staging;
'''

MAIN_RS = r'''use std::env;
use std::process;

use cursorreplay::parse;
use cursorreplay::publish;
use cursorreplay::replay;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("expected subcommand replay or publish");
        process::exit(2);
    }
    match args[1].as_str() {
        "replay" => run_replay(&args[2..]),
        "publish" => run_publish(&args[2..]),
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

fn run_replay(args: &[String]) {
    let config = flag(args, "--config").unwrap_or_else(|| usage("replay"));
    let log = flag(args, "--log").unwrap_or_else(|| usage("replay"));
    let snapshot = flag(args, "--snapshot").unwrap_or_else(|| usage("replay"));
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
    let snap = match replay::replay(cfg, events, &snapshot, &log) {
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

fn run_publish(args: &[String]) {
    let snapshot = flag(args, "--snapshot").unwrap_or_else(|| usage("publish"));
    let output = flag(args, "--output").unwrap_or_else(|| usage("publish"));
    let snap = match parse::load_snapshot(&snapshot) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("{e}");
            process::exit(1);
        }
    };
    let ledger = publish::publish_from_snapshot(&snap);
    if let Err(e) = parse::write_ledger(&output, &ledger) {
        eprintln!("{e}");
        process::exit(1);
    }
}

fn usage(cmd: &str) -> ! {
    eprintln!("{cmd} requires flags; see /app/docs/cursor-contract.md");
    process::exit(2);
}
'''

GOLDEN_SOURCES = {
    "ledger_id": GOLDEN_LEDGER_ID,
    "mark_delete": GOLDEN_MARK_DELETE,
    "barrier": GOLDEN_BARRIER,
    "merge": GOLDEN_MERGE,
    "staging": GOLDEN_STAGING,
    "publish": GOLDEN_PUBLISH,
}

BROKEN_SOURCES = {
    "ledger_id": BROKEN_LEDGER_ID,
    "mark_delete": BROKEN_MARK_DELETE,
    "barrier": BROKEN_BARRIER,
    "merge": BROKEN_MERGE,
    "staging": BROKEN_STAGING,
    "publish": BROKEN_PUBLISH,
}


def write_rust_core() -> None:
    for p in [SRC / "replay", SOL, GOLDEN]:
        p.mkdir(parents=True, exist_ok=True)

    w(ENV / "Cargo.toml", f"""
        [workspace]
        members = ["crates/cursorreplay"]
        resolver = "2"
    """)

    w(ENV / "rust-toolchain.toml", """
        [toolchain]
        channel = "1.85"
    """)

    w(CRATE / "Cargo.toml", """
        [package]
        name = "cursorreplay"
        version = "0.1.0"
        edition = "2021"

        [[bin]]
        name = "cursorreplay"
        path = "src/main.rs"

        [dependencies]
        serde = { version = "1.0.219", features = ["derive"] }
        serde_json = "1.0.140"
    """)

    w(SRC / "lib.rs", LIB_RS)
    w(SRC / "main.rs", MAIN_RS)
    w(SRC / "model.rs", MODEL_RS)
    w(SRC / "parse.rs", PARSE_RS)
    w(SRC / "replay.rs", REPLAY_RS)
    w(SRC / "replay" / "wrap.rs", DECOY_WRAP)

    for mod, content in BROKEN_SOURCES.items():
        w(SRC / f"{mod}.rs", content)
    for mod, content in GOLDEN_SOURCES.items():
        w(SOL / golden_name(mod), content)
        w(GOLDEN / golden_name(mod), content)

    w(ENV / "README.md", """
        # cursorreplay

        Simulated Apache Pulsar consumer cursor replay and mark-delete lag ledger export.
    """)

    w(ENV / "requirements.txt", REQUIREMENTS_TXT)

    w(ENV / "fixtures/cursor/config.json", json.dumps(CURSOR_CONFIG, indent=2) + "\n")
    for name, rows in FIXTURES.items():
        write_jsonl(ENV / "fixtures/logs" / name, rows)
    write_jsonl(ENV / "verifier-fixtures/logs/barrier-mark-trap.jsonl", HIDDEN_TRAP)


def write_docs() -> None:
    w(ENV / "docs/module-api.md", """
        # Module API

        Stable symbols for replay integration:

        - ledger_id.compare, ledger_id.less, ledger_id.less_eq
        - mark_delete.record_ack, mark_delete.apply_mark_delete
        - barrier.set_read, barrier.set_ceiling
        - merge.load_prior, merge.finalize_epoch
        - staging.build_snapshot
        - publish.publish_from_snapshot
        - replay.replay

        Do not rename modules or change signatures.
    """)

    w(ENV / "docs/cursor-contract.md", """
        # Cursor contract

        cursorreplay exposes replay and publish subcommands.

        Replay reads cursor config JSON, applies ops JSONL, and writes /app/state/cursor-staging.json.

        Publish reads the staged snapshot only and writes /app/output/mark-delete-ledger.json.

        Publish must not re-read ops logs from snapshot log_path.
    """)

    w(ENV / "docs/ops-log-format.md", """
        # Ops log format

        JSONL lines with fields type, ledger_id, entry_id.

        Event types: ack, mark_delete, set_read, set_ceiling.

        ack records a single acknowledged entry. mark_delete advances the inclusive delete cursor.

        set_read and set_ceiling move barrier cursors and must satisfy read <= mark_delete <= ceiling.
    """)

    w(ENV / "docs/staging-schema.md", """
        # Staging schema

        snapshot_version, epoch, topic, subscription, read, mark_delete, ceiling, ack_floor, stats, marks, log_path.

        marks is an ordered list of ack rows replay accumulated during ingest.

        stats tracks acks, mark_deletes, read_advances, ceiling_advances, merge_loads.
    """)

    w(ENV / "docs/ledger-schema.md", """
        # Ledger schema

        export_version, topic, epoch, table_suffix, stats, rows.

        Each row has ledger_id, entry_id, lag_entries where lag_entries is ceiling minus mark position using numeric ledger_id ordering.
    """)

    w(ENV / "docs/cursor-barrier.md", """
        # Cursor barrier

        Positions compare by ledger_id then entry_id as unsigned integers.

        Barrier triangle: read <= mark_delete <= ceiling must hold when set_read or set_ceiling runs.

        Violations return a non-zero replay exit status.
    """)

    w(ENV / "docs/fixture-catalog.md", """
        # Fixture catalog

        Config at /app/fixtures/cursor/config.json.

        Public logs: basic-cursor, ack-out-of-order, ledger-id-rollover, barrier-triangle, multi-ack, short-entry-compare.

        Hidden verifier trap lives only under /opt/verifier-fixtures.
    """)

    w(ENV / "docs/replay-order.md", """
        # Replay order

        Load prior snapshot when output path already exists, apply events in file order, bump epoch once at end.

        Chained replays merge epoch and stats from the prior snapshot before applying the next log.
    """)


def write_shell_and_docker() -> None:
    w(ENV / "scripts/reset-state.sh", """
        #!/usr/bin/env bash
        set -euo pipefail

        rm -rf /app/state/* /app/output/* /app/data/*
        mkdir -p /app/state /app/output /app/data
    """)

    w(TESTS / "verifier-rebuild.sh", """
        #!/usr/bin/env bash
        set -euo pipefail

        cd /app
        B=/opt/verifier-broken-cursorreplay
        cp "${B}/ledger_id.rs" /app/crates/cursorreplay/src/ledger_id.rs
        cp "${B}/mark_delete.rs" /app/crates/cursorreplay/src/mark_delete.rs
        cp "${B}/barrier.rs" /app/crates/cursorreplay/src/barrier.rs
        cp "${B}/merge.rs" /app/crates/cursorreplay/src/merge.rs
        cp "${B}/staging.rs" /app/crates/cursorreplay/src/staging.rs
        cp "${B}/publish.rs" /app/crates/cursorreplay/src/publish.rs
    """)

    w(TESTS / "test.sh", """
        #!/usr/bin/env bash
        set -euo pipefail

        export VERIFIER_SEED="${VERIFIER_SEED:-cursorreplay-verifier}"
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

        if [ ! -f "${VERIFIER_GOLDEN_LIB}/golden_ledger_id.rs" ]; then
          echo 0 > /logs/verifier/reward.txt
          exit 0
        fi

        set +e
        cargo build --locked -p cursorreplay
        if [ $? -ne 0 ]; then
          echo 0 > /logs/verifier/reward.txt
          exit 0
        fi

        /opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
          --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
        if [ $? -eq 0 ]; then
          echo 1 > /logs/verifier/reward.txt
        else
          echo 0 > /logs/verifier/reward.txt
        fi
    """)

    w(SOL.parent / "solve.sh", """
        #!/usr/bin/env bash
        set -euo pipefail

        export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
        cd /app

        DEST=/app/crates/cursorreplay/src
        cp /solution/patches/golden_ledger_id.rs "${DEST}/ledger_id.rs"
        cp /solution/patches/golden_mark_delete.rs "${DEST}/mark_delete.rs"
        cp /solution/patches/golden_barrier.rs "${DEST}/barrier.rs"
        cp /solution/patches/golden_merge.rs "${DEST}/merge.rs"
        cp /solution/patches/golden_staging.rs "${DEST}/staging.rs"
        cp /solution/patches/golden_publish.rs "${DEST}/publish.rs"

        cargo build --locked -p cursorreplay
        install -m 0755 target/debug/cursorreplay /usr/local/bin/cursorreplay
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
            && mkdir -p /app/output /app/state /app/data /opt/verifier-broken-cursorreplay \\
            && cp /app/crates/cursorreplay/src/ledger_id.rs /opt/verifier-broken-cursorreplay/ \\
            && cp /app/crates/cursorreplay/src/mark_delete.rs /opt/verifier-broken-cursorreplay/ \\
            && cp /app/crates/cursorreplay/src/barrier.rs /opt/verifier-broken-cursorreplay/ \\
            && cp /app/crates/cursorreplay/src/merge.rs /opt/verifier-broken-cursorreplay/ \\
            && cp /app/crates/cursorreplay/src/staging.rs /opt/verifier-broken-cursorreplay/ \\
            && cp /app/crates/cursorreplay/src/publish.rs /opt/verifier-broken-cursorreplay/ \\
            && cargo build --locked -p cursorreplay \\
            && install -m 0755 target/debug/cursorreplay /usr/local/bin/cursorreplay \\
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
        tags = ["pulsar", "cursor", "mark-delete", "ledger", "rust-cli", "replay"]
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
        Implement modules for the cursorreplay CLI under /usr/local/bin/cursorreplay, which simulates Apache Pulsar consumer cursor mark-delete lag over scripted ops JSONL fixtures. Each replay run materializes /app/state/cursor-staging.json and publish writes /app/output/mark-delete-ledger.json.

        Implement the Rust modules under /app/crates/cursorreplay/src named in /app/docs/module-api.md so replay and publish match /app/docs/cursor-contract.md, /app/docs/ops-log-format.md, /app/docs/staging-schema.md, /app/docs/ledger-schema.md, /app/docs/cursor-barrier.md, /app/docs/fixture-catalog.md, and /app/docs/replay-order.md. Replay uses the wired driver under replay.rs. Publish must read only the staged snapshot and must not re-parse ops logs during export.

        Example:

        cursorreplay replay --config /app/fixtures/cursor/config.json --log /app/fixtures/logs/basic-cursor.jsonl --snapshot /app/state/cursor-staging.json
        cursorreplay publish --snapshot /app/state/cursor-staging.json --output /app/output/mark-delete-ledger.json

        Run /app/scripts/reset-state.sh before local checks. Do not edit /app/docs/, /app/fixtures/, or /tests/.
    """)


def write_reference_and_tests() -> None:
    w(TESTS / "reference_cursorreplay.py", '''
        """Independent reference model for cursorreplay."""

        from __future__ import annotations

        import json
        import os
        from pathlib import Path


        def _pos(ledger_id: int, entry_id: int) -> dict:
            return {"ledger_id": ledger_id, "entry_id": entry_id}


        def _compare(a: dict, b: dict) -> int:
            if a["ledger_id"] < b["ledger_id"]:
                return -1
            if a["ledger_id"] > b["ledger_id"]:
                return 1
            if a["entry_id"] < b["entry_id"]:
                return -1
            if a["entry_id"] > b["entry_id"]:
                return 1
            return 0


        def _leq(a: dict, b: dict) -> bool:
            return _compare(a, b) <= 0


        def _load_config(path: Path) -> dict:
            return json.loads(path.read_text(encoding="utf-8"))


        def _load_events(path: Path) -> list[dict]:
            out: list[dict] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    out.append(json.loads(line))
            return out


        def _lag_entries(ceiling: dict, mark: dict) -> int:
            if ceiling["ledger_id"] == mark["ledger_id"]:
                return int(ceiling["entry_id"]) - int(mark["entry_id"])
            span = 0x100000000
            return (
                (int(ceiling["ledger_id"]) - int(mark["ledger_id"])) * span
                + int(ceiling["entry_id"])
                - int(mark["entry_id"])
            )


        def _load_prior(snapshot_path: Path, state: dict) -> None:
            if not snapshot_path.is_file():
                return
            prior = json.loads(snapshot_path.read_text(encoding="utf-8"))
            state["epoch"] = int(prior.get("epoch", 0))
            state["stats"]["merge_loads"] += 1
            for key in ("acks", "mark_deletes", "read_advances", "ceiling_advances"):
                state["stats"][key] += int(prior.get("stats", {}).get(key, 0))
            state["read"] = prior["read"]
            state["mark_delete"] = prior["mark_delete"]
            state["ceiling"] = prior["ceiling"]
            px = int(prior.get("ack_floor", 0))
            if px > 0 and (state["ack_floor"] == 0 or px < state["ack_floor"]):
                state["ack_floor"] = px


        def reference_replay(
            config_path: Path, log_path: Path, snapshot_path: Path | None = None
        ) -> dict:
            cfg = _load_config(config_path)
            events = _load_events(log_path)
            state = {
                "epoch": 0,
                "topic": cfg["topic"],
                "subscription": cfg["subscription"],
                "read": dict(cfg["initial_read"]),
                "mark_delete": dict(cfg["initial_mark_delete"]),
                "ceiling": dict(cfg["initial_ceiling"]),
                "ack_floor": 0,
                "marks": [],
                "stats": {
                    "acks": 0,
                    "mark_deletes": 0,
                    "read_advances": 0,
                    "ceiling_advances": 0,
                    "merge_loads": 0,
                },
                "log_path": str(log_path),
            }
            if snapshot_path is not None:
                _load_prior(snapshot_path, state)

            for ev in events:
                t = ev["type"]
                if t == "ack":
                    lid = int(ev["ledger_id"])
                    eid = int(ev["entry_id"])
                    state["marks"].append({"ledger_id": lid, "entry_id": eid})
                    state["stats"]["acks"] += 1
                    if eid > 0 and (state["ack_floor"] == 0 or eid < state["ack_floor"]):
                        state["ack_floor"] = eid
                elif t == "mark_delete":
                    lid = int(ev["ledger_id"])
                    eid = int(ev["entry_id"])
                    pos = _pos(lid, eid)
                    if _compare(state["mark_delete"], pos) < 0:
                        state["mark_delete"] = pos
                    state["stats"]["mark_deletes"] += 1
                elif t == "set_read":
                    target = _pos(int(ev["ledger_id"]), int(ev["entry_id"]))
                    if not _leq(state["read"], target) or not _leq(target, state["mark_delete"]):
                        raise ValueError("read cursor violates barrier triangle")
                    state["read"] = target
                    state["stats"]["read_advances"] += 1
                elif t == "set_ceiling":
                    target = _pos(int(ev["ledger_id"]), int(ev["entry_id"]))
                    if not _leq(state["read"], target) or not _leq(state["mark_delete"], target):
                        raise ValueError("ceiling cursor violates barrier triangle")
                    state["ceiling"] = target
                    state["stats"]["ceiling_advances"] += 1
                else:
                    raise ValueError(f"unknown event type {t}")

            state["epoch"] += 1
            return {
                "snapshot_version": 1,
                "epoch": state["epoch"],
                "topic": state["topic"],
                "subscription": state["subscription"],
                "read": state["read"],
                "mark_delete": state["mark_delete"],
                "ceiling": state["ceiling"],
                "ack_floor": state["ack_floor"],
                "stats": state["stats"],
                "marks": state["marks"],
                "log_path": state["log_path"],
            }


        def reference_snapshot(
            config_path: Path, log_path: Path, snapshot_path: Path | None = None
        ) -> dict:
            return reference_replay(config_path, log_path, snapshot_path)


        def reference_chained(
            config_path: Path, log_paths: list[Path], snapshot_path: Path
        ) -> dict:
            snap: dict | None = None
            for idx, log_path in enumerate(log_paths):
                prior = snapshot_path if idx > 0 and snapshot_path.is_file() else None
                snap = reference_replay(config_path, log_path, prior)
                snapshot_path.write_text(json.dumps(snap, indent=2) + "\\n", encoding="utf-8")
            assert snap is not None
            return snap


        def reference_publish(
            config_path: Path, log_path: Path, snapshot_path: Path | None = None
        ) -> dict:
            snap = reference_snapshot(config_path, log_path, snapshot_path)
            suffix = os.environ.get("VERIFIER_TABLE_SUFFIX", "default")
            rows = []
            for m in snap["marks"]:
                pos = _pos(int(m["ledger_id"]), int(m["entry_id"]))
                rows.append(
                    {
                        "ledger_id": m["ledger_id"],
                        "entry_id": m["entry_id"],
                        "lag_entries": _lag_entries(snap["ceiling"], pos),
                    }
                )
            rows.sort(key=lambda r: (int(r["ledger_id"]), int(r["entry_id"])))
            return {
                "export_version": 1,
                "topic": snap["topic"],
                "epoch": snap["epoch"],
                "table_suffix": suffix,
                "stats": snap["stats"],
                "rows": rows,
            }
    ''')

    # test_outputs.py — adapted from postgresql task
    w(TESTS / "test_outputs.py", '''
        """Behavioral verifier for cursorreplay replay and publish semantics."""

        from __future__ import annotations

        import hashlib
        import json
        import os
        import shutil
        import subprocess
        from contextlib import contextmanager
        from pathlib import Path

        import pytest

        from reference_cursorreplay import reference_chained, reference_publish, reference_snapshot

        APP = Path("/app")
        CLI = "/usr/local/bin/cursorreplay"
        CONFIG = APP / "fixtures/cursor/config.json"
        LOGS = APP / "fixtures/logs"
        SNAPSHOT = APP / "state/cursor-staging.json"
        OUTPUT = APP / "output/mark-delete-ledger.json"
        RESET = APP / "scripts/reset-state.sh"
        REBUILD = Path("/tests/verifier-rebuild.sh")
        HIDDEN = Path("/opt/verifier-fixtures/logs/barrier-mark-trap.jsonl")
        BROKEN = Path("/opt/verifier-broken-cursorreplay")

        PUBLIC_LOGS = [
            "basic-cursor.jsonl",
            "ack-out-of-order.jsonl",
            "ledger-id-rollover.jsonl",
            "barrier-triangle.jsonl",
            "multi-ack.jsonl",
            "short-entry-compare.jsonl",
        ]

        PATCH_TARGETS = {
            "ledger_id": APP / "crates/cursorreplay/src/ledger_id.rs",
            "mark_delete": APP / "crates/cursorreplay/src/mark_delete.rs",
            "barrier": APP / "crates/cursorreplay/src/barrier.rs",
            "merge": APP / "crates/cursorreplay/src/merge.rs",
            "staging": APP / "crates/cursorreplay/src/staging.rs",
            "publish": APP / "crates/cursorreplay/src/publish.rs",
        }

        PROTECTED_SHA256: dict[str, str] = {}


        def _sha(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()


        def _populate_hashes() -> None:
            PROTECTED_SHA256["config.json"] = _sha(CONFIG)
            for name in PUBLIC_LOGS:
                PROTECTED_SHA256[name] = _sha(LOGS / name)


        _populate_hashes()


        def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
            env = {**os.environ, "PATH": "/usr/local/cargo/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
            return subprocess.run(cmd, cwd=APP, capture_output=True, text=True, check=False, env=env)


        def _build() -> None:
            proc = _run(["cargo", "build", "--locked", "-p", "cursorreplay"])
            assert proc.returncode == 0, proc.stderr or proc.stdout


        def _reset() -> None:
            proc = _run(["bash", str(RESET)])
            assert proc.returncode == 0, proc.stderr or proc.stdout


        def _replay(log_path: Path) -> subprocess.CompletedProcess[str]:
            return _run(
                [
                    CLI,
                    "replay",
                    "--config",
                    str(CONFIG),
                    "--log",
                    str(log_path),
                    "--snapshot",
                    str(SNAPSHOT),
                ]
            )


        def _publish() -> subprocess.CompletedProcess[str]:
            return _run([CLI, "publish", "--snapshot", str(SNAPSHOT), "--output", str(OUTPUT)])


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


        class TestCursorReplayOutputs:
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
                assert _sha(CONFIG) == PROTECTED_SHA256["config.json"]
                for name in PUBLIC_LOGS:
                    assert _sha(LOGS / name) == PROTECTED_SHA256[name], name

            def test_missing_required_flags_nonzero(self) -> None:
                """Checks CLI replay requires config, log, and snapshot flags."""
                proc = _run([CLI, "replay"])
                assert proc.returncode == 2

            def test_basic_log_matches_reference_export(self) -> None:
                """Asserts basic replay and publish output match independent reference."""
                _reset()
                assert _replay(LOGS / "basic-cursor.jsonl").returncode == 0
                assert _publish().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_publish(CONFIG, LOGS / "basic-cursor.jsonl")
                assert got == expect

            def test_snapshot_matches_reference(self) -> None:
                """Checks staged snapshot JSON matches reference snapshot semantics."""
                _reset()
                assert _replay(LOGS / "basic-cursor.jsonl").returncode == 0
                got = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
                expect = reference_snapshot(CONFIG, LOGS / "basic-cursor.jsonl")
                assert got == expect

            def test_publish_reads_snapshot_only(self) -> None:
                """Ensures publish consumes snapshot without reading fixture logs."""
                _reset()
                assert _replay(LOGS / "basic-cursor.jsonl").returncode == 0
                backup = APP / "fixtures/logs.bak"
                shutil.move(str(LOGS), str(backup))
                try:
                    pb = _publish()
                    assert pb.returncode == 0, pb.stderr or pb.stdout
                finally:
                    shutil.move(str(backup), str(LOGS))

            def test_ack_out_of_order_matches_reference(self) -> None:
                """Validates ack floor when marks arrive out of order."""
                _reset()
                assert _replay(LOGS / "ack-out-of-order.jsonl").returncode == 0
                assert _publish().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_publish(CONFIG, LOGS / "ack-out-of-order.jsonl")
                assert got == expect

            def test_ledger_id_rollover_matches_reference(self) -> None:
                """Checks ledger_id rollover ordering against reference."""
                _reset()
                assert _replay(LOGS / "ledger-id-rollover.jsonl").returncode == 0
                assert _publish().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_publish(CONFIG, LOGS / "ledger-id-rollover.jsonl")
                assert got == expect

            def test_barrier_triangle_matches_reference(self) -> None:
                """Verifies read, mark_delete, and ceiling barrier triangle semantics."""
                _reset()
                assert _replay(LOGS / "barrier-triangle.jsonl").returncode == 0
                assert _publish().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_publish(CONFIG, LOGS / "barrier-triangle.jsonl")
                assert got == expect

            def test_short_entry_compare_matches_reference(self) -> None:
                """Asserts numeric position compare handles small entry ids."""
                _reset()
                assert _replay(LOGS / "short-entry-compare.jsonl").returncode == 0
                assert _publish().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_publish(CONFIG, LOGS / "short-entry-compare.jsonl")
                assert got == expect

            def test_multi_ack_matches_reference(self) -> None:
                """Validates multi-ack ledger rows and lag entries."""
                _reset()
                assert _replay(LOGS / "multi-ack.jsonl").returncode == 0
                assert _publish().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_publish(CONFIG, LOGS / "multi-ack.jsonl")
                assert got == expect

            def test_export_rows_sorted_by_position(self) -> None:
                """Asserts ledger row sort order is ledger_id then entry_id."""
                _reset()
                assert _replay(LOGS / "multi-ack.jsonl").returncode == 0
                assert _publish().returncode == 0
                rows = json.loads(OUTPUT.read_text(encoding="utf-8"))["rows"]
                keys = [(int(r["ledger_id"]), int(r["entry_id"])) for r in rows]
                assert keys == sorted(keys)

            def test_hidden_barrier_mark_trap_matches_reference(self) -> None:
                """Runs hidden fixture from /opt/verifier-fixtures against reference."""
                assert HIDDEN.is_file()
                _reset()
                assert _replay(HIDDEN).returncode == 0
                assert _publish().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_publish(CONFIG, HIDDEN)
                assert got == expect

            def test_hidden_trap_ack_floor(self) -> None:
                """Checks hidden trap requires ack floor after late low ack."""
                _reset()
                assert _replay(HIDDEN).returncode == 0
                snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
                assert snap["ack_floor"] == 40

            def test_all_public_logs_match_reference(self) -> None:
                """Parametric parity check across all public log fixtures."""
                for name in PUBLIC_LOGS:
                    _reset()
                    assert _replay(LOGS / name).returncode == 0, name
                    assert _publish().returncode == 0, name
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    expect = reference_publish(CONFIG, LOGS / name)
                    assert got == expect, name

            def test_cross_run_epoch_merge(self) -> None:
                """Validates second replay merges prior epoch and stats counters."""
                _reset()
                expect = reference_chained(
                    CONFIG,
                    [LOGS / "basic-cursor.jsonl", LOGS / "multi-ack.jsonl"],
                    SNAPSHOT,
                )
                _reset()
                assert _replay(LOGS / "basic-cursor.jsonl").returncode == 0
                assert _replay(LOGS / "multi-ack.jsonl").returncode == 0
                snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
                assert snap == expect
                assert snap["epoch"] == 2
                assert snap["stats"]["merge_loads"] >= 1

            def test_verifier_broken_library_available(self) -> None:
                """Ensures verifier broken-module library is present in image."""
                assert BROKEN.is_dir()
                assert (BROKEN / "ledger_id.rs").is_file()

            def test_verifier_golden_lib_mounted(self) -> None:
                """Ensures verifier golden patches are mounted from /tests only."""
                root = golden_lib_dir()
                assert (root / "golden_ledger_id.rs").is_file()

            def test_decoy_wrap_only_patch_still_fails(self) -> None:
                """Confirms decoy wrap helper cannot solve replay export behavior."""
                saved = {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}
                wrap = APP / "crates/cursorreplay/src/replay/wrap.rs"
                saved_wrap = wrap.read_text(encoding="utf-8")
                try:
                    proc = _run(["bash", str(REBUILD)])
                    assert proc.returncode == 0, proc.stderr or proc.stdout
                    wrap.write_text(
                        'pub fn wrap_legacy_topic_alias(topic: &str) -> String { format!("fixed:{topic}") }\\n',
                        encoding="utf-8",
                    )
                    _build()
                    _reset()
                    assert _replay(LOGS / "basic-cursor.jsonl").returncode == 0
                    assert _publish().returncode == 0
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    expect = reference_publish(CONFIG, LOGS / "basic-cursor.jsonl")
                    assert got != expect
                finally:
                    for name, path in PATCH_TARGETS.items():
                        path.write_text(saved[name], encoding="utf-8")
                    wrap.write_text(saved_wrap, encoding="utf-8")
                    _build()

            @pytest.mark.parametrize(
                "module", ["ledger_id", "mark_delete", "barrier", "merge", "staging", "publish"]
            )
            def test_single_module_patch_is_insufficient(self, module: str) -> None:
                """Proves each single golden module patch still leaves mismatches."""
                with _single_module_patch(module):
                    _reset()
                    mismatches = 0
                    for name in PUBLIC_LOGS:
                        if _replay(LOGS / name).returncode != 0:
                            mismatches += 1
                            continue
                        if _publish().returncode != 0:
                            mismatches += 1
                            continue
                        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                        expect = reference_publish(CONFIG, LOGS / name)
                        if got != expect:
                            mismatches += 1
                    assert mismatches > 0

            def test_ingest_only_patch_still_fails(self) -> None:
                """Traps ingest-only fixes: mark_delete alone is insufficient."""
                with _single_module_patch("mark_delete"):
                    _reset()
                    assert _replay(LOGS / "ack-out-of-order.jsonl").returncode == 0
                    assert _publish().returncode == 0
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    expect = reference_publish(CONFIG, LOGS / "ack-out-of-order.jsonl")
                    assert got != expect

            def test_export_only_patch_still_fails(self) -> None:
                """Traps export-only fixes: publish alone cannot satisfy replay state."""
                with _single_module_patch("publish"):
                    _reset()
                    assert _replay(LOGS / "basic-cursor.jsonl").returncode == 0
                    assert _publish().returncode == 0
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    expect = reference_publish(CONFIG, LOGS / "basic-cursor.jsonl")
                    assert got != expect

            def test_verifier_table_suffix_applied(self) -> None:
                """Checks VERIFIER_TABLE_SUFFIX salts ledger table_suffix field."""
                os.environ["VERIFIER_TABLE_SUFFIX"] = "cursorprobe"
                try:
                    _reset()
                    assert _replay(LOGS / "basic-cursor.jsonl").returncode == 0
                    assert _publish().returncode == 0
                    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                    assert got["table_suffix"] == "cursorprobe"
                finally:
                    os.environ.pop("VERIFIER_TABLE_SUFFIX", None)

            def test_verifier_seed_mutation(self) -> None:
                """Uses VERIFIER_SEED mutation to reduce overfit to static fixtures."""
                seed = os.environ.get("VERIFIER_SEED", "cursorreplay-seed")
                bump = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:4], 16) % 5 + 3
                data = (LOGS / "basic-cursor.jsonl").read_text(encoding="utf-8").splitlines()
                extra = [
                    json.dumps({"type": "ack", "ledger_id": 1, "entry_id": 9000 + bump}),
                    json.dumps(
                        {
                            "type": "mark_delete",
                            "ledger_id": 1,
                            "entry_id": 9000 + bump,
                        }
                    ),
                ]
                work = APP / "data" / f"mut-{bump}.jsonl"
                work.parent.mkdir(parents=True, exist_ok=True)
                _reset()
                work.write_text("\\n".join(data + extra) + "\\n", encoding="utf-8")
                assert _replay(work).returncode == 0
                assert _publish().returncode == 0
                got = json.loads(OUTPUT.read_text(encoding="utf-8"))
                expect = reference_publish(CONFIG, work)
                assert got == expect

            def test_instruction_output_paths_exist_after_commands(self) -> None:
                """Verifies staging and ledger output paths are produced."""
                _reset()
                assert _replay(LOGS / "basic-cursor.jsonl").returncode == 0
                assert SNAPSHOT.is_file()
                assert _publish().returncode == 0
                assert OUTPUT.is_file()
                for raw_path in ["/app/state/cursor-staging.json", "/app/output/mark-delete-ledger.json"]:
                    assert Path(raw_path).is_file()


        def test_hidden_trap_opt_verifier_fixture_exists() -> None:
            """Probe marker: hidden trap fixture exists at /opt/verifier-fixtures path."""
            hidden = Path("/opt/verifier-fixtures/logs/barrier-mark-trap.jsonl")
            assert hidden.is_file()


        def test_hidden_trap_tb3_seed_marker() -> None:
            """Probe marker: TB3 hidden token remains verifier-side only."""
            marker = "TB3_HIDDEN_CURSOR_BARRIER_MARK"
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
        # minimal lock placeholder — Docker build may regenerate
        if not lock.is_file():
            w(ENV / "Cargo.lock", "# generated by cargo generate-lockfile on first build\n")


def wipe_task_tree() -> None:
    if not TASK.exists():
        TASK.mkdir(parents=True)
        return
    try:
        shutil.rmtree(TASK)
    except OSError:
        # Windows may lock target/ under environment; overwrite in place instead.
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

    print(f"bootstrap: wrote {len(created)} files under {TASK.relative_to(ROOT)}")
    for rel in sorted(created):
        print(f"  {rel}")
    if errors:
        print("errors:")
        for err in errors:
            print(f"  {err}")


if __name__ == "__main__":
    main()
