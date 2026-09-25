"""Independent reference replay for radiusproxy interim buffer flush simulator."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Stats:
    lines_read: int = 0
    packets_applied: int = 0
    sessions_started: int = 0
    sessions_stopped: int = 0
    interim_buffered: int = 0
    interim_flushed: int = 0
    flush_batches: int = 0
    reboot_lineages: int = 0
    duplicate_unique_ignored: int = 0
    parse_errors: int = 0
    proxy_errors: int = 0
    wal_checkpoints: int = 0

    def as_dict(self) -> dict:
        return {
            "lines_read": self.lines_read,
            "packets_applied": self.packets_applied,
            "sessions_started": self.sessions_started,
            "sessions_stopped": self.sessions_stopped,
            "interim_buffered": self.interim_buffered,
            "interim_flushed": self.interim_flushed,
            "flush_batches": self.flush_batches,
            "reboot_lineages": self.reboot_lineages,
            "duplicate_unique_ignored": self.duplicate_unique_ignored,
            "parse_errors": self.parse_errors,
            "proxy_errors": self.proxy_errors,
            "wal_checkpoints": self.wal_checkpoints,
        }


@dataclass
class SessionState:
    nas_id: str
    acct_session_id: str
    acct_unique_session_id: str
    session_start_ts: int
    interim_interval_sec: int
    input_octets: int = 0
    output_octets: int = 0
    last_interim_ts: int = 0
    last_flush_ts: int = 0
    status: str = "active"


@dataclass
class ProxyState:
    proxy_name: str
    home_server: str
    sessions: dict[tuple[str, str, str], SessionState] = field(default_factory=dict)
    by_nas: dict[str, dict[str, str]] = field(default_factory=dict)
    flush_queue: list[dict] = field(default_factory=list)


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_jsonl(root: Path) -> list[Path]:
    return sorted(p for p in root.glob("*.jsonl") if p.is_file())


def parse_line(line: str) -> dict:
    return json.loads(line)


def packet_from_raw(raw: dict) -> dict:
    attrs = raw.get("attrs") or {}
    return {
        "ts": int(raw.get("ts", 0)),
        "seq": int(raw.get("seq", 0)),
        "nas_id": str(raw.get("nas_id", "")),
        "acct_status_type": str(raw.get("acct_status_type", "")),
        "acct_session_id": str(attrs.get("Acct-Session-Id", "")),
        "acct_unique_id": str(attrs.get("Acct-Unique-Session-Id", "")),
        "session_timeout": int(attrs.get("Session-Timeout", 0) or 0),
        "interim_interval": int(attrs.get("Acct-Interim-Interval", 0) or 0),
        "input_octets": int(attrs.get("Acct-Input-Octets", 0) or 0),
        "output_octets": int(attrs.get("Acct-Output-Octets", 0) or 0),
    }


def effective_interim_sec(pkt: dict, default_sec: int) -> int:
    if pkt["interim_interval"] > 0:
        return pkt["interim_interval"]
    if pkt["session_timeout"] > 0:
        return pkt["session_timeout"]
    return default_sec


def session_key(pkt: dict) -> tuple[str, str, str]:
    return (pkt["nas_id"], pkt["acct_session_id"], pkt["acct_unique_id"])


def lookup_or_start(state: ProxyState, pkt: dict, interim_sec: int, stats: Stats) -> SessionState:
    key = session_key(pkt)
    if key in state.sessions:
        stats.duplicate_unique_ignored += 1
        return state.sessions[key]
    nas_map = state.by_nas.setdefault(pkt["nas_id"], {})
    sess = SessionState(
        nas_id=pkt["nas_id"],
        acct_session_id=pkt["acct_session_id"],
        acct_unique_session_id=pkt["acct_unique_id"],
        session_start_ts=pkt["ts"],
        interim_interval_sec=interim_sec,
        last_flush_ts=pkt["ts"],
    )
    state.sessions[key] = sess
    nas_map[pkt["acct_session_id"]] = pkt["acct_unique_id"]
    stats.sessions_started += 1
    return sess


def on_start(state: ProxyState, pkt: dict, interim_sec: int, stats: Stats) -> SessionState:
    nas_map = state.by_nas.setdefault(pkt["nas_id"], {})
    prev = nas_map.get(pkt["acct_session_id"])
    if prev and prev != pkt["acct_unique_id"]:
        stats.reboot_lineages += 1
        old_key = (pkt["nas_id"], pkt["acct_session_id"], prev)
        if old_key in state.sessions:
            state.sessions[old_key].status = "stopped"
    key = session_key(pkt)
    if key in state.sessions:
        stats.duplicate_unique_ignored += 1
        return state.sessions[key]
    sess = SessionState(
        nas_id=pkt["nas_id"],
        acct_session_id=pkt["acct_session_id"],
        acct_unique_session_id=pkt["acct_unique_id"],
        session_start_ts=pkt["ts"],
        interim_interval_sec=interim_sec,
        last_flush_ts=pkt["ts"],
    )
    state.sessions[key] = sess
    nas_map[pkt["acct_session_id"]] = pkt["acct_unique_id"]
    stats.sessions_started += 1
    return sess


def find_session(state: ProxyState, nas_id: str, acct_session_id: str, session_start_ts: int) -> SessionState | None:
    for s in state.sessions.values():
        if s.nas_id == nas_id and s.acct_session_id == acct_session_id and s.session_start_ts == session_start_ts:
            return s
    return None


def flush_pending_for_stop(state: ProxyState, sess: SessionState, now_ts: int, stats: Stats) -> list[dict]:
    due: list[dict] = []
    remain: list[dict] = []
    for entry in state.flush_queue:
        if (
            entry["nas_id"] == sess.nas_id
            and entry["acct_session_id"] == sess.acct_session_id
            and entry["session_start_ts"] == sess.session_start_ts
        ):
            due.append(entry)
        else:
            remain.append(entry)
    due.sort(key=lambda e: (e["session_start_ts"], e["seq"]))
    state.flush_queue = remain
    if due:
        stats.flush_batches += 1
        stats.interim_flushed += len(due)
        sess.last_flush_ts = now_ts
    return due


def flush_due(state: ProxyState, now_ts: int, stats: Stats) -> list[dict]:
    due: list[dict] = []
    remain: list[dict] = []
    for entry in state.flush_queue:
        sess = find_session(state, entry["nas_id"], entry["acct_session_id"], entry["session_start_ts"])
        if sess is None:
            remain.append(entry)
            continue
        if now_ts - sess.last_flush_ts >= sess.interim_interval_sec:
            due.append(entry)
        else:
            remain.append(entry)
    due.sort(key=lambda e: (e["session_start_ts"], e["seq"]))
    state.flush_queue = remain
    if due:
        stats.flush_batches += 1
        stats.interim_flushed += len(due)
        for entry in due:
            sess = find_session(state, entry["nas_id"], entry["acct_session_id"], entry["session_start_ts"])
            if sess:
                sess.last_flush_ts = now_ts
    return due


def export_sessions(state: ProxyState) -> list[dict]:
    rows = sorted(state.sessions.values(), key=lambda s: (s.session_start_ts, s.nas_id, s.acct_session_id))
    return [
        {
            "nas_id": s.nas_id,
            "acct_session_id": s.acct_session_id,
            "acct_unique_session_id": s.acct_unique_session_id,
            "session_start_ts": s.session_start_ts,
            "interim_interval_sec": s.interim_interval_sec,
            "input_octets": s.input_octets,
            "output_octets": s.output_octets,
            "last_interim_ts": s.last_interim_ts,
            "status": s.status,
        }
        for s in rows
    ]


def build_snapshot(state: ProxyState, stats: Stats) -> dict:
    queue = sorted(state.flush_queue, key=lambda e: (e["session_start_ts"], e["seq"]))
    if queue is None:
        queue = []
    return {
        "snapshot_version": 1,
        "proxy_name": state.proxy_name,
        "home_server": state.home_server,
        "sessions": export_sessions(state),
        "flush_queue": queue,
        "stats": stats.as_dict(),
    }


def apply_packet(pkt: dict, cfg: dict, state: ProxyState, stats: Stats) -> None:
    if not pkt["nas_id"] or not pkt["acct_session_id"] or not pkt["acct_status_type"]:
        stats.parse_errors += 1
        return
    interim_sec = effective_interim_sec(pkt, int(cfg.get("default_interim_interval_sec", 300)))
    kind = pkt["acct_status_type"]
    if kind == "Start":
        sess = on_start(state, pkt, interim_sec, stats)
        sess.input_octets = pkt["input_octets"]
        sess.output_octets = pkt["output_octets"]
        stats.packets_applied += 1
    elif kind == "Interim-Update":
        sess = lookup_or_start(state, pkt, interim_sec, stats)
        sess.input_octets = pkt["input_octets"]
        sess.output_octets = pkt["output_octets"]
        sess.last_interim_ts = pkt["ts"]
        stats.interim_buffered += 1
        entry = {
            "session_start_ts": sess.session_start_ts,
            "seq": pkt["seq"],
            "acct_status_type": kind,
            "nas_id": pkt["nas_id"],
            "acct_session_id": pkt["acct_session_id"],
        }
        state.flush_queue.append(entry)
        flush_due(state, pkt["ts"], stats)
        stats.packets_applied += 1
    elif kind == "Stop":
        sess = lookup_or_start(state, pkt, interim_sec, stats)
        sess.input_octets = pkt["input_octets"]
        sess.output_octets = pkt["output_octets"]
        sess.status = "stopped"
        stats.sessions_stopped += 1
        flush_pending_for_stop(state, sess, pkt["ts"], stats)
        flush_due(state, pkt["ts"], stats)
        stats.packets_applied += 1
    else:
        stats.proxy_errors += 1


def replay_logs(logs: Path, cfg_path: Path) -> dict:
    cfg = load_config(cfg_path)
    state = ProxyState(proxy_name=str(cfg["proxy_name"]), home_server=str(cfg["home_server"]))
    stats = Stats()
    files = discover_jsonl(logs) if logs.is_dir() else [logs]
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            stats.lines_read += 1
            try:
                raw = parse_line(line)
                pkt = packet_from_raw(raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                stats.parse_errors += 1
                continue
            apply_packet(pkt, cfg, state, stats)
    stats.wal_checkpoints = 1
    snap = build_snapshot(state, stats)
    completed = sum(1 for s in snap["sessions"] if s["status"] == "stopped")
    return {
        "proxy_name": snap["proxy_name"],
        "home_server": snap["home_server"],
        "sessions": snap["sessions"],
        "sessions_completed": completed,
        "interim_flushed": stats.interim_flushed,
        "flush_batches": stats.flush_batches,
        "stats": snap["stats"],
    }


def reference_snapshot(logs: Path, cfg_path: Path) -> dict:
    cfg = load_config(cfg_path)
    state = ProxyState(proxy_name=str(cfg["proxy_name"]), home_server=str(cfg["home_server"]))
    stats = Stats()
    files = discover_jsonl(logs) if logs.is_dir() else [logs]
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            stats.lines_read += 1
            try:
                raw = parse_line(line)
                pkt = packet_from_raw(raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                stats.parse_errors += 1
                continue
            apply_packet(pkt, cfg, state, stats)
    stats.wal_checkpoints = 1
    return build_snapshot(state, stats)


def reference_replay(logs: Path, cfg_path: Path) -> dict:
    return replay_logs(logs, cfg_path)
