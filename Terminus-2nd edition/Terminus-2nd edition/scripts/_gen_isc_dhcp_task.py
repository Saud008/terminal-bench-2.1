#!/usr/bin/env python3
"""Generate tasks/isc-dhcp-failover-bndupd-lease-atlas (one-shot CREATE helper)."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "isc-dhcp-failover-bndupd-lease-atlas"
SUR = ROOT / "tasks" / "suricata-eve-flow-alert-correlator-exporter"
ENV = TASK / "environment"
CRATE = ENV / "crates" / "bndupd" / "src"


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8")


def copy_lock() -> None:
    src = SUR / "environment" / "Cargo.lock"
    text = src.read_text(encoding="utf-8")
    text = text.replace("name = \"suricorrelate\"", "name = \"bndupd\"")
    text = text.replace("/suricorrelate", "/bndupd")
    w(ENV / "Cargo.lock", text)


# --- broken modules ---

BROKEN_BINDING_KEY = r'''use crate::model::Binding;

/// Broken: keeps raw chaddr case and uses ip-only identity.
pub fn binding_key(ip: &str, chaddr: &str) -> String {
    format!("{}|{}", ip, chaddr)
}

pub fn status_rank(status: &str) -> u8 {
    match status {
        "active" => 1,
        "backup" => 1,
        "expired" => 1,
        "abandoned" => 1,
        "free" => 1,
        _ => 0,
    }
}

pub fn should_supersede(existing: &Binding, incoming: &Binding) -> bool {
    // Broken: last-writer always wins.
    let _ = (existing, incoming);
    true
}
'''

GOLDEN_BINDING_KEY = r'''use crate::model::Binding;

/// Canonical key: dotted IP + lowercase hex chaddr without separators.
pub fn binding_key(ip: &str, chaddr: &str) -> String {
    let norm: String = chaddr
        .chars()
        .filter(|c| c.is_ascii_hexdigit())
        .map(|c| c.to_ascii_lowercase())
        .collect();
    format!("{ip}|{norm}")
}

pub fn status_rank(status: &str) -> u8 {
    match status {
        "active" => 5,
        "backup" => 4,
        "expired" => 3,
        "abandoned" => 2,
        "free" => 1,
        _ => 0,
    }
}

pub fn should_supersede(existing: &Binding, incoming: &Binding) -> bool {
    if incoming.tstp > existing.tstp {
        return true;
    }
    if incoming.tstp < existing.tstp {
        return false;
    }
    status_rank(&incoming.binding_status) > status_rank(&existing.binding_status)
}
'''

BROKEN_MCLT = r'''use crate::model::MutableState;

/// Broken: ignores MCLT holdover when partner is down.
pub fn mclt_blocks_free(state: &MutableState, _target_status: &str) -> bool {
    let _ = state;
    false
}

pub fn note_partner_down(state: &mut MutableState, at_clock: u64) {
    state.partner_up = false;
    state.partner_down_at = Some(at_clock);
}

pub fn note_partner_up(state: &mut MutableState) {
    state.partner_up = true;
    state.partner_down_at = None;
}
'''

GOLDEN_MCLT = r'''use crate::model::MutableState;

/// Partner-down free/backup→free transitions require MCLT holdover.
pub fn mclt_blocks_free(state: &MutableState, target_status: &str) -> bool {
    if target_status != "free" {
        return false;
    }
    if state.partner_up {
        return false;
    }
    let down_at = match state.partner_down_at {
        Some(v) => v,
        None => return true,
    };
    state.clock < down_at.saturating_add(state.config.mclt_seconds)
}

pub fn note_partner_down(state: &mut MutableState, at_clock: u64) {
    state.partner_up = false;
    state.partner_down_at = Some(at_clock);
}

pub fn note_partner_up(state: &mut MutableState) {
    state.partner_up = true;
    state.partner_down_at = None;
}
'''

BROKEN_ACK = r'''use crate::model::{Binding, MutableState, PendingUpd};

/// Broken: commits BNDUPD immediately without waiting for BNDACK.
pub fn stage_bndupd(state: &mut MutableState, pending: PendingUpd) {
    state.stats.bndupd += 1;
    // Auto-ack path (incorrect).
    let _ = commit_pending(state, pending);
}

pub fn apply_bndack(state: &mut MutableState, xid: u64) -> Result<(), String> {
    state.stats.bndack += 1;
    if let Some(idx) = state.pending.iter().position(|p| p.xid == xid) {
        let pending = state.pending.remove(idx);
        commit_pending(state, pending)?;
    }
    Ok(())
}

fn commit_pending(state: &mut MutableState, pending: PendingUpd) -> Result<(), String> {
    use crate::failover::{binding_key, mclt_holdover, splitbrain};

    let key = binding_key::binding_key(&pending.ip, &pending.chaddr);
    let incoming = Binding {
        binding_key: key.clone(),
        ip: pending.ip.clone(),
        chaddr: pending.chaddr.clone(),
        binding_status: pending.binding_status.clone(),
        tstp: pending.tstp,
        starts: pending.starts,
        ends: pending.ends,
        peer: pending.peer.clone(),
        xid: pending.xid,
    };

    if mclt_holdover::mclt_blocks_free(state, &incoming.binding_status) {
        state.stats.mclt_blocked += 1;
        state.pending.push(pending);
        return Ok(());
    }

    if let Some(existing) = state.bindings.iter().find(|b| b.binding_key == key).cloned() {
        if existing.binding_status == "active"
            && incoming.binding_status == "active"
            && binding_key::binding_key(&existing.ip, &existing.chaddr)
                != binding_key::binding_key(&incoming.ip, &incoming.chaddr)
        {
            // Broken: overwrite instead of quarantine.
            state.bindings.retain(|b| b.binding_key != key);
            state.bindings.push(incoming);
            state.stats.acked += 1;
            return Ok(());
        }
        if binding_key::should_supersede(&existing, &incoming) {
            state.bindings.retain(|b| b.binding_key != key);
            state.bindings.push(incoming);
        }
    } else {
        state.bindings.push(incoming);
    }
    state.stats.acked += 1;
    Ok(())
}
'''

GOLDEN_ACK = r'''use crate::model::{Binding, MutableState, PendingUpd};

/// BNDUPD stays pending until matching BNDACK xid arrives.
pub fn stage_bndupd(state: &mut MutableState, pending: PendingUpd) {
    state.stats.bndupd += 1;
    if let Some(idx) = state.pending.iter().position(|p| p.xid == pending.xid) {
        state.pending[idx] = pending;
    } else {
        state.pending.push(pending);
    }
}

pub fn apply_bndack(state: &mut MutableState, xid: u64) -> Result<(), String> {
    state.stats.bndack += 1;
    let idx = state
        .pending
        .iter()
        .position(|p| p.xid == xid)
        .ok_or_else(|| format!("bndack for unknown xid {xid}"))?;
    let pending = state.pending.remove(idx);
    commit_pending(state, pending)
}

fn commit_pending(state: &mut MutableState, pending: PendingUpd) -> Result<(), String> {
    use crate::failover::{binding_key, mclt_holdover, splitbrain};

    let key = binding_key::binding_key(&pending.ip, &pending.chaddr);
    let incoming = Binding {
        binding_key: key.clone(),
        ip: pending.ip.clone(),
        chaddr: pending.chaddr.clone(),
        binding_status: pending.binding_status.clone(),
        tstp: pending.tstp,
        starts: pending.starts,
        ends: pending.ends,
        peer: pending.peer.clone(),
        xid: pending.xid,
    };

    if mclt_holdover::mclt_blocks_free(state, &incoming.binding_status) {
        state.stats.mclt_blocked += 1;
        state.pending.push(pending);
        return Ok(());
    }

    if let Some(existing) = state.bindings.iter().find(|b| b.binding_key == key).cloned() {
        if splitbrain::is_split_brain(&existing, &incoming) {
            splitbrain::quarantine_pair(state, &existing, &incoming);
            return Ok(());
        }
        if binding_key::should_supersede(&existing, &incoming) {
            state.bindings.retain(|b| b.binding_key != key);
            state.bindings.push(incoming);
            state.stats.acked += 1;
        } else {
            state.stats.stale_ignored += 1;
        }
    } else {
        // Also detect active conflict across keys that share IP but different chaddr norm
        if incoming.binding_status == "active" {
            if let Some(other) = state
                .bindings
                .iter()
                .find(|b| b.ip == incoming.ip && b.binding_status == "active" && b.binding_key != key)
                .cloned()
            {
                splitbrain::quarantine_pair(state, &other, &incoming);
                return Ok(());
            }
        }
        state.bindings.push(incoming);
        state.stats.acked += 1;
    }
    Ok(())
}
'''

BROKEN_SPLIT = r'''use sha2::{Digest, Sha256};

use crate::model::{Binding, MutableState, QuarantineRow};

pub fn is_split_brain(_a: &Binding, _b: &Binding) -> bool {
    false
}

pub fn quarantine_pair(state: &mut MutableState, a: &Binding, b: &Binding) {
    // Broken: keep last writer, no quarantine row.
    state.bindings.retain(|x| x.binding_key != a.binding_key && x.binding_key != b.binding_key);
    state.bindings.push(b.clone());
    state.stats.acked += 1;
    let _ = (Sha256::digest(b""), QuarantineRow {
        binding_key: a.binding_key.clone(),
        witness_checksum: String::new(),
        peer_a: a.peer.clone(),
        peer_b: b.peer.clone(),
        chaddr_a: a.chaddr.clone(),
        chaddr_b: b.chaddr.clone(),
        tstp_a: a.tstp,
        tstp_b: b.tstp,
    });
}

pub fn witness_checksum(a: &Binding, b: &Binding) -> String {
    format!("{:x}", Sha256::digest(format!("{}{}", a.chaddr, b.chaddr).as_bytes()))
}
'''

GOLDEN_SPLIT = r'''use sha2::{Digest, Sha256};

use crate::failover::binding_key;
use crate::model::{Binding, MutableState, QuarantineRow};

pub fn is_split_brain(a: &Binding, b: &Binding) -> bool {
    if a.binding_status != "active" || b.binding_status != "active" {
        return false;
    }
    a.ip == b.ip
        && binding_key::binding_key(&a.ip, &a.chaddr)
            != binding_key::binding_key(&b.ip, &b.chaddr)
}

pub fn witness_checksum(a: &Binding, b: &Binding) -> String {
    let payload = format!(
        "{}|{}|{}|{}|{}|{}",
        a.binding_key, a.chaddr, a.tstp, b.binding_key, b.chaddr, b.tstp
    );
    format!("{:x}", Sha256::digest(payload.as_bytes()))
}

pub fn quarantine_pair(state: &mut MutableState, a: &Binding, b: &Binding) {
    let key = if a.binding_key == b.binding_key {
        a.binding_key.clone()
    } else {
        a.ip.clone()
    };
    state.bindings.retain(|x| x.binding_key != a.binding_key && x.binding_key != b.binding_key);
    let row = QuarantineRow {
        binding_key: key,
        witness_checksum: witness_checksum(a, b),
        peer_a: a.peer.clone(),
        peer_b: b.peer.clone(),
        chaddr_a: a.chaddr.clone(),
        chaddr_b: b.chaddr.clone(),
        tstp_a: a.tstp,
        tstp_b: b.tstp,
    };
    state.quarantine.retain(|q| q.binding_key != row.binding_key);
    state.quarantine.push(row);
    state.stats.quarantined += 1;
}
'''

BROKEN_STAGING = r'''use sha2::{Digest, Sha256};

use crate::model::{Binding, MutableState, QuarantineRow, Snapshot};

pub fn canonical_binding_line(b: &Binding) -> String {
    format!(
        "{}|{}|{}|{}|{}",
        b.ip, b.chaddr, b.binding_status, b.tstp, b.peer
    )
}

pub fn atlas_digest(bindings: &[Binding], quarantine: &[QuarantineRow]) -> String {
    // Broken: unsorted insertion order.
    let mut parts: Vec<String> = bindings.iter().map(canonical_binding_line).collect();
    for q in quarantine {
        parts.push(format!("Q|{}|{}", q.binding_key, q.witness_checksum));
    }
    format!("{:x}", Sha256::digest(parts.join("\n").as_bytes()))
}

pub fn build_snapshot(state: MutableState) -> Snapshot {
    let digest = atlas_digest(&state.bindings, &state.quarantine);
    Snapshot {
        snapshot_version: 1,
        peer_id: state.config.peer_id.clone(),
        partner_id: state.config.partner_id.clone(),
        pool_name: state.config.pool_name.clone(),
        clock: state.clock,
        partner_up: state.partner_up,
        partner_down_at: state.partner_down_at,
        atlas_digest: digest,
        bindings: state.bindings,
        pending: state.pending,
        quarantine: state.quarantine,
        stats: state.stats,
        log_path: state.log_path,
    }
}
'''

GOLDEN_STAGING = r'''use sha2::{Digest, Sha256};

use crate::failover::binding_key;
use crate::model::{Binding, MutableState, QuarantineRow, Snapshot};

pub fn canonical_binding_line(b: &Binding) -> String {
    let key = binding_key::binding_key(&b.ip, &b.chaddr);
    format!(
        "{}|{}|{}|{}|{}|{}|{}",
        key, b.ip, b.chaddr.to_ascii_lowercase(), b.binding_status, b.tstp, b.peer, b.xid
    )
}

pub fn atlas_digest(bindings: &[Binding], quarantine: &[QuarantineRow]) -> String {
    let mut parts: Vec<String> = bindings.iter().map(canonical_binding_line).collect();
    parts.sort();
    let mut qparts: Vec<String> = quarantine
        .iter()
        .map(|q| format!("Q|{}|{}", q.binding_key, q.witness_checksum))
        .collect();
    qparts.sort();
    parts.extend(qparts);
    format!("{:x}", Sha256::digest(parts.join("\n").as_bytes()))
}

pub fn build_snapshot(state: MutableState) -> Snapshot {
    let mut bindings = state.bindings;
    bindings.sort_by(|a, b| a.binding_key.cmp(&b.binding_key));
    let mut quarantine = state.quarantine;
    quarantine.sort_by(|a, b| a.binding_key.cmp(&b.binding_key));
    let digest = atlas_digest(&bindings, &quarantine);
    Snapshot {
        snapshot_version: 1,
        peer_id: state.config.peer_id.clone(),
        partner_id: state.config.partner_id.clone(),
        pool_name: state.config.pool_name.clone(),
        clock: state.clock,
        partner_up: state.partner_up,
        partner_down_at: state.partner_down_at,
        atlas_digest: digest,
        bindings,
        pending: state.pending,
        quarantine,
        stats: state.stats,
        log_path: state.log_path,
    }
}
'''

BROKEN_EXPORT = r'''use crate::model::{Atlas, Snapshot};

pub fn publish_from_snapshot(snap: &Snapshot) -> Result<Atlas, String> {
    let mut bindings = snap.bindings.clone();
    // Broken: sort by tstp descending, drop quarantine.
    bindings.sort_by(|a, b| b.tstp.cmp(&a.tstp));
    Ok(Atlas {
        export_version: 1,
        peer_id: snap.peer_id.clone(),
        partner_id: snap.partner_id.clone(),
        pool_name: snap.pool_name.clone(),
        clock: snap.clock,
        atlas_digest: snap.atlas_digest.clone(),
        table_suffix: "lease-atlas".to_string(),
        stats: snap.stats.clone(),
        bindings,
        quarantine: Vec::new(),
        pending_count: snap.pending.len() as u64,
    })
}
'''

GOLDEN_EXPORT = r'''use crate::model::{Atlas, Snapshot};
use crate::staging::snapshot as staging;

pub fn publish_from_snapshot(snap: &Snapshot) -> Result<Atlas, String> {
    let mut bindings = snap.bindings.clone();
    bindings.sort_by(|a, b| a.binding_key.cmp(&b.binding_key));
    let mut quarantine = snap.quarantine.clone();
    quarantine.sort_by(|a, b| a.binding_key.cmp(&b.binding_key));
    let digest = staging::atlas_digest(&bindings, &quarantine);
    if digest != snap.atlas_digest {
        return Err("staging atlas_digest drift".into());
    }
    Ok(Atlas {
        export_version: 1,
        peer_id: snap.peer_id.clone(),
        partner_id: snap.partner_id.clone(),
        pool_name: snap.pool_name.clone(),
        clock: snap.clock,
        atlas_digest: digest,
        table_suffix: "lease-atlas".to_string(),
        stats: snap.stats.clone(),
        bindings,
        quarantine,
        pending_count: snap.pending.len() as u64,
    })
}
'''

DECOY = r'''/// Decoy OMAPI wrap — not wired into replay or publish.
pub fn omapi_normalize_lease(ip: &str, chaddr: &str) -> String {
    format!("omapi:{}:{}", chaddr.to_uppercase(), ip)
}

pub fn legacy_lease_fold(rows: &[String]) -> Vec<String> {
    let mut out = rows.to_vec();
    out.sort();
    out
}
'''


def write_rust() -> None:
    w(ENV / "Cargo.toml", '[workspace]\nmembers = ["crates/bndupd"]\nresolver = "2"\n')
    w(
        ENV / "crates" / "bndupd" / "Cargo.toml",
        """[package]
name = "bndupd"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "bndupd"
path = "src/main.rs"

[dependencies]
serde = { version = "1.0.219", features = ["derive"] }
serde_json = "1.0.140"
sha2 = "0.10.8"
""",
    )
    w(ENV / "rust-toolchain.toml", '[toolchain]\nchannel = "1.85"\n')
    w(CRATE / "lib.rs", "pub mod failover;\npub mod model;\npub mod omapi_decoy;\npub mod parse;\npub mod replay;\npub mod staging;\npub mod export;\n")
    w(
        CRATE / "failover" / "mod.rs",
        "pub mod ack_gate;\npub mod binding_key;\npub mod mclt_holdover;\npub mod splitbrain;\n",
    )
    w(CRATE / "failover" / "binding_key.rs", BROKEN_BINDING_KEY)
    w(CRATE / "failover" / "mclt_holdover.rs", BROKEN_MCLT)
    w(CRATE / "failover" / "ack_gate.rs", BROKEN_ACK)
    w(CRATE / "failover" / "splitbrain.rs", BROKEN_SPLIT)
    w(CRATE / "staging" / "mod.rs", "pub mod snapshot;\n")
    w(CRATE / "staging" / "snapshot.rs", BROKEN_STAGING)
    w(CRATE / "export" / "mod.rs", "pub mod atlas;\n")
    w(CRATE / "export" / "atlas.rs", BROKEN_EXPORT)
    w(CRATE / "omapi_decoy" / "mod.rs", "pub mod wrap;\n")
    w(CRATE / "omapi_decoy" / "wrap.rs", DECOY)

    w(
        CRATE / "model.rs",
        r'''use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub peer_id: String,
    pub partner_id: String,
    pub mclt_seconds: u64,
    pub pool_name: String,
    pub initial_clock: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    #[serde(rename = "event_type")]
    pub kind: String,
    pub clock: Option<u64>,
    pub partner_up: Option<bool>,
    pub at_clock: Option<u64>,
    pub xid: Option<u64>,
    pub ip: Option<String>,
    pub chaddr: Option<String>,
    pub binding_status: Option<String>,
    pub tstp: Option<u64>,
    pub starts: Option<u64>,
    pub ends: Option<u64>,
    pub peer: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Binding {
    pub binding_key: String,
    pub ip: String,
    pub chaddr: String,
    pub binding_status: String,
    pub tstp: u64,
    pub starts: u64,
    pub ends: u64,
    pub peer: String,
    pub xid: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PendingUpd {
    pub xid: u64,
    pub ip: String,
    pub chaddr: String,
    pub binding_status: String,
    pub tstp: u64,
    pub starts: u64,
    pub ends: u64,
    pub peer: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct QuarantineRow {
    pub binding_key: String,
    pub witness_checksum: String,
    pub peer_a: String,
    pub peer_b: String,
    pub chaddr_a: String,
    pub chaddr_b: String,
    pub tstp_a: u64,
    pub tstp_b: u64,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
pub struct Stats {
    pub bndupd: u64,
    pub bndack: u64,
    pub acked: u64,
    pub mclt_blocked: u64,
    pub quarantined: u64,
    pub stale_ignored: u64,
    pub merge_loads: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Snapshot {
    pub snapshot_version: u32,
    pub peer_id: String,
    pub partner_id: String,
    pub pool_name: String,
    pub clock: u64,
    pub partner_up: bool,
    pub partner_down_at: Option<u64>,
    pub atlas_digest: String,
    pub bindings: Vec<Binding>,
    pub pending: Vec<PendingUpd>,
    pub quarantine: Vec<QuarantineRow>,
    pub stats: Stats,
    pub log_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Atlas {
    pub export_version: u32,
    pub peer_id: String,
    pub partner_id: String,
    pub pool_name: String,
    pub clock: u64,
    pub atlas_digest: String,
    pub table_suffix: String,
    pub stats: Stats,
    pub bindings: Vec<Binding>,
    pub quarantine: Vec<QuarantineRow>,
    pub pending_count: u64,
}

#[derive(Debug, Clone)]
pub struct MutableState {
    pub config: Config,
    pub clock: u64,
    pub partner_up: bool,
    pub partner_down_at: Option<u64>,
    pub bindings: Vec<Binding>,
    pub pending: Vec<PendingUpd>,
    pub quarantine: Vec<QuarantineRow>,
    pub stats: Stats,
    pub log_path: String,
}
''',
    )

    w(
        CRATE / "parse.rs",
        r'''use std::fs;
use std::path::Path;

use crate::model::{Atlas, Config, Event, Snapshot};

pub fn load_config(path: &str) -> Result<Config, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn load_events(path: &str) -> Result<Vec<Event>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in raw.lines() {
        let t = line.trim();
        if t.is_empty() {
            continue;
        }
        out.push(serde_json::from_str(t).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

pub fn write_json<T: serde::Serialize>(path: &str, value: &T) -> Result<(), String> {
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let raw = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    fs::write(path, raw + "\n").map_err(|e| e.to_string())
}

pub fn read_snapshot(path: &str) -> Result<Snapshot, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

pub fn write_atlas(path: &str, atlas: &Atlas) -> Result<(), String> {
    write_json(path, atlas)
}

pub fn path_exists(path: &str) -> bool {
    Path::new(path).is_file()
}
''',
    )

    w(
        CRATE / "replay.rs",
        r'''use crate::failover::{ack_gate, mclt_holdover};
use crate::model::{Config, Event, MutableState, PendingUpd, Snapshot};
use crate::parse;
use crate::staging::snapshot as staging;

pub fn replay(
    cfg: Config,
    events: Vec<Event>,
    snapshot_path: &str,
    log_path: &str,
    purge: bool,
) -> Result<Snapshot, String> {
    let mut state = MutableState {
        clock: cfg.initial_clock,
        partner_up: true,
        partner_down_at: None,
        bindings: Vec::new(),
        pending: Vec::new(),
        quarantine: Vec::new(),
        stats: Default::default(),
        log_path: log_path.to_string(),
        config: cfg,
    };

    if !purge && parse::path_exists(snapshot_path) {
        let prior = parse::read_snapshot(snapshot_path)?;
        state.clock = prior.clock;
        state.partner_up = prior.partner_up;
        state.partner_down_at = prior.partner_down_at;
        state.bindings = prior.bindings;
        state.pending = prior.pending;
        state.quarantine = prior.quarantine;
        state.stats = prior.stats;
        state.stats.merge_loads += 1;
    }

    for ev in events {
        match ev.kind.as_str() {
            "clock" => {
                state.clock = ev.clock.ok_or("clock missing clock")?;
            }
            "partner_state" => {
                let up = ev.partner_up.ok_or("partner_state missing partner_up")?;
                let at = ev.at_clock.unwrap_or(state.clock);
                if up {
                    mclt_holdover::note_partner_up(&mut state);
                } else {
                    mclt_holdover::note_partner_down(&mut state, at);
                }
                state.clock = state.clock.max(at);
            }
            "bndupd" => {
                let pending = PendingUpd {
                    xid: ev.xid.ok_or("bndupd missing xid")?,
                    ip: ev.ip.ok_or("bndupd missing ip")?.clone(),
                    chaddr: ev.chaddr.ok_or("bndupd missing chaddr")?.clone(),
                    binding_status: ev
                        .binding_status
                        .ok_or("bndupd missing binding_status")?
                        .clone(),
                    tstp: ev.tstp.ok_or("bndupd missing tstp")?,
                    starts: ev.starts.unwrap_or(0),
                    ends: ev.ends.unwrap_or(0),
                    peer: ev.peer.ok_or("bndupd missing peer")?.clone(),
                };
                ack_gate::stage_bndupd(&mut state, pending);
            }
            "bndack" => {
                let xid = ev.xid.ok_or("bndack missing xid")?;
                if let Some(at) = ev.at_clock {
                    state.clock = state.clock.max(at);
                }
                ack_gate::apply_bndack(&mut state, xid)?;
            }
            other => return Err(format!("unknown event type {other}")),
        }
    }

    Ok(staging::build_snapshot(state))
}
''',
    )

    w(
        CRATE / "main.rs",
        r'''use std::env;
use std::process;

use bndupd::export::atlas;
use bndupd::parse;
use bndupd::replay;

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

fn has_flag(args: &[String], name: &str) -> bool {
    args.iter().any(|a| a == name)
}

fn run_replay(args: &[String]) {
    let config = flag(args, "--config").unwrap_or_else(|| usage("replay"));
    let log = flag(args, "--log").unwrap_or_else(|| usage("replay"));
    let snapshot = flag(args, "--snapshot").unwrap_or_else(|| usage("replay"));
    let purge = has_flag(args, "--purge");
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
    let snap = match replay::replay(cfg, events, &snapshot, &log, purge) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("{e}");
            process::exit(1);
        }
    };
    if let Err(e) = parse::write_json(&snapshot, &snap) {
        eprintln!("{e}");
        process::exit(1);
    }
}

fn run_publish(args: &[String]) {
    let snapshot = flag(args, "--snapshot").unwrap_or_else(|| usage("publish"));
    let output = flag(args, "--output").unwrap_or_else(|| usage("publish"));
    let snap = match parse::read_snapshot(&snapshot) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("{e}");
            process::exit(1);
        }
    };
    let report = match atlas::publish_from_snapshot(&snap) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("{e}");
            process::exit(1);
        }
    };
    if let Err(e) = parse::write_atlas(&output, &report) {
        eprintln!("{e}");
        process::exit(1);
    }
}

fn usage(cmd: &str) -> ! {
    eprintln!("{cmd} requires flags; see /app/docs/cli.md");
    process::exit(2);
}
''',
    )


def write_docs() -> None:
    docs = ENV / "docs"
    w(
        docs / "module-api.md",
        """# Module API

Hot-path modules under /app/crates/bndupd/src:

- failover/binding_key.rs — canonical binding identity and supersede ordering
- failover/mclt_holdover.rs — partner-down MCLT free transition policy
- failover/ack_gate.rs — BNDUPD pending until BNDACK
- failover/splitbrain.rs — active conflict quarantine with witness checksum
- staging/snapshot.rs — staging snapshot builder and atlas_digest
- export/atlas.rs — publish atlas from staging only

Decoy (not on hot path): omapi_decoy/wrap.rs
""",
    )
    w(
        docs / "cli.md",
        """# CLI

bndupd replay --config PATH --log PATH --snapshot PATH [--purge]
bndupd publish --snapshot PATH --output PATH

Without --purge, replay loads an existing snapshot before applying the log.
Publish must read only the snapshot file.
""",
    )
    w(
        docs / "failover-contract.md",
        """# Failover contract

Binding identity is the pair of IPv4 address and chaddr. Chaddr is normalized to lowercase hexadecimal digits with separators removed before keying.

Supersede when the incoming tstp is greater. On equal tstp, higher binding_status rank wins: active, backup, expired, abandoned, free.

BNDUPD messages remain pending until a BNDACK with the same xid is observed. Only acked bindings enter the committed binding set used for atlas export.
""",
    )
    w(
        docs / "mclt-policy.md",
        """# MCLT policy

When partner_up is false, transitions whose target binding_status is free are blocked while clock is less than partner_down_at plus mclt_seconds from config.

Blocked commits stay pending and increment stats.mclt_blocked.
""",
    )
    w(
        docs / "staging-schema.md",
        """# Staging schema

/app/state/dhcp-staging.json fields: snapshot_version, peer_id, partner_id, pool_name, clock, partner_up, partner_down_at, atlas_digest, bindings, pending, quarantine, stats, log_path.

atlas_digest is SHA256 hex over sorted canonical binding lines plus sorted quarantine witness lines.
""",
    )
    w(
        docs / "atlas-schema.md",
        """# Atlas schema

/app/output/lease-atlas.json fields: export_version, peer_id, partner_id, pool_name, clock, atlas_digest, table_suffix, stats, bindings, quarantine, pending_count.

Bindings are sorted by binding_key ascending. Quarantine rows are included and sorted by binding_key. pending_count is the staging pending length.
""",
    )
    w(
        docs / "splitbrain-witness.md",
        """# Split-brain witness

Two active claims for the same IP with disagreeing normalized chaddr values are quarantined. Both bindings are removed from the committed set. A quarantine row stores peer_a, peer_b, chaddr_a, chaddr_b, tstp_a, tstp_b, and witness_checksum.

witness_checksum is SHA256 hex of binding_key_a|chaddr_a|tstp_a|binding_key_b|chaddr_b|tstp_b using each side binding_key field as stored on the Binding.
""",
    )
    w(
        docs / "fixture-catalog.md",
        """# Fixture catalog

Config: /app/fixtures/dhcp/peer.json

Public logs under /app/fixtures/logs/:
- basic-active-ack.jsonl
- chaddr-case-normalize.jsonl
- mclt-partner-down.jsonl
- splitbrain-active.jsonl
- supersede-tstp.jsonl
- pending-without-ack.jsonl
- multi-pool-peers.jsonl
""",
    )


def jl(events: list[dict]) -> str:
    return "\n".join(json.dumps(e, separators=(",", ":")) for e in events) + "\n"


def write_fixtures() -> None:
    cfg = {
        "peer_id": "primary",
        "partner_id": "secondary",
        "mclt_seconds": 3600,
        "pool_name": "pool-a",
        "initial_clock": 1_000_000,
    }
    w(ENV / "fixtures" / "dhcp" / "peer.json", json.dumps(cfg, indent=2) + "\n")

    fixtures = {
        "basic-active-ack.jsonl": [
            {"event_type": "bndupd", "xid": 1, "ip": "10.0.0.5", "chaddr": "aa:bb:cc:dd:ee:01", "binding_status": "active", "tstp": 1000100, "starts": 1000000, "ends": 1003600, "peer": "primary"},
            {"event_type": "bndack", "xid": 1, "peer": "secondary", "at_clock": 1000110},
        ],
        "chaddr-case-normalize.jsonl": [
            {"event_type": "bndupd", "xid": 2, "ip": "10.0.0.6", "chaddr": "AA-BB-CC-DD-EE-02", "binding_status": "active", "tstp": 1000200, "starts": 1000000, "ends": 1003600, "peer": "primary"},
            {"event_type": "bndack", "xid": 2, "at_clock": 1000210},
            {"event_type": "bndupd", "xid": 3, "ip": "10.0.0.6", "chaddr": "aa:bb:cc:dd:ee:02", "binding_status": "backup", "tstp": 1000200, "starts": 1000000, "ends": 1003600, "peer": "secondary"},
            {"event_type": "bndack", "xid": 3, "at_clock": 1000220},
        ],
        "mclt-partner-down.jsonl": [
            {"event_type": "bndupd", "xid": 10, "ip": "10.0.0.7", "chaddr": "aa:bb:cc:dd:ee:07", "binding_status": "active", "tstp": 1001000, "starts": 1000000, "ends": 1010000, "peer": "primary"},
            {"event_type": "bndack", "xid": 10, "at_clock": 1001010},
            {"event_type": "partner_state", "partner_up": False, "at_clock": 1002000},
            {"event_type": "bndupd", "xid": 11, "ip": "10.0.0.7", "chaddr": "aa:bb:cc:dd:ee:07", "binding_status": "free", "tstp": 1002100, "starts": 0, "ends": 0, "peer": "primary"},
            {"event_type": "bndack", "xid": 11, "at_clock": 1002110},
            {"event_type": "clock", "clock": 1005600},
            {"event_type": "bndupd", "xid": 12, "ip": "10.0.0.7", "chaddr": "aa:bb:cc:dd:ee:07", "binding_status": "free", "tstp": 1005700, "starts": 0, "ends": 0, "peer": "primary"},
            {"event_type": "bndack", "xid": 12, "at_clock": 1005710},
        ],
        "splitbrain-active.jsonl": [
            {"event_type": "bndupd", "xid": 20, "ip": "10.0.0.8", "chaddr": "aa:bb:cc:dd:ee:08", "binding_status": "active", "tstp": 1003000, "starts": 1000000, "ends": 1009000, "peer": "primary"},
            {"event_type": "bndack", "xid": 20, "at_clock": 1003010},
            {"event_type": "bndupd", "xid": 21, "ip": "10.0.0.8", "chaddr": "11:22:33:44:55:66", "binding_status": "active", "tstp": 1003100, "starts": 1000000, "ends": 1009000, "peer": "secondary"},
            {"event_type": "bndack", "xid": 21, "at_clock": 1003110},
        ],
        "supersede-tstp.jsonl": [
            {"event_type": "bndupd", "xid": 30, "ip": "10.0.0.9", "chaddr": "aa:bb:cc:dd:ee:09", "binding_status": "active", "tstp": 1004000, "starts": 1000000, "ends": 1008000, "peer": "primary"},
            {"event_type": "bndack", "xid": 30, "at_clock": 1004010},
            {"event_type": "bndupd", "xid": 31, "ip": "10.0.0.9", "chaddr": "aa:bb:cc:dd:ee:09", "binding_status": "expired", "tstp": 1004500, "starts": 1000000, "ends": 1004500, "peer": "primary"},
            {"event_type": "bndack", "xid": 31, "at_clock": 1004510},
        ],
        "pending-without-ack.jsonl": [
            {"event_type": "bndupd", "xid": 40, "ip": "10.0.0.10", "chaddr": "aa:bb:cc:dd:ee:0a", "binding_status": "active", "tstp": 1005000, "starts": 1000000, "ends": 1009000, "peer": "primary"},
            {"event_type": "bndupd", "xid": 41, "ip": "10.0.0.11", "chaddr": "aa:bb:cc:dd:ee:0b", "binding_status": "active", "tstp": 1005100, "starts": 1000000, "ends": 1009000, "peer": "primary"},
            {"event_type": "bndack", "xid": 41, "at_clock": 1005110},
        ],
        "multi-pool-peers.jsonl": [
            {"event_type": "bndupd", "xid": 50, "ip": "10.1.0.1", "chaddr": "de:ad:be:ef:00:01", "binding_status": "active", "tstp": 1006000, "starts": 1000000, "ends": 1010000, "peer": "primary"},
            {"event_type": "bndack", "xid": 50, "at_clock": 1006010},
            {"event_type": "bndupd", "xid": 51, "ip": "10.1.0.2", "chaddr": "de:ad:be:ef:00:02", "binding_status": "backup", "tstp": 1006100, "starts": 1000000, "ends": 1010000, "peer": "secondary"},
            {"event_type": "bndack", "xid": 51, "at_clock": 1006110},
            {"event_type": "bndupd", "xid": 52, "ip": "10.1.0.1", "chaddr": "de:ad:be:ef:00:01", "binding_status": "active", "tstp": 1005900, "starts": 1000000, "ends": 1010000, "peer": "secondary"},
            {"event_type": "bndack", "xid": 52, "at_clock": 1006120},
        ],
    }
    for name, events in fixtures.items():
        w(ENV / "fixtures" / "logs" / name, jl(events))

    # Hidden traps — independent failure modes
    w(
        ENV / "verifier-fixtures" / "logs" / "TB3_mclt_boundary.jsonl",
        jl(
            [
                {"event_type": "bndupd", "xid": 70, "ip": "10.9.9.1", "chaddr": "01:02:03:04:05:70", "binding_status": "active", "tstp": 2000000, "starts": 1990000, "ends": 2990000, "peer": "primary"},
                {"event_type": "bndack", "xid": 70, "at_clock": 2000010},
                {"event_type": "partner_state", "partner_up": False, "at_clock": 2001000},
                {"event_type": "clock", "clock": 2004599},
                {"event_type": "bndupd", "xid": 71, "ip": "10.9.9.1", "chaddr": "01:02:03:04:05:70", "binding_status": "free", "tstp": 2004600, "starts": 0, "ends": 0, "peer": "primary"},
                {"event_type": "bndack", "xid": 71, "at_clock": 2004599},
                {"event_type": "clock", "clock": 2004600},
                {"event_type": "bndupd", "xid": 72, "ip": "10.9.9.1", "chaddr": "01:02:03:04:05:70", "binding_status": "free", "tstp": 2004700, "starts": 0, "ends": 0, "peer": "primary"},
                {"event_type": "bndack", "xid": 72, "at_clock": 2004600},
            ]
        ),
    )
    w(
        ENV / "verifier-fixtures" / "logs" / "TB3_ack_skew_split.jsonl",
        jl(
            [
                {"event_type": "bndupd", "xid": 80, "ip": "10.9.9.2", "chaddr": "aa:aa:aa:aa:aa:80", "binding_status": "active", "tstp": 2100000, "starts": 2090000, "ends": 2190000, "peer": "primary"},
                {"event_type": "bndupd", "xid": 81, "ip": "10.9.9.2", "chaddr": "bb:bb:bb:bb:bb:81", "binding_status": "active", "tstp": 2100100, "starts": 2090000, "ends": 2190000, "peer": "secondary"},
                {"event_type": "bndack", "xid": 80, "at_clock": 2100200},
                {"event_type": "bndack", "xid": 81, "at_clock": 2100300},
            ]
        ),
    )


def write_meta() -> None:
    w(
        TASK / "instruction.md",
        """Build the bndupd CLI for ISC DHCP failover BNDUPD peer binding analysis. The tool replays failover message fixtures into a staging snapshot, then publishes a lease atlas for broadband provisioning review.

Binding identity, chaddr normalization, and supersede ordering are defined in /app/docs/failover-contract.md. Partner-down free transitions follow /app/docs/mclt-policy.md. Active split-brain quarantine and witness checksums are defined in /app/docs/splitbrain-witness.md.

Each replay run materializes /app/state/dhcp-staging.json
Publish writes /app/output/lease-atlas.json

Implement the Rust modules under /app/crates/bndupd/src named in /app/docs/module-api.md so replay and publish match /app/docs/failover-contract.md, /app/docs/mclt-policy.md, /app/docs/staging-schema.md, /app/docs/atlas-schema.md, /app/docs/splitbrain-witness.md, /app/docs/cli.md, and /app/docs/fixture-catalog.md. Replay uses the wired driver under replay.rs. Publish must read only the staged snapshot and must not re-parse failover logs during export.

Example:

bndupd replay --config /app/fixtures/dhcp/peer.json --log /app/fixtures/logs/basic-active-ack.jsonl --snapshot /app/state/dhcp-staging.json
bndupd publish --snapshot /app/state/dhcp-staging.json --output /app/output/lease-atlas.json

Without --purge, a second replay loads the existing snapshot before applying the next log.

Run /app/scripts/reset-state.sh before local checks. Do not edit /app/docs/, /app/fixtures/, or /tests/.
""",
    )
    w(
        TASK / "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "build-and-dependency-management"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["rust", "bash"]
tags = ["isc-dhcp", "failover", "bndupd", "mclt", "lease-atlas", "rust-cli", "staging"]
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
""",
    )
    w(ENV / "README.md", "bndupd — ISC DHCP failover BNDUPD lease atlas CLI\n")
    w(ENV / ".dockerignore", "solution/\ntests/\n__pycache__/\n.pytest_cache/\n*.pyc\ntarget/\n")
    shutil.copyfile(SUR / "environment" / "requirements.txt", ENV / "requirements.txt")
    w(
        ENV / "scripts" / "reset-state.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\nrm -rf /app/state/* /app/output/* /app/data/*\nmkdir -p /app/state /app/output /app/data\n",
    )
    w(
        ENV / "scripts" / "verifier-rebuild.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\ncd /app\nbash /tests/verifier-rebuild.sh\n",
    )
    w(
        ENV / "Dockerfile",
        """FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

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

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app
COPY Cargo.toml rust-toolchain.toml README.md /app/
COPY Cargo.lock /app/Cargo.lock
COPY crates/ /app/crates/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY verifier-fixtures/ /opt/verifier-fixtures/

RUN find /app/scripts -name '*.sh' -exec sed -i 's/\\r$//' {} + \\
    && chmod +x /app/scripts/*.sh \\
    && mkdir -p /app/output /app/state /app/data /opt/verifier-broken-bndupd \\
    && cp /app/crates/bndupd/src/failover/binding_key.rs /opt/verifier-broken-bndupd/binding_key.rs \\
    && cp /app/crates/bndupd/src/failover/mclt_holdover.rs /opt/verifier-broken-bndupd/mclt_holdover.rs \\
    && cp /app/crates/bndupd/src/failover/ack_gate.rs /opt/verifier-broken-bndupd/ack_gate.rs \\
    && cp /app/crates/bndupd/src/failover/splitbrain.rs /opt/verifier-broken-bndupd/splitbrain.rs \\
    && cp /app/crates/bndupd/src/staging/snapshot.rs /opt/verifier-broken-bndupd/snapshot.rs \\
    && cp /app/crates/bndupd/src/export/atlas.rs /opt/verifier-broken-bndupd/atlas.rs \\
    && cargo build --locked -p bndupd \\
    && install -m 0755 target/debug/bndupd /usr/local/bin/bndupd \\
    && /app/scripts/reset-state.sh
""",
    )


def write_solution() -> None:
    patches = TASK / "solution" / "patches"
    w(patches / "golden_binding_key.rs", GOLDEN_BINDING_KEY)
    w(patches / "golden_mclt_holdover.rs", GOLDEN_MCLT)
    w(patches / "golden_ack_gate.rs", GOLDEN_ACK)
    w(patches / "golden_splitbrain.rs", GOLDEN_SPLIT)
    w(patches / "golden_snapshot.rs", GOLDEN_STAGING)
    w(patches / "golden_atlas.rs", GOLDEN_EXPORT)
    # verifier-golden copies
    vg = TASK / "tests" / "verifier-golden"
    vg.mkdir(parents=True, exist_ok=True)
    for name in [
        "binding_key",
        "mclt_holdover",
        "ack_gate",
        "splitbrain",
        "snapshot",
        "atlas",
    ]:
        shutil.copyfile(patches / f"golden_{name}.rs", vg / f"golden_{name}.rs")
    w(
        TASK / "solution" / "solve.sh",
        """#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd /app

DEST=/app/crates/bndupd/src
cp /solution/patches/golden_binding_key.rs "${DEST}/failover/binding_key.rs"
cp /solution/patches/golden_mclt_holdover.rs "${DEST}/failover/mclt_holdover.rs"
cp /solution/patches/golden_ack_gate.rs "${DEST}/failover/ack_gate.rs"
cp /solution/patches/golden_splitbrain.rs "${DEST}/failover/splitbrain.rs"
cp /solution/patches/golden_snapshot.rs "${DEST}/staging/snapshot.rs"
cp /solution/patches/golden_atlas.rs "${DEST}/export/atlas.rs"

cargo build --locked -p bndupd
install -m 0755 target/debug/bndupd /usr/local/bin/bndupd
bash /app/scripts/reset-state.sh
""",
    )


def write_tests() -> None:
    w(
        TASK / "tests" / "verifier-rebuild.sh",
        """#!/usr/bin/env bash
set -euo pipefail

cd /app
B=/opt/verifier-broken-bndupd
cp "${B}/binding_key.rs" /app/crates/bndupd/src/failover/binding_key.rs
cp "${B}/mclt_holdover.rs" /app/crates/bndupd/src/failover/mclt_holdover.rs
cp "${B}/ack_gate.rs" /app/crates/bndupd/src/failover/ack_gate.rs
cp "${B}/splitbrain.rs" /app/crates/bndupd/src/failover/splitbrain.rs
cp "${B}/snapshot.rs" /app/crates/bndupd/src/staging/snapshot.rs
cp "${B}/atlas.rs" /app/crates/bndupd/src/export/atlas.rs
cargo build --locked -p bndupd
install -m 0755 target/debug/bndupd /usr/local/bin/bndupd
""",
    )
    w(
        TASK / "tests" / "test.sh",
        """#!/usr/bin/env bash
set -euo pipefail

export VERIFIER_SEED="${VERIFIER_SEED:-bndupd-verifier}"
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

if [ ! -f "${VERIFIER_GOLDEN_LIB}/golden_binding_key.rs" ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

set +e
cargo build --locked -p bndupd
if [ $? -ne 0 ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi
install -m 0755 target/debug/bndupd /usr/local/bin/bndupd

/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
rc=$?
if [ \"$rc\" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
""",
    )

    # Reference + tests are large — write from companion strings below
    ref = Path(__file__).with_name("_gen_isc_dhcp_reference.py.txt")
    # inline write reference and test_outputs in this function via separate content
    w(TASK / "tests" / "reference_bndupd.py", REFERENCE_PY)
    w(TASK / "tests" / "test_outputs.py", TEST_PY)


REFERENCE_PY = r'''"""Independent reference model for bndupd."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def binding_key(ip: str, chaddr: str) -> str:
    norm = "".join(c.lower() for c in chaddr if c in "0123456789abcdefABCDEF")
    return f"{ip}|{norm}"


def status_rank(status: str) -> int:
    return {
        "active": 5,
        "backup": 4,
        "expired": 3,
        "abandoned": 2,
        "free": 1,
    }.get(status, 0)


def should_supersede(existing: dict, incoming: dict) -> bool:
    if int(incoming["tstp"]) > int(existing["tstp"]):
        return True
    if int(incoming["tstp"]) < int(existing["tstp"]):
        return False
    return status_rank(incoming["binding_status"]) > status_rank(existing["binding_status"])


def mclt_blocks_free(state: dict, target_status: str) -> bool:
    if target_status != "free":
        return False
    if state["partner_up"]:
        return False
    down_at = state.get("partner_down_at")
    if down_at is None:
        return True
    return int(state["clock"]) < int(down_at) + int(state["mclt_seconds"])


def witness_checksum(a: dict, b: dict) -> str:
    payload = "|".join(
        [
            a["binding_key"],
            a["chaddr"],
            str(a["tstp"]),
            b["binding_key"],
            b["chaddr"],
            str(b["tstp"]),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_split_brain(a: dict, b: dict) -> bool:
    if a["binding_status"] != "active" or b["binding_status"] != "active":
        return False
    return a["ip"] == b["ip"] and binding_key(a["ip"], a["chaddr"]) != binding_key(
        b["ip"], b["chaddr"]
    )


def quarantine_pair(state: dict, a: dict, b: dict) -> None:
    key = a["binding_key"] if a["binding_key"] == b["binding_key"] else a["ip"]
    state["bindings"] = [
        x
        for x in state["bindings"]
        if x["binding_key"] not in (a["binding_key"], b["binding_key"])
    ]
    row = {
        "binding_key": key,
        "witness_checksum": witness_checksum(a, b),
        "peer_a": a["peer"],
        "peer_b": b["peer"],
        "chaddr_a": a["chaddr"],
        "chaddr_b": b["chaddr"],
        "tstp_a": int(a["tstp"]),
        "tstp_b": int(b["tstp"]),
    }
    state["quarantine"] = [q for q in state["quarantine"] if q["binding_key"] != row["binding_key"]]
    state["quarantine"].append(row)
    state["stats"]["quarantined"] += 1


def canonical_binding_line(b: dict) -> str:
    key = binding_key(b["ip"], b["chaddr"])
    return "|".join(
        [
            key,
            b["ip"],
            b["chaddr"].lower(),
            b["binding_status"],
            str(b["tstp"]),
            b["peer"],
            str(b["xid"]),
        ]
    )


def atlas_digest(bindings: list[dict], quarantine: list[dict]) -> str:
    parts = sorted(canonical_binding_line(b) for b in bindings)
    qparts = sorted(f"Q|{q['binding_key']}|{q['witness_checksum']}" for q in quarantine)
    parts.extend(qparts)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_events(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _commit_pending(state: dict, pending: dict) -> None:
    key = binding_key(pending["ip"], pending["chaddr"])
    incoming = {
        "binding_key": key,
        "ip": pending["ip"],
        "chaddr": pending["chaddr"],
        "binding_status": pending["binding_status"],
        "tstp": int(pending["tstp"]),
        "starts": int(pending["starts"]),
        "ends": int(pending["ends"]),
        "peer": pending["peer"],
        "xid": int(pending["xid"]),
    }
    if mclt_blocks_free(state, incoming["binding_status"]):
        state["stats"]["mclt_blocked"] += 1
        state["pending"].append(pending)
        return

    existing = next((b for b in state["bindings"] if b["binding_key"] == key), None)
    if existing is not None:
        if is_split_brain(existing, incoming):
            quarantine_pair(state, existing, incoming)
            return
        if should_supersede(existing, incoming):
            state["bindings"] = [b for b in state["bindings"] if b["binding_key"] != key]
            state["bindings"].append(incoming)
            state["stats"]["acked"] += 1
        else:
            state["stats"]["stale_ignored"] += 1
    else:
        other = next(
            (
                b
                for b in state["bindings"]
                if b["ip"] == incoming["ip"]
                and b["binding_status"] == "active"
                and incoming["binding_status"] == "active"
                and b["binding_key"] != key
            ),
            None,
        )
        if other is not None:
            quarantine_pair(state, other, incoming)
            return
        state["bindings"].append(incoming)
        state["stats"]["acked"] += 1


def reference_replay(
    config_path: Path,
    log_path: Path,
    snapshot_path: Path | None = None,
    purge: bool = False,
) -> dict:
    cfg = _load_config(config_path)
    events = _load_events(log_path)
    state = {
        "peer_id": cfg["peer_id"],
        "partner_id": cfg["partner_id"],
        "pool_name": cfg["pool_name"],
        "mclt_seconds": int(cfg["mclt_seconds"]),
        "clock": int(cfg["initial_clock"]),
        "partner_up": True,
        "partner_down_at": None,
        "bindings": [],
        "pending": [],
        "quarantine": [],
        "stats": {
            "bndupd": 0,
            "bndack": 0,
            "acked": 0,
            "mclt_blocked": 0,
            "quarantined": 0,
            "stale_ignored": 0,
            "merge_loads": 0,
        },
        "log_path": str(log_path),
    }
    if snapshot_path is not None and snapshot_path.is_file() and not purge:
        prior = json.loads(snapshot_path.read_text(encoding="utf-8"))
        state["clock"] = int(prior["clock"])
        state["partner_up"] = bool(prior["partner_up"])
        state["partner_down_at"] = prior.get("partner_down_at")
        state["bindings"] = list(prior.get("bindings", []))
        state["pending"] = list(prior.get("pending", []))
        state["quarantine"] = list(prior.get("quarantine", []))
        state["stats"] = dict(prior.get("stats", state["stats"]))
        state["stats"]["merge_loads"] = int(state["stats"].get("merge_loads", 0)) + 1

    for ev in events:
        kind = ev["event_type"]
        if kind == "clock":
            state["clock"] = int(ev["clock"])
        elif kind == "partner_state":
            up = bool(ev["partner_up"])
            at = int(ev.get("at_clock", state["clock"]))
            if up:
                state["partner_up"] = True
                state["partner_down_at"] = None
            else:
                state["partner_up"] = False
                state["partner_down_at"] = at
            state["clock"] = max(state["clock"], at)
        elif kind == "bndupd":
            state["stats"]["bndupd"] += 1
            pending = {
                "xid": int(ev["xid"]),
                "ip": ev["ip"],
                "chaddr": ev["chaddr"],
                "binding_status": ev["binding_status"],
                "tstp": int(ev["tstp"]),
                "starts": int(ev.get("starts", 0)),
                "ends": int(ev.get("ends", 0)),
                "peer": ev["peer"],
            }
            replaced = False
            for i, p in enumerate(state["pending"]):
                if int(p["xid"]) == pending["xid"]:
                    state["pending"][i] = pending
                    replaced = True
                    break
            if not replaced:
                state["pending"].append(pending)
        elif kind == "bndack":
            state["stats"]["bndack"] += 1
            if "at_clock" in ev:
                state["clock"] = max(state["clock"], int(ev["at_clock"]))
            xid = int(ev["xid"])
            idx = next((i for i, p in enumerate(state["pending"]) if int(p["xid"]) == xid), None)
            if idx is None:
                raise ValueError(f"bndack for unknown xid {xid}")
            pending = state["pending"].pop(idx)
            _commit_pending(state, pending)
        else:
            raise ValueError(f"unknown event {kind}")

    bindings = sorted(state["bindings"], key=lambda b: b["binding_key"])
    quarantine = sorted(state["quarantine"], key=lambda q: q["binding_key"])
    digest = atlas_digest(bindings, quarantine)
    return {
        "snapshot_version": 1,
        "peer_id": state["peer_id"],
        "partner_id": state["partner_id"],
        "pool_name": state["pool_name"],
        "clock": state["clock"],
        "partner_up": state["partner_up"],
        "partner_down_at": state["partner_down_at"],
        "atlas_digest": digest,
        "bindings": bindings,
        "pending": state["pending"],
        "quarantine": quarantine,
        "stats": state["stats"],
        "log_path": state["log_path"],
    }


def reference_snapshot(config_path: Path, log_path: Path, snapshot_path: Path | None = None, purge: bool = False) -> dict:
    return reference_replay(config_path, log_path, snapshot_path=snapshot_path, purge=purge)


def reference_publish(config_path: Path, log_path: Path, snapshot_path: Path | None = None, purge: bool = False) -> dict:
    snap = reference_snapshot(config_path, log_path, snapshot_path=snapshot_path, purge=purge)
    bindings = sorted(snap["bindings"], key=lambda b: b["binding_key"])
    quarantine = sorted(snap["quarantine"], key=lambda q: q["binding_key"])
    digest = atlas_digest(bindings, quarantine)
    return {
        "export_version": 1,
        "peer_id": snap["peer_id"],
        "partner_id": snap["partner_id"],
        "pool_name": snap["pool_name"],
        "clock": snap["clock"],
        "atlas_digest": digest,
        "table_suffix": "lease-atlas",
        "stats": snap["stats"],
        "bindings": bindings,
        "quarantine": quarantine,
        "pending_count": len(snap["pending"]),
    }


def reference_chained(config_path: Path, logs: list[Path], snapshot_path: Path) -> dict:
    if snapshot_path.exists():
        snapshot_path.unlink()
    snap = None
    for log in logs:
        snap = reference_replay(config_path, log, snapshot_path=snapshot_path if snap else None, purge=False)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    assert snap is not None
    return reference_publish(config_path, logs[-1], snapshot_path=snapshot_path, purge=False)
'''

TEST_PY = r'''"""Behavioral verifier for bndupd replay and publish semantics."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_bndupd import reference_chained, reference_publish, reference_snapshot

APP = Path("/app")
CLI = "/usr/local/bin/bndupd"
CONFIG = APP / "fixtures/dhcp/peer.json"
LOGS = APP / "fixtures/logs"
SNAPSHOT = APP / "state/dhcp-staging.json"
OUTPUT = APP / "output/lease-atlas.json"
RESET = APP / "scripts/reset-state.sh"
REBUILD = Path("/tests/verifier-rebuild.sh")
HIDDEN_MCLT = Path("/opt/verifier-fixtures/logs/TB3_mclt_boundary.jsonl")
HIDDEN_ACK = Path("/opt/verifier-fixtures/logs/TB3_ack_skew_split.jsonl")
BROKEN = Path("/opt/verifier-broken-bndupd")

PUBLIC_LOGS = [
    "basic-active-ack.jsonl",
    "chaddr-case-normalize.jsonl",
    "mclt-partner-down.jsonl",
    "splitbrain-active.jsonl",
    "supersede-tstp.jsonl",
    "pending-without-ack.jsonl",
    "multi-pool-peers.jsonl",
]

MODULE_TARGETS = {
    "binding_key": APP / "crates/bndupd/src/failover/binding_key.rs",
    "mclt_holdover": APP / "crates/bndupd/src/failover/mclt_holdover.rs",
    "ack_gate": APP / "crates/bndupd/src/failover/ack_gate.rs",
    "splitbrain": APP / "crates/bndupd/src/failover/splitbrain.rs",
    "snapshot": APP / "crates/bndupd/src/staging/snapshot.rs",
    "atlas": APP / "crates/bndupd/src/export/atlas.rs",
}

PROTECTED_SHA256: dict[str, str] = {}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _populate_hashes() -> None:
    PROTECTED_SHA256["peer.json"] = _sha(CONFIG)
    for name in PUBLIC_LOGS:
        PROTECTED_SHA256[name] = _sha(LOGS / name)


_populate_hashes()


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": "/usr/local/cargo/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
    return subprocess.run(cmd, cwd=APP, capture_output=True, text=True, check=False, env=env)


def _build() -> None:
    proc = _run(["cargo", "build", "--locked", "-p", "bndupd"])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    install = _run(["install", "-m", "0755", str(APP / "target/debug/bndupd"), CLI])
    assert install.returncode == 0, install.stderr or install.stdout


def _reset() -> None:
    proc = _run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _replay(log_path: Path, purge: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [
        CLI,
        "replay",
        "--config",
        str(CONFIG),
        "--log",
        str(log_path),
        "--snapshot",
        str(SNAPSHOT),
    ]
    if purge:
        cmd.append("--purge")
    return _run(cmd)


def _publish() -> subprocess.CompletedProcess[str]:
    return _run([CLI, "publish", "--snapshot", str(SNAPSHOT), "--output", str(OUTPUT)])


def golden_lib_dir() -> Path:
    raw = os.environ.get("VERIFIER_GOLDEN_LIB", "").strip()
    if not raw:
        pytest.fail("VERIFIER_GOLDEN_LIB is unset")
    path = Path(raw)
    if not path.is_dir() or not str(path).startswith("/tests/"):
        pytest.fail(f"bad VERIFIER_GOLDEN_LIB: {path}")
    return path


@contextmanager
def _overlay_module(module: str):
    golden = golden_lib_dir() / f"golden_{module}.rs"
    assert golden.is_file(), f"missing golden for {module}"
    saved = {name: path.read_text(encoding="utf-8") for name, path in MODULE_TARGETS.items()}
    proc = _run(["bash", str(REBUILD)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    shutil.copyfile(golden, MODULE_TARGETS[module])
    _build()
    try:
        yield
    finally:
        for name, path in MODULE_TARGETS.items():
            path.write_text(saved[name], encoding="utf-8")
        _build()


class TestBndupdLeaseAtlas:
    @classmethod
    def setup_class(cls) -> None:
        _reset()
        _build()

    def test_fixture_catalog_present(self) -> None:
        assert CONFIG.is_file()
        for name in PUBLIC_LOGS:
            assert (LOGS / name).is_file(), name

    def test_fixture_sha256_integrity(self) -> None:
        assert _sha(CONFIG) == PROTECTED_SHA256["peer.json"]
        for name in PUBLIC_LOGS:
            assert _sha(LOGS / name) == PROTECTED_SHA256[name], name

    def test_cli_flags_required(self) -> None:
        proc = _run([CLI, "replay"])
        assert proc.returncode == 2

    def test_basic_active_ack_atlas(self) -> None:
        _reset()
        assert _replay(LOGS / "basic-active-ack.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, LOGS / "basic-active-ack.jsonl")
        assert got == expect

    def test_staging_matches_model(self) -> None:
        _reset()
        assert _replay(LOGS / "basic-active-ack.jsonl").returncode == 0
        got = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        expect = reference_snapshot(CONFIG, LOGS / "basic-active-ack.jsonl")
        assert got == expect

    def test_publish_reads_staging_only(self) -> None:
        _reset()
        assert _replay(LOGS / "basic-active-ack.jsonl").returncode == 0
        backup = APP / "fixtures/logs.bak"
        shutil.move(str(LOGS), str(backup))
        try:
            pb = _publish()
            assert pb.returncode == 0, pb.stderr or pb.stdout
        finally:
            shutil.move(str(backup), str(LOGS))

    def test_chaddr_case_normalize(self) -> None:
        _reset()
        assert _replay(LOGS / "chaddr-case-normalize.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, LOGS / "chaddr-case-normalize.jsonl")
        assert got == expect
        assert len(got["bindings"]) == 1
        assert got["bindings"][0]["binding_status"] == "active"

    def test_mclt_partner_down(self) -> None:
        _reset()
        assert _replay(LOGS / "mclt-partner-down.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, LOGS / "mclt-partner-down.jsonl")
        assert got == expect
        assert got["stats"]["mclt_blocked"] >= 1
        assert got["bindings"][0]["binding_status"] == "free"

    def test_splitbrain_quarantine(self) -> None:
        _reset()
        assert _replay(LOGS / "splitbrain-active.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, LOGS / "splitbrain-active.jsonl")
        assert got == expect
        assert got["stats"]["quarantined"] >= 1
        assert len(got["quarantine"]) >= 1
        assert got["bindings"] == []

    def test_supersede_tstp(self) -> None:
        _reset()
        assert _replay(LOGS / "supersede-tstp.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, LOGS / "supersede-tstp.jsonl")
        assert got == expect
        assert got["bindings"][0]["binding_status"] == "expired"

    def test_pending_without_ack(self) -> None:
        _reset()
        assert _replay(LOGS / "pending-without-ack.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, LOGS / "pending-without-ack.jsonl")
        assert got == expect
        assert got["pending_count"] == 1
        assert len(got["bindings"]) == 1
        assert got["bindings"][0]["ip"] == "10.0.0.11"

    def test_multi_pool_peers(self) -> None:
        _reset()
        assert _replay(LOGS / "multi-pool-peers.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, LOGS / "multi-pool-peers.jsonl")
        assert got == expect
        assert got["stats"]["stale_ignored"] >= 1

    def test_bindings_sorted_by_key(self) -> None:
        _reset()
        assert _replay(LOGS / "multi-pool-peers.jsonl").returncode == 0
        assert _publish().returncode == 0
        rows = json.loads(OUTPUT.read_text(encoding="utf-8"))["bindings"]
        keys = [r["binding_key"] for r in rows]
        assert keys == sorted(keys)

    def test_tb3_mclt_boundary(self) -> None:
        assert HIDDEN_MCLT.is_file()
        _reset()
        assert _replay(HIDDEN_MCLT).returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, HIDDEN_MCLT)
        assert got == expect
        assert got["stats"]["mclt_blocked"] >= 1

    def test_tb3_ack_skew_split(self) -> None:
        assert HIDDEN_ACK.is_file()
        _reset()
        assert _replay(HIDDEN_ACK).returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, HIDDEN_ACK)
        assert got == expect
        assert got["stats"]["quarantined"] >= 1

    def test_all_public_logs_match_model(self) -> None:
        for name in PUBLIC_LOGS:
            _reset()
            assert _replay(LOGS / name).returncode == 0, name
            assert _publish().returncode == 0, name
            got = json.loads(OUTPUT.read_text(encoding="utf-8"))
            expect = reference_publish(CONFIG, LOGS / name)
            assert got == expect, name

    def test_cross_run_persistence(self) -> None:
        _reset()
        assert _replay(LOGS / "basic-active-ack.jsonl").returncode == 0
        assert _replay(LOGS / "multi-pool-peers.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        # rebuild expected via chained reference writes
        _reset()
        expect = reference_chained(
            CONFIG,
            [LOGS / "basic-active-ack.jsonl", LOGS / "multi-pool-peers.jsonl"],
            SNAPSHOT,
        )
        # re-run SUT chain
        _reset()
        assert _replay(LOGS / "basic-active-ack.jsonl").returncode == 0
        assert _replay(LOGS / "multi-pool-peers.jsonl").returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        assert got["stats"]["merge_loads"] >= 1
        assert got == expect

    def test_purge_clears_prior(self) -> None:
        _reset()
        assert _replay(LOGS / "basic-active-ack.jsonl").returncode == 0
        assert _replay(LOGS / "pending-without-ack.jsonl", purge=True).returncode == 0
        assert _publish().returncode == 0
        got = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expect = reference_publish(CONFIG, LOGS / "pending-without-ack.jsonl", purge=True)
        assert got == expect
        assert all(b["ip"] != "10.0.0.5" for b in got["bindings"])

    def test_omapi_decoy_overlay_fails_alone(self) -> None:
        saved = {name: path.read_text(encoding="utf-8") for name, path in MODULE_TARGETS.items()}
        decoy = APP / "crates/bndupd/src/omapi_decoy/wrap.rs"
        saved_decoy = decoy.read_text(encoding="utf-8")
        try:
            proc = _run(["bash", str(REBUILD)])
            assert proc.returncode == 0, proc.stderr or proc.stdout
            decoy.write_text(
                'pub fn omapi_normalize_lease(ip: &str, chaddr: &str) -> String { format!("fixed:{chaddr}:{ip}") }\n'
                "pub fn legacy_lease_fold(rows: &[String]) -> Vec<String> { rows.to_vec() }\n",
                encoding="utf-8",
            )
            _build()
            _reset()
            assert _replay(LOGS / "splitbrain-active.jsonl").returncode == 0
            assert _publish().returncode == 0
            got = json.loads(OUTPUT.read_text(encoding="utf-8"))
            expect = reference_publish(CONFIG, LOGS / "splitbrain-active.jsonl")
            assert got != expect
        finally:
            for name, path in MODULE_TARGETS.items():
                path.write_text(saved[name], encoding="utf-8")
            decoy.write_text(saved_decoy, encoding="utf-8")
            _build()

    @pytest.mark.parametrize("module", list(MODULE_TARGETS))
    def test_single_module_patch_is_insufficient(self, module: str) -> None:
        with _overlay_module(module):
            _reset()
            # hard fixture needing multiple modules
            proc = _replay(LOGS / "splitbrain-active.jsonl")
            assert proc.returncode == 0
            assert _publish().returncode == 0
            got = json.loads(OUTPUT.read_text(encoding="utf-8"))
            expect = reference_publish(CONFIG, LOGS / "splitbrain-active.jsonl")
            # also check mclt fixture for modules that might pass splitbrain alone
            _reset()
            assert _replay(LOGS / "mclt-partner-down.jsonl").returncode == 0
            assert _publish().returncode == 0
            got2 = json.loads(OUTPUT.read_text(encoding="utf-8"))
            expect2 = reference_publish(CONFIG, LOGS / "mclt-partner-down.jsonl")
            assert got != expect or got2 != expect2

    def test_ingest_only_poison_still_fails_export_contract(self) -> None:
        with _overlay_module("binding_key"):
            with _overlay_module("mclt_holdover"):
                pass
        # restore broken then patch only ingest-ish modules via sequential overlays is messy;
        # instead patch binding_key+ack_gate+splitbrain+mclt but leave export broken
        golden = golden_lib_dir()
        saved = {n: p.read_text(encoding="utf-8") for n, p in MODULE_TARGETS.items()}
        try:
            _run(["bash", str(REBUILD)])
            for mod in ("binding_key", "mclt_holdover", "ack_gate", "splitbrain", "snapshot"):
                shutil.copyfile(golden / f"golden_{mod}.rs", MODULE_TARGETS[mod])
            _build()
            _reset()
            assert _replay(LOGS / "splitbrain-active.jsonl").returncode == 0
            assert _publish().returncode == 0
            got = json.loads(OUTPUT.read_text(encoding="utf-8"))
            expect = reference_publish(CONFIG, LOGS / "splitbrain-active.jsonl")
            assert got != expect
        finally:
            for n, p in MODULE_TARGETS.items():
                p.write_text(saved[n], encoding="utf-8")
            _build()

    def test_export_only_poison_fails_without_ingest(self) -> None:
        golden = golden_lib_dir()
        saved = {n: p.read_text(encoding="utf-8") for n, p in MODULE_TARGETS.items()}
        try:
            _run(["bash", str(REBUILD)])
            shutil.copyfile(golden / "golden_atlas.rs", MODULE_TARGETS["atlas"])
            _build()
            _reset()
            assert _replay(LOGS / "pending-without-ack.jsonl").returncode == 0
            assert _publish().returncode == 0
            got = json.loads(OUTPUT.read_text(encoding="utf-8"))
            expect = reference_publish(CONFIG, LOGS / "pending-without-ack.jsonl")
            assert got != expect
        finally:
            for n, p in MODULE_TARGETS.items():
                p.write_text(saved[n], encoding="utf-8")
            _build()


def test_probe_staging_artifact_required() -> None:
    assert "dhcp-staging.json" in (APP / "docs/staging-schema.md").read_text(encoding="utf-8")


def test_probe_decoy_module_present() -> None:
    assert (APP / "crates/bndupd/src/omapi_decoy/wrap.rs").is_file()
'''


def main() -> None:
    if TASK.exists():
        shutil.rmtree(TASK)
    write_rust()
    write_docs()
    write_fixtures()
    write_meta()
    copy_lock()
    write_solution()
    write_tests()
    print("generated", TASK)


if __name__ == "__main__":
    main()
